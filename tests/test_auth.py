"""Auth endpoint tests."""

import uuid

from conftest import API_PREFIX, AUTH_COOKIE_PATH, error_message


def test_register_success(client, db_engine):
    email = f"new_{uuid.uuid4().hex[:8]}@example.com"
    response = client.post(
        f"{API_PREFIX}/auth/register",
        json={"name": "Alice", "email": email, "password": "pass1234"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["name"] == "Alice"
    assert body["user"]["email"] == email
    assert body["user"]["available_free_doubts"] == 10
    assert body["user"]["user_id"]

    from models.doubt_models import UserDetailsModel
    from sqlalchemy.orm import sessionmaker

    with sessionmaker(bind=db_engine)() as session:
        stored = session.query(UserDetailsModel).filter_by(email=email).one()
        assert stored.password != "pass1234"
        assert stored.password.startswith("$argon2")


def test_register_normalizes_email(client, db_engine):
    response = client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "Alice",
            "email": "  Ada@Example.COM ",
            "password": "pass1234",
        },
    )
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "ada@example.com"

    from models.doubt_models import UserDetailsModel
    from sqlalchemy.orm import sessionmaker

    with sessionmaker(bind=db_engine)() as session:
        stored = (
            session.query(UserDetailsModel)
            .filter_by(email="ada@example.com")
            .one()
        )
        assert stored.email == "ada@example.com"


def test_register_duplicate_email(client, registered_user):
    response = client.post(
        f"{API_PREFIX}/auth/register",
        json={
            "name": "Other",
            "email": registered_user["email"].upper(),
            "password": "another-password",
        },
    )
    assert response.status_code == 400
    assert "already exists" in error_message(response).lower()


def test_login_success(client, registered_user):
    response = client.post(
        f"{API_PREFIX}/auth/login",
        json={
            "email": registered_user["email"].upper(),
            "password": registered_user["password"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["user_id"] == registered_user["user_id"]
    assert body["user"]["email"] == registered_user["email"]


def test_login_wrong_password(client, registered_user):
    response = client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": registered_user["email"], "password": "wrong-password"},
    )
    assert response.status_code == 401
    body = response.json()["error"]
    assert body["code"] == "AUTHENTICATION_ERROR"
    assert body["message"] == "Invalid email or password"
    assert body["request_id"]


def test_login_user_not_found(client):
    response = client.post(
        f"{API_PREFIX}/auth/login",
        json={"email": "missing@example.com", "password": "whatever"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid email or password"


def test_get_user_details_success(client, registered_user):
    response = client.get(
        f"{API_PREFIX}/auth/me",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == registered_user["user_id"]
    assert body["doubts_asked"] == 0
    assert body["bookmarks"] == 0
    assert body["first_doubt_asked_at"] is None


def test_users_me_canonical_identity_endpoint(client, registered_user):
    response = client.get(
        f"{API_PREFIX}/users/me",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == registered_user["user_id"]
    assert body["email"] == registered_user["email"]


def test_get_user_details_requires_authentication(client):
    response = client.get(f"{API_PREFIX}/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_ERROR"


def test_refresh_rotation_and_logout(client, registered_user):
    first_refresh = client.post(f"{API_PREFIX}/auth/refresh")
    assert first_refresh.status_code == 200
    assert first_refresh.json()["access_token"]

    logout = client.post(f"{API_PREFIX}/auth/logout")
    assert logout.status_code == 200
    assert client.post(f"{API_PREFIX}/auth/refresh").status_code == 401


def test_reused_refresh_token_revokes_its_token_family(client, registered_user):
    old_token = client.cookies.get("refresh_token")
    rotated = client.post(f"{API_PREFIX}/auth/refresh")
    assert rotated.status_code == 200
    new_token = client.cookies.get("refresh_token")
    assert new_token != old_token

    client.cookies.set("refresh_token", old_token, path=AUTH_COOKIE_PATH)
    assert client.post(f"{API_PREFIX}/auth/refresh").status_code == 401

    client.cookies.set("refresh_token", new_token, path=AUTH_COOKIE_PATH)
    assert client.post(f"{API_PREFIX}/auth/refresh").status_code == 401
