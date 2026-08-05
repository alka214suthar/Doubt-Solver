"""Authorization tests: users cannot act on each other's doubts."""

from conftest import API_PREFIX, error_message


def test_user_cannot_read_another_users_doubts(client, solved_doubt, second_user):
    response = client.get(
        f"{API_PREFIX}/user_doubts",
        headers={"Authorization": f"Bearer {second_user['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["pagination"]["total"] == 0


def test_user_cannot_submit_feedback_for_another_users_doubt(
    client, solved_doubt, second_user
):
    response = client.post(
        f"{API_PREFIX}/feedback",
        headers={"Authorization": f"Bearer {second_user['access_token']}"},
        json={"doubt_id": solved_doubt["doubt_id"], "is_doubt_helpful": True},
    )
    assert response.status_code == 400
    assert "couldn't find" in error_message(response).lower()


def test_user_cannot_delete_another_users_doubt(client, solved_doubt, second_user):
    response = client.delete(
        f"{API_PREFIX}/doubts/{solved_doubt['doubt_id']}",
        headers={"Authorization": f"Bearer {second_user['access_token']}"},
    )
    assert response.status_code == 400
    assert "couldn't find" in error_message(response).lower()

    owner_history = client.get(
        f"{API_PREFIX}/user_doubts",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
    )
    assert owner_history.status_code == 200
    assert len(owner_history.json()["items"]) == 1


def test_owner_can_delete_own_doubt(client, solved_doubt):
    response = client.delete(
        f"{API_PREFIX}/doubts/{solved_doubt['doubt_id']}",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
    )
    assert response.status_code == 200
    assert response.json() == {"deleted": True}

    history = client.get(
        f"{API_PREFIX}/user_doubts",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
    )
    assert history.status_code == 200
    assert history.json()["items"] == []
