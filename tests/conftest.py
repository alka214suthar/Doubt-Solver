"""Shared fixtures for API tests (SQLite + mocked LLM)."""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR))

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET"] = "test-secret-key-for-jwt-signing-in-unit-tests"
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("QUESTION_CACHE_ENABLED", "false")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

from database import Base  # noqa: E402
import models.doubt_models  # noqa: E402, F401 — register metadata
from dtos.response import DoubtSolverResponse  # noqa: E402
from main import app  # noqa: E402

API_PREFIX = "/api/v1"
AUTH_COOKIE_PATH = "/api/v1/auth"


def error_message(response) -> str:
    body = response.json()
    if isinstance(body.get("error"), dict):
        return body["error"].get("message", "")
    return str(body.get("detail", ""))


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client(db_engine, tmp_path):
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )
    mock_solution = DoubtSolverResponse(
        answer="The answer is 4.",
        hints=["Think about addition.", "2 + 2", "Simple arithmetic"],
        steps=["Identify the numbers.", "Add them together.", "Result is 4."],
    )

    with (
        patch("decorators.decorators.SessionLocal", TestingSessionLocal),
        patch("database.SessionLocal", TestingSessionLocal),
        patch("image_uploads.UPLOAD_DIR", tmp_path),
        patch(
            "service.doubt_service.doubt_solver.solve_doubt",
            return_value=mock_solution,
        ),
    ):
        yield TestClient(app)


def register_user(client, *, name="Test User", password="secret123"):
    email = f"user_{uuid.uuid4().hex[:10]}@example.com"
    payload = {
        "name": name,
        "email": email,
        "password": password,
    }
    response = client.post(f"{API_PREFIX}/auth/register", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    return {
        **payload,
        "user_id": data["user"]["user_id"],
        "available_free_doubts": data["user"]["available_free_doubts"],
        "access_token": data["access_token"],
    }


@pytest.fixture()
def registered_user(client):
    return register_user(client)


@pytest.fixture()
def second_user(client):
    return register_user(client, name="Other User", password="other-secret")


@pytest.fixture()
def solved_doubt(client, registered_user):
    response = client.post(
        f"{API_PREFIX}/doubts/solve-doubt",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        data={
            "question": "What is 2 + 2?",
            "subject": "Mathematics",
            "class_name": "8",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    return {
        "user": registered_user,
        "doubt_id": body["doubt_id"],
        "answer": body["answer"],
        "hints": body["hints"],
        "steps": body["steps"],
    }
