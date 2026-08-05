from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from errors import (
    AppError,
    AuthenticationError,
    FileValidationError,
    LLMInvalidRequestError,
    LLMProviderError,
    RateLimitError,
)
from logging_config import get_logger
from user_messages import DEFAULT_MESSAGE, resolve_user_message

logger = get_logger(__name__)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", None) or request.headers.get(
        "x-request-id"
    ) or str(uuid4())


def _response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    *,
    details: Any | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = _request_id(request)
    body: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
        }
    }
    if details is not None:
        body["error"]["details"] = details
    response_headers = {**(headers or {}), "X-Request-ID": request_id}
    return JSONResponse(
        status_code=status_code,
        content=body,
        headers=response_headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.info(
            "request validation failed",
            extra={
                "event": "validation_error",
                "request_id": _request_id(request),
                "error_detail": str(exc.errors()),
            },
        )
        return _response(
            request,
            422,
            "VALIDATION_ERROR",
            resolve_user_message("VALIDATION_ERROR"),
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(
        request: Request, exc: AuthenticationError
    ) -> JSONResponse:
        return _response(
            request,
            exc.status_code,
            exc.code,
            resolve_user_message(exc.code, exc.message, status_code=exc.status_code),
            headers=exc.headers,
        )

    @app.exception_handler(FileValidationError)
    async def file_validation_error_handler(
        request: Request, exc: FileValidationError
    ) -> JSONResponse:
        return _response(
            request,
            exc.status_code,
            exc.code,
            resolve_user_message(exc.code, exc.message, status_code=exc.status_code),
            headers=exc.headers,
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_error_handler(
        request: Request, exc: RateLimitError
    ) -> JSONResponse:
        logger.warning(
            "rate limit exceeded",
            extra={
                "event": "rate_limit_exceeded",
                "request_id": _request_id(request),
                "user_id": str(getattr(request.state, "user_id", None) or ""),
                "endpoint": request.url.path,
                "status_code": exc.status_code,
            },
        )
        return _response(
            request,
            exc.status_code,
            exc.code,
            resolve_user_message(exc.code, exc.message, status_code=exc.status_code),
            headers=exc.headers,
        )

    @app.exception_handler(LLMInvalidRequestError)
    async def llm_invalid_request_handler(
        request: Request, exc: LLMInvalidRequestError
    ) -> JSONResponse:
        logger.error(
            "llm provider rejected request",
            extra={
                "event": "llm_invalid_request",
                "request_id": _request_id(request),
                "ai_success": False,
                "error_detail": exc.message,
            },
        )
        return _response(
            request,
            exc.status_code,
            exc.code,
            resolve_user_message(exc.code, status_code=exc.status_code),
            headers=exc.headers,
        )

    @app.exception_handler(LLMProviderError)
    async def llm_provider_error_handler(
        request: Request, exc: LLMProviderError
    ) -> JSONResponse:
        logger.error(
            "llm provider request failed",
            extra={
                "event": "llm_provider_error",
                "request_id": _request_id(request),
                "ai_success": False,
                "error_detail": exc.message,
            },
        )
        return _response(
            request,
            exc.status_code,
            exc.code,
            resolve_user_message(exc.code, status_code=exc.status_code),
            headers=exc.headers,
        )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "application error",
            extra={
                "event": "app_error",
                "request_id": _request_id(request),
                "error_code": exc.code,
                "error_detail": exc.message,
                "status_code": exc.status_code,
            },
        )
        return _response(
            request,
            exc.status_code,
            exc.code,
            resolve_user_message(exc.code, exc.message, status_code=exc.status_code),
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        if exc.status_code == 401:
            code = "AUTHENTICATION_ERROR"
        elif exc.status_code == 404:
            code = "NOT_FOUND"
        else:
            code = "HTTP_ERROR"
        logger.info(
            "http error",
            extra={
                "event": "http_error",
                "request_id": _request_id(request),
                "status_code": exc.status_code,
                "error_detail": str(exc.detail),
            },
        )
        return _response(
            request,
            exc.status_code,
            code,
            resolve_user_message(code, status_code=exc.status_code),
            headers=exc.headers,
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(
        request: Request, exc: IntegrityError
    ) -> JSONResponse:
        logger.warning(
            "database constraint rejected request",
            extra={
                "event": "database_integrity_error",
                "request_id": _request_id(request),
            },
        )
        return _response(
            request,
            409,
            "DATABASE_CONSTRAINT_ERROR",
            resolve_user_message("DATABASE_CONSTRAINT_ERROR", status_code=409),
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        logger.exception(
            "database request failed",
            extra={
                "event": "database_error",
                "error_type": type(exc).__name__,
                "request_id": _request_id(request),
            },
        )
        return _response(
            request,
            503,
            "DATABASE_ERROR",
            resolve_user_message("DATABASE_ERROR", status_code=503),
        )

    @app.exception_handler(Exception)
    async def unknown_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled request error",
            extra={
                "event": "unhandled_error",
                "error_type": type(exc).__name__,
                "request_id": _request_id(request),
            },
        )
        return _response(
            request,
            500,
            "INTERNAL_SERVER_ERROR",
            resolve_user_message("INTERNAL_SERVER_ERROR", status_code=500)
            or DEFAULT_MESSAGE,
        )
