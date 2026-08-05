import inspect
from functools import wraps

from database import SessionLocal
from logging_config import get_logger

logger = get_logger(__name__)


def log_calls(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger.info(
            "function call",
            extra={
                "event": "call",
                "function": func.__name__,
                "arg_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
            },
        )
        try:
            result = await func(*args, **kwargs)
            logger.info(
                "function return",
                extra={"event": "return", "function": func.__name__},
            )
            return result
        except Exception as error:
            logger.exception(
                "function error",
                extra={
                    "event": "error",
                    "function": func.__name__,
                    "error_type": type(error).__name__,
                    "error": str(error),
                },
            )
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger.info(
            "function call",
            extra={
                "event": "call",
                "function": func.__name__,
                "arg_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
            },
        )
        try:
            result = func(*args, **kwargs)
            logger.info(
                "function return",
                extra={"event": "return", "function": func.__name__},
            )
            return result
        except Exception as error:
            logger.exception(
                "function error",
                extra={
                    "event": "error",
                    "function": func.__name__,
                    "error_type": type(error).__name__,
                    "error": str(error),
                },
            )
            raise

    return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper


def db_transaction(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        session = SessionLocal()

        try:
            kwargs["session"] = session

            result = await func(*args, **kwargs)

            session.commit()

            return result

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        session = SessionLocal()

        try:
            kwargs["session"] = session

            result = func(*args, **kwargs)

            session.commit()

            return result

        except Exception:
            session.rollback()
            raise

        finally:
            session.close()

    return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper
