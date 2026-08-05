from __future__ import annotations

from typing import Any


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int,
        *,
        details: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.headers = headers


class AuthenticationError(AppError):
    def __init__(self, message: str = "Please sign in again.") -> None:
        super().__init__(
            "AUTHENTICATION_ERROR",
            message,
            401,
            headers={"WWW-Authenticate": "Bearer"},
        )


class LLMProviderError(AppError):
    def __init__(self, message: str = "The AI provider is temporarily unavailable") -> None:
        super().__init__("LLM_PROVIDER_ERROR", message, 503)


class LLMInvalidRequestError(AppError):
    def __init__(self, message: str = "The AI provider rejected the request") -> None:
        super().__init__("LLM_INVALID_REQUEST", message, 502)


class RateLimitError(AppError):
    def __init__(
        self,
        message: str = "Too many requests. Please try again later.",
        *,
        retry_after: int | None = None,
    ) -> None:
        headers = {"Retry-After": str(retry_after)} if retry_after is not None else None
        super().__init__(
            "RATE_LIMIT_EXCEEDED",
            message,
            429,
            details={"retry_after": retry_after} if retry_after is not None else None,
            headers=headers,
        )


class FileValidationError(AppError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__("FILE_VALIDATION_ERROR", message, status_code)
