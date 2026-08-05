import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", BASE_DIR / "uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
DOUBT_RETENTION_DAYS = int(os.getenv("DOUBT_RETENTION_DAYS", "10"))

APP_ENV = os.getenv("APP_ENV", "development").lower()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()


def _parse_cors_origins() -> list[str]:
    """Exact frontend origins only. Never use '*' with credentials."""
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if not raw:
        if APP_ENV in {"production", "prod"}:
            raise RuntimeError(
                "CORS_ORIGINS is required in production "
                "(comma-separated exact domains, e.g. https://your-project-domain.com)"
            )
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    if any(origin == "*" for origin in origins):
        raise RuntimeError(
            "CORS_ORIGINS must not include '*' when credentials are enabled; "
            "use exact domains instead"
        )
    return origins


CORS_ORIGINS = _parse_cors_origins()
PORT = int(os.getenv("PORT", "8000"))
JWT_SECRET = os.getenv("JWT_SECRET", "").strip()
if not JWT_SECRET:
    if APP_ENV in {"production", "prod"}:
        raise RuntimeError("JWT_SECRET is required in production")
    JWT_SECRET = secrets.token_urlsafe(48)

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))
REFRESH_COOKIE_NAME = "refresh_token"
COOKIE_SECURE = os.getenv(
    "COOKIE_SECURE", "true" if APP_ENV in {"production", "prod"} else "false"
).lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax").lower()

# Gemini client
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v1")
GEMINI_TIMEOUT_MS = int(os.getenv("GEMINI_TIMEOUT_MS", "30000"))
GEMINI_MAX_RETRIES = int(os.getenv("GEMINI_MAX_RETRIES", "3"))
GEMINI_RETRY_BASE_SECONDS = float(os.getenv("GEMINI_RETRY_BASE_SECONDS", "1"))

# Rate limiting (solve-doubt). Disabled in test by default.
RATE_LIMIT_ENABLED = (
    os.getenv(
        "RATE_LIMIT_ENABLED",
        "false" if APP_ENV in {"test"} else "true",
    ).lower()
    == "true"
)
RATE_LIMIT_SOLVE_PER_MINUTE = int(os.getenv("RATE_LIMIT_SOLVE_PER_MINUTE", "10"))
RATE_LIMIT_SOLVE_PER_HOUR = int(os.getenv("RATE_LIMIT_SOLVE_PER_HOUR", "60"))

# Duplicate-question cache
QUESTION_CACHE_ENABLED = (
    os.getenv(
        "QUESTION_CACHE_ENABLED",
        "false" if APP_ENV in {"test"} else "true",
    ).lower()
    == "true"
)
QUESTION_CACHE_TTL_HOURS = int(os.getenv("QUESTION_CACHE_TTL_HOURS", "168"))


def require_database_url() -> str:
    if DATABASE_URL:
        return DATABASE_URL
    if APP_ENV in {"production", "prod"}:
        raise RuntimeError("DATABASE_URL is required in production")
    return "postgresql+psycopg2://postgres:1234@localhost:5432/doubt_solver"
