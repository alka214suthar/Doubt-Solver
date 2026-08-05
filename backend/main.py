from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from config import CORS_ORIGINS, LOG_LEVEL, UPLOAD_DIR
from database import engine
from dtos.response import HealthResponse, ReadyHealthResponse
from exception_handlers import register_exception_handlers
from image_uploads import delete_expired_uploads
from logging_config import get_logger, setup_logging
from middleware import RequestContextMiddleware
from routes.delete_doubt import router as delete_doubt_router
from routes.get_bookmarked_dubts import router as get_bookmarked_doubts_router
from routes.get_user_doubts import router as get_user_doubts_router
from routes.solve_doubt import router as doubt_router
from routes.submit_bookmark import router as submit_bookmark_router
from routes.submit_feedback import router as feedback_router
from routes.user_auth import account_router
from routes.user_auth import router as user_auth_router
from routes.user_auth import users_router

API_V1_PREFIX = "/api/v1"
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging(LOG_LEVEL)
    logger.info("application starting", extra={"event": "app_start"})
    delete_expired_uploads()
    yield
    logger.info("application stopping", extra={"event": "app_stop"})


app = FastAPI(
    title="Doubt Solver API",
    version="1.0.0",
    description=(
        "REST API for AI Doubt Solver: register/login, ask academic doubts, "
        "receive AI solutions, submit feedback, and manage bookmarks.\n\n"
        "Interactive docs: `/docs` (Swagger) · `/redoc` (ReDoc)."
    ),
    openapi_tags=[
        {
            "name": "health",
            "description": "Service health checks",
        },
        {
            "name": "users",
            "description": "Registration, login, and user profile",
        },
        {
            "name": "doubts",
            "description": "Ask doubts, history, feedback, and bookmarks",
        },
    ],
    lifespan=lifespan,
)

register_exception_handlers(app)

# Last added middleware runs first for incoming requests.
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(doubt_router, prefix=f"{API_V1_PREFIX}/doubts")
app.include_router(delete_doubt_router, prefix=f"{API_V1_PREFIX}/doubts")
app.include_router(user_auth_router, prefix=f"{API_V1_PREFIX}/auth")
app.include_router(account_router, prefix=f"{API_V1_PREFIX}/auth")
app.include_router(users_router, prefix=f"{API_V1_PREFIX}/users")
app.include_router(feedback_router, prefix=f"{API_V1_PREFIX}/feedback")
app.include_router(get_user_doubts_router, prefix=f"{API_V1_PREFIX}/user_doubts")
app.include_router(submit_bookmark_router, prefix=f"{API_V1_PREFIX}/bookmark")
app.include_router(
    get_bookmarked_doubts_router,
    prefix=f"{API_V1_PREFIX}/bookmarked_doubts",
)


@app.get(
    "/health/live",
    response_model=HealthResponse,
    status_code=200,
    tags=["health"],
    summary="Liveness probe",
    description="Returns ok when the API process is running. Does not check dependencies.",
)
def health_live() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get(
    "/health/ready",
    response_model=ReadyHealthResponse,
    tags=["health"],
    summary="Readiness probe",
    description=(
        "Returns ok when the API can serve traffic. Checks database connectivity only. "
        "Does not call the AI provider."
    ),
)
def health_ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error(
            "readiness check failed",
            extra={
                "event": "health_ready_failed",
                "error_type": type(exc).__name__,
            },
        )
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "checks": {"database": "fail"},
            },
        )
    return ReadyHealthResponse(status="ok", checks={"database": "ok"})


@app.get(
    f"{API_V1_PREFIX}/health",
    response_model=HealthResponse,
    status_code=200,
    tags=["health"],
    summary="Health check (legacy)",
    description="Alias of `/health/live` for backwards compatibility.",
    include_in_schema=False,
)
def health_check() -> HealthResponse:
    return health_live()
