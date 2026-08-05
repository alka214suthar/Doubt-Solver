import json
import mimetypes
import re
import time
from pathlib import Path

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from dotenv import load_dotenv

from config import (
    GEMINI_API_KEY,
    GEMINI_MAX_RETRIES,
    GEMINI_MODEL,
    GEMINI_RETRY_BASE_SECONDS,
    GEMINI_TIMEOUT_MS,
    UPLOAD_DIR,
)
from dtos.request import DoubtSolverRequest
from dtos.response import DoubtSolverResponse
from errors import LLMInvalidRequestError, LLMProviderError
from LLM.promt import get_prompt
from logging_config import get_logger

load_dotenv()

logger = get_logger(__name__)

RETRYABLE_STATUS_CODES = {429, 500, 502, 503}

client = genai.Client(
    api_key=GEMINI_API_KEY or None,
    http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
)


def _resolve_image_path(image_url: str | None) -> Path | None:
    if not image_url:
        return None

    raw = str(image_url).replace("\\", "/")
    path = Path(raw)

    candidates = []
    if path.is_absolute():
        candidates.append(path)
    else:
        candidates.append(Path.cwd() / path)
        candidates.append(Path(UPLOAD_DIR) / path.name)
        if raw.startswith("uploads/"):
            candidates.append(Path(UPLOAD_DIR) / Path(raw).name)

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _extract_json(text: str) -> dict:
    if not text or not text.strip():
        raise ValueError("Model returned an empty response")

    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if fenced:
        cleaned = fenced.group(1).strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"Model response was not valid JSON: {cleaned[:300]}")
        data = json.loads(cleaned[start : end + 1])

    if not isinstance(data, dict):
        raise ValueError("Invalid response format from model")

    return data


def _is_timeout_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, httpx.TimeoutException)):
        return True
    name = type(exc).__name__.lower()
    message = str(exc).lower()
    return "timeout" in name or "timed out" in message or "deadline" in message


def _is_retryable(exc: BaseException) -> bool:
    if _is_timeout_error(exc):
        return True
    if isinstance(exc, (httpx.TransportError, ConnectionError)):
        return True
    if isinstance(exc, genai_errors.APIError):
        return exc.code in RETRYABLE_STATUS_CODES
    return False


def _provider_error_message(exc: BaseException) -> str:
    if isinstance(exc, genai_errors.APIError):
        detail = exc.message or exc.status or type(exc).__name__
        return f"AI provider error ({exc.code}): {detail}"
    if _is_timeout_error(exc):
        return "AI provider request timed out"
    return f"AI provider error: {type(exc).__name__}"


def solve_doubt(request: DoubtSolverRequest) -> DoubtSolverResponse:
    prompt = get_prompt(
        request.class_name, request.question, request.subject, request.image_url
    )
    max_retries = max(1, GEMINI_MAX_RETRIES)
    backoff = GEMINI_RETRY_BASE_SECONDS
    image_path = _resolve_image_path(request.image_url)
    overall_started = time.perf_counter()

    for attempt in range(1, max_retries + 1):
        attempt_started = time.perf_counter()
        try:
            logger.info(
                "solve_doubt attempt",
                extra={
                    "event": "solve_doubt_attempt",
                    "attempt": attempt,
                    "user_id": str(request.user_id),
                    "ai_model": GEMINI_MODEL,
                    "has_image": bool(image_path),
                },
            )

            contents: list = [prompt]
            if image_path:
                mime_type = (
                    mimetypes.guess_type(str(image_path))[0] or "image/png"
                )
                image_bytes = image_path.read_bytes()
                contents = [
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                    prompt,
                ]

            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )

            raw_text = getattr(response, "text", None) or ""
            data = _extract_json(raw_text)
            latency_ms = round((time.perf_counter() - attempt_started) * 1000, 2)
            total_ms = round((time.perf_counter() - overall_started) * 1000, 2)

            logger.info(
                "solve_doubt success",
                extra={
                    "event": "solve_doubt_success",
                    "attempt": attempt,
                    "user_id": str(request.user_id),
                    "ai_model": GEMINI_MODEL,
                    "ai_latency_ms": latency_ms,
                    "ai_total_ms": total_ms,
                    "ai_success": True,
                },
            )
            return DoubtSolverResponse(
                answer=data.get("answer", "") or "",
                hints=[hint for hint in data.get("hints", []) if hint],
                steps=[step for step in data.get("steps", []) if step],
            )

        except Exception as e:
            latency_ms = round((time.perf_counter() - attempt_started) * 1000, 2)
            retryable = _is_retryable(e)
            provider_message = _provider_error_message(e)

            logger.error(
                "solve_doubt failed",
                extra={
                    "event": "solve_doubt_error",
                    "attempt": attempt,
                    "user_id": str(request.user_id),
                    "ai_model": GEMINI_MODEL,
                    "ai_latency_ms": latency_ms,
                    "ai_success": False,
                    "retryable": retryable,
                    "error_type": type(e).__name__,
                    "provider_error": provider_message,
                },
            )

            if not retryable:
                if isinstance(e, (ValueError, json.JSONDecodeError)):
                    raise LLMInvalidRequestError() from e
                if (
                    isinstance(e, genai_errors.ClientError)
                    and e.code not in RETRYABLE_STATUS_CODES
                ):
                    # Keep provider/API-key details out of the client response.
                    raise LLMInvalidRequestError() from e
                raise LLMProviderError() from e

            if attempt >= max_retries:
                raise LLMProviderError() from e

            time.sleep(backoff)
            backoff *= 2

    raise LLMProviderError()
