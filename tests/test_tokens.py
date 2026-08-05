"""Token validity tests (invalid / expired access tokens)."""

import datetime
import uuid

import jwt

from config import JWT_ALGORITHM, JWT_SECRET
from conftest import API_PREFIX


def _access_token(user_id: str, *, expired: bool = False) -> str:
    now = datetime.datetime.utcnow()
    if expired:
        issued_at = now - datetime.timedelta(hours=2)
        expires_at = now - datetime.timedelta(minutes=1)
    else:
        issued_at = now
        expires_at = now + datetime.timedelta(minutes=15)
    return jwt.encode(
        {
            "sub": str(user_id),
            "type": "access",
            "iat": issued_at,
            "exp": expires_at,
            "jti": str(uuid.uuid4()),
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def test_invalid_token_fails(client, registered_user):
    response = client.get(
        f"{API_PREFIX}/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


def test_expired_token_fails(client, registered_user):
    token = _access_token(registered_user["user_id"], expired=True)
    response = client.get(
        f"{API_PREFIX}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"
    assert response.json()["error"]["message"] == "Please sign in again."


def test_refresh_token_cannot_be_used_as_access_token(client, registered_user):
    refresh = client.cookies.get("refresh_token")
    assert refresh
    response = client.get(
        f"{API_PREFIX}/auth/me",
        headers={"Authorization": f"Bearer {refresh}"},
    )
    assert response.status_code == 401


def test_protected_solve_doubt_requires_authentication(client):
    response = client.post(
        f"{API_PREFIX}/doubts/solve-doubt",
        data={
            "question": "What is 2 + 2?",
            "subject": "Mathematics",
            "class_name": "8",
        },
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


def test_expired_token_rejected_on_solve_doubt(client, registered_user):
    token = _access_token(registered_user["user_id"], expired=True)
    response = client.post(
        f"{API_PREFIX}/doubts/solve-doubt",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "question": "What is 2 + 2?",
            "subject": "Mathematics",
            "class_name": "8",
        },
    )
    assert response.status_code == 401
