"""Request ID assignment and structured HTTP access logging."""

from __future__ import annotations

import time
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from logging_config import get_logger

logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid4())
        request.state.request_id = request_id
        request.state.user_id = None

        started = time.perf_counter()
        status_code = 500
        response: Response | None = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            user_id = getattr(request.state, "user_id", None)
            logger.info(
                "request completed",
                extra={
                    "event": "http_request",
                    "request_id": request_id,
                    "user_id": str(user_id) if user_id else None,
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status_code": status_code,
                    "response_time_ms": duration_ms,
                },
            )
