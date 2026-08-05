"""In-memory sliding-window rate limiter for API abuse protection."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import Depends

from config import (
    RATE_LIMIT_ENABLED,
    RATE_LIMIT_SOLVE_PER_HOUR,
    RATE_LIMIT_SOLVE_PER_MINUTE,
)
from errors import RateLimitError
from security import get_current_user


class SlidingWindowRateLimiter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: dict[str, Deque[float]] = defaultdict(deque)

    def check(
        self,
        key: str,
        *,
        limit: int,
        window_seconds: int,
    ) -> None:
        if not RATE_LIMIT_ENABLED or limit <= 0:
            return

        now = time.monotonic()
        window_start = now - window_seconds

        with self._lock:
            bucket = self._events[key]
            while bucket and bucket[0] < window_start:
                bucket.popleft()

            if len(bucket) >= limit:
                oldest = bucket[0]
                retry_after = max(1, int(oldest + window_seconds - now) + 1)
                raise RateLimitError(retry_after=retry_after)

            bucket.append(now)


limiter = SlidingWindowRateLimiter()


def enforce_solve_rate_limit(current_user=Depends(get_current_user)):
    """Dependency: limit AI solve calls per authenticated user."""
    user_key = f"solve:{current_user.id}"
    limiter.check(
        f"{user_key}:minute",
        limit=RATE_LIMIT_SOLVE_PER_MINUTE,
        window_seconds=60,
    )
    limiter.check(
        f"{user_key}:hour",
        limit=RATE_LIMIT_SOLVE_PER_HOUR,
        window_seconds=3600,
    )
    return current_user
