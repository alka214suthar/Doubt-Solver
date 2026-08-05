"""Bookmark endpoint tests."""

import uuid

from conftest import API_PREFIX, error_message


def test_bookmark_doubt_success(client, solved_doubt):
    response = client.post(
        f"{API_PREFIX}/bookmark",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
        json={
            "doubt_id": solved_doubt["doubt_id"],
            "is_bookmarked": True,
        },
    )
    assert response.status_code == 200
    assert response.json() == {"isBookmarkSubmitted": True}

    details = client.get(
        f"{API_PREFIX}/auth/me",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
    )
    assert details.status_code == 200
    assert details.json()["bookmarks"] == 1


def test_bookmark_doubt_not_found(client, registered_user):
    response = client.post(
        f"{API_PREFIX}/bookmark",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        json={"doubt_id": str(uuid.uuid4()), "is_bookmarked": True},
    )
    assert response.status_code == 400
    assert "couldn't find" in error_message(response).lower()


def test_get_bookmarked_doubts_empty(client, registered_user):
    response = client.get(
        f"{API_PREFIX}/bookmarked_doubts",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["pagination"]["total"] == 0


def test_get_bookmarked_doubts_with_data(client, solved_doubt):
    bookmark = client.post(
        f"{API_PREFIX}/bookmark",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
        json={
            "doubt_id": solved_doubt["doubt_id"],
            "is_bookmarked": True,
        },
    )
    assert bookmark.status_code == 200

    response = client.get(
        f"{API_PREFIX}/bookmarked_doubts",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
    )
    assert response.status_code == 200
    bookmarks = response.json()["items"]
    assert len(bookmarks) == 1
    assert bookmarks[0]["doubt_id"] == solved_doubt["doubt_id"]
    assert bookmarks[0]["question"] == "What is 2 + 2?"
    assert bookmarks[0]["answer"] == solved_doubt["answer"]


def test_unbookmark_doubt(client, solved_doubt):
    client.post(
        f"{API_PREFIX}/bookmark",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
        json={
            "doubt_id": solved_doubt["doubt_id"],
            "is_bookmarked": True,
        },
    )
    unbookmark = client.post(
        f"{API_PREFIX}/bookmark",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
        json={
            "doubt_id": solved_doubt["doubt_id"],
            "is_bookmarked": False,
        },
    )
    assert unbookmark.status_code == 200
    assert unbookmark.json() == {"isBookmarkSubmitted": True}

    response = client.get(
        f"{API_PREFIX}/bookmarked_doubts",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
    )
    assert response.status_code == 200
    assert response.json()["items"] == []

    history = client.get(
        f"{API_PREFIX}/user_doubts",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
    )
    assert history.status_code == 200
    assert history.json()["items"][0]["is_bookmarked"] is False


def test_bookmark_flag_visible_in_history(client, solved_doubt):
    client.post(
        f"{API_PREFIX}/bookmark",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
        json={
            "doubt_id": solved_doubt["doubt_id"],
            "is_bookmarked": True,
        },
    )
    history = client.get(
        f"{API_PREFIX}/user_doubts",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
    )
    assert history.status_code == 200
    assert history.json()["items"][0]["is_bookmarked"] is True


def test_user_cannot_bookmark_another_users_doubt(client, solved_doubt):
    email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    password = "other-secret"
    assert client.post(
        f"{API_PREFIX}/auth/register",
        json={"name": "Other User", "email": email, "password": password},
    ).status_code == 200
    login = client.post(
        f"{API_PREFIX}/auth/login", json={"email": email, "password": password}
    )
    other_token = login.json()["access_token"]

    response = client.post(
        f"{API_PREFIX}/bookmark",
        headers={"Authorization": f"Bearer {other_token}"},
        json={"doubt_id": solved_doubt["doubt_id"], "is_bookmarked": True},
    )
    assert response.status_code == 400
    assert "couldn't find" in error_message(response).lower()

    history = client.get(
        f"{API_PREFIX}/user_doubts",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert history.status_code == 200
    assert history.json()["items"] == []
