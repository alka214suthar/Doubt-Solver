"""Unit tests for rate limiting, question cache hashing, and Gemini retry policy."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("GEMINI_API_KEY", "test-key")


def test_question_hash_is_stable_after_normalization():
    from question_cache import compute_question_hash

    left = compute_question_hash(
        question="  What is   2 + 2? ",
        subject="Mathematics",
        class_name=8,
        image_url=None,
    )
    right = compute_question_hash(
        question="what is 2 + 2?",
        subject="mathematics",
        class_name="8",
        image_url=None,
    )
    assert left == right
    assert len(left) == 64


def test_question_hash_changes_with_prompt_or_model_version():
    from question_cache import compute_question_hash

    base = compute_question_hash(
        question="solve x",
        subject="Mathematics",
        class_name=9,
        image_url=None,
        prompt_version="v1",
        model_version="model-a",
    )
    other_prompt = compute_question_hash(
        question="solve x",
        subject="Mathematics",
        class_name=9,
        image_url=None,
        prompt_version="v2",
        model_version="model-a",
    )
    other_model = compute_question_hash(
        question="solve x",
        subject="Mathematics",
        class_name=9,
        image_url=None,
        prompt_version="v1",
        model_version="model-b",
    )
    assert base != other_prompt
    assert base != other_model


def test_rate_limiter_blocks_after_limit(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    # Reload config-dependent module state
    import importlib
    import config
    import rate_limit

    importlib.reload(config)
    importlib.reload(rate_limit)

    limiter = rate_limit.SlidingWindowRateLimiter()
    for _ in range(3):
        limiter.check("user:test", limit=3, window_seconds=60)

    with pytest.raises(rate_limit.RateLimitError) as exc_info:
        limiter.check("user:test", limit=3, window_seconds=60)
    assert exc_info.value.status_code == 429


def test_gemini_retries_only_transient_failures():
    from google.genai import errors as genai_errors
    from LLM import doubt_solver

    assert doubt_solver._is_retryable(httpx.TimeoutException("timeout"))
    assert doubt_solver._is_retryable(
        genai_errors.APIError(429, {"message": "rate limited", "status": "RESOURCE_EXHAUSTED"})
    )
    assert doubt_solver._is_retryable(
        genai_errors.APIError(503, {"message": "unavailable", "status": "UNAVAILABLE"})
    )
    assert not doubt_solver._is_retryable(
        genai_errors.ClientError(400, {"message": "bad request", "status": "INVALID_ARGUMENT"})
    )
    assert not doubt_solver._is_retryable(ValueError("bad json"))
