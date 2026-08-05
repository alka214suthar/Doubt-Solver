"""Normalized question-hash cache for duplicate AI answers."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from config import (
    GEMINI_MODEL,
    PROMPT_VERSION,
    QUESTION_CACHE_ENABLED,
    QUESTION_CACHE_TTL_HOURS,
    UPLOAD_DIR,
)
from dtos.response import DoubtSolverResponse
from logging_config import get_logger
from models.doubt_models import SolutionCacheModel

logger = get_logger(__name__)


def normalize_question_text(question: str) -> str:
    collapsed = re.sub(r"\s+", " ", (question or "").strip().lower())
    return collapsed


def _resolve_image_bytes(image_url: str | None) -> bytes | None:
    if not image_url:
        return None

    raw = str(image_url).replace("\\", "/")
    path = Path(raw)
    candidates: list[Path] = []
    if path.is_absolute():
        candidates.append(path)
    else:
        candidates.append(Path.cwd() / path)
        candidates.append(Path(UPLOAD_DIR) / path.name)
        if raw.startswith("uploads/"):
            candidates.append(Path(UPLOAD_DIR) / Path(raw).name)

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.read_bytes()
    return None


def compute_image_fingerprint(image_url: str | None) -> str:
    """Return content hash when an image exists, else a stable 'none' marker."""
    image_bytes = _resolve_image_bytes(image_url)
    if image_bytes is None:
        return "none" if not image_url else "missing"
    return hashlib.sha256(image_bytes).hexdigest()


def compute_question_hash(
    *,
    question: str,
    subject: str,
    class_name: int | str,
    image_url: str | None,
    prompt_version: str = PROMPT_VERSION,
    model_version: str = GEMINI_MODEL,
) -> str:
    subject_value = getattr(subject, "value", subject)
    payload = {
        "question": normalize_question_text(question),
        "subject": str(subject_value).strip().lower(),
        "class": str(class_name).strip(),
        "image": compute_image_fingerprint(image_url),
        "prompt_version": prompt_version,
        "model_version": model_version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def get_cached_solution(
    session: Session, question_hash: str
) -> DoubtSolverResponse | None:
    if not QUESTION_CACHE_ENABLED:
        return None

    row = (
        session.query(SolutionCacheModel)
        .filter(SolutionCacheModel.question_hash == question_hash)
        .first()
    )
    if not row:
        return None

    if QUESTION_CACHE_TTL_HOURS > 0:
        expires_at = row.created_at + timedelta(hours=QUESTION_CACHE_TTL_HOURS)
        if datetime.utcnow() > expires_at:
            session.delete(row)
            session.flush()
            logger.info(
                "question cache expired",
                extra={
                    "event": "question_cache_expired",
                    "question_hash": question_hash,
                },
            )
            return None

    row.hit_count = (row.hit_count or 0) + 1
    session.flush()
    logger.info(
        "question cache hit",
        extra={
            "event": "question_cache_hit",
            "question_hash": question_hash,
            "hit_count": row.hit_count,
        },
    )
    return DoubtSolverResponse(
        answer=row.answer,
        hints=list(row.hints or []),
        steps=list(row.steps or []),
    )


def store_cached_solution(
    session: Session,
    question_hash: str,
    solution: DoubtSolverResponse,
) -> None:
    if not QUESTION_CACHE_ENABLED:
        return

    # Skip caching empty / refused answers
    answer = (solution.answer or "").strip()
    if not answer:
        return
    if answer.lower().startswith("not related"):
        return

    existing = (
        session.query(SolutionCacheModel)
        .filter(SolutionCacheModel.question_hash == question_hash)
        .first()
    )
    if existing:
        existing.answer = solution.answer
        existing.hints = list(solution.hints or [])
        existing.steps = list(solution.steps or [])
        existing.updated_at = datetime.utcnow()
    else:
        session.add(
            SolutionCacheModel(
                question_hash=question_hash,
                answer=solution.answer,
                hints=list(solution.hints or []),
                steps=list(solution.steps or []),
            )
        )
    session.flush()
    logger.info(
        "question cache stored",
        extra={"event": "question_cache_store", "question_hash": question_hash},
    )
