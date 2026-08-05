"""Doubt solve, history, and feedback tests."""

import datetime
import io
import os
import uuid

from PIL import Image

from conftest import API_PREFIX, error_message


def _png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2), color="white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_health_check(client):
    response = client.get(f"{API_PREFIX}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_live(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers


def test_health_ready(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["checks"]["database"] == "ok"


def test_solve_doubt_success(client, registered_user):
    response = client.post(
        f"{API_PREFIX}/doubts/solve-doubt",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        data={
            "question": "What is 2 + 2?",
            "subject": "Mathematics",
            "class_name": "8",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["doubt_id"]
    assert body["answer"] == "The answer is 4."
    assert len(body["hints"]) == 3
    assert len(body["steps"]) == 3

    details = client.get(
        f"{API_PREFIX}/auth/me",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
    )
    assert details.status_code == 200
    assert details.json()["doubts_asked"] == 1
    assert details.json()["available_free_doubts"] == 9


def test_solve_doubt_accepts_valid_image_with_generated_name(
    client, registered_user, tmp_path
):
    response = client.post(
        f"{API_PREFIX}/doubts/solve-doubt",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        data={
            "question": "What is shown?",
            "subject": "Mathematics",
            "class_name": "8",
        },
        files={"image": ("my original.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 200
    history = client.get(
        f"{API_PREFIX}/user_doubts",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
    ).json()
    stored_name = history["items"][0]["img_url"].removeprefix("uploads/")
    assert stored_name != "my original.png"
    assert len(stored_name) == 36
    assert stored_name.endswith(".png")
    assert (tmp_path / stored_name).is_file()


def test_solve_doubt_rejects_unsupported_extension(client, registered_user):
    response = client.post(
        f"{API_PREFIX}/doubts/solve-doubt",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        data={"question": "Q", "subject": "Mathematics", "class_name": "8"},
        files={"image": ("image.gif", b"GIF89a", "image/gif")},
    )

    assert response.status_code == 400
    body = response.json()["error"]
    assert body["code"] == "FILE_VALIDATION_ERROR"
    assert "only" in body["message"].lower()


def test_solve_doubt_rejects_fake_image(client, registered_user):
    response = client.post(
        f"{API_PREFIX}/doubts/solve-doubt",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        data={"question": "Q", "subject": "Mathematics", "class_name": "8"},
        files={"image": ("image.png", b"not an image", "image/png")},
    )

    assert response.status_code == 400
    assert "valid image" in error_message(response).lower()


def test_solve_doubt_rejects_image_over_five_mb(client, registered_user):
    response = client.post(
        f"{API_PREFIX}/doubts/solve-doubt",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        data={"question": "Q", "subject": "Mathematics", "class_name": "8"},
        files={"image": ("image.png", b"x" * (5 * 1024 * 1024 + 1), "image/png")},
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_VALIDATION_ERROR"


def test_solve_doubt_no_free_doubts(client, registered_user, db_engine):
    from models.doubt_models import UserDetailsModel
    from sqlalchemy.orm import sessionmaker

    Session = sessionmaker(bind=db_engine)
    with Session() as session:
        user = (
            session.query(UserDetailsModel)
            .filter(UserDetailsModel.id == uuid.UUID(registered_user["user_id"]))
            .one()
        )
        user.available_free_doubts = 0
        session.commit()

    response = client.post(
        f"{API_PREFIX}/doubts/solve-doubt",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        data={
            "question": "Explain gravity",
            "subject": "Physics",
            "class_name": "9",
        },
    )
    assert response.status_code == 400
    assert "free doubt" in error_message(response).lower()


def test_get_user_doubts_empty(client, registered_user):
    response = client.get(
        f"{API_PREFIX}/user_doubts",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["pagination"] == {
        "page": 1,
        "page_size": 20,
        "total": 0,
        "total_pages": 0,
    }


def test_get_user_doubts_with_data(client, solved_doubt):
    user = solved_doubt["user"]
    response = client.get(
        f"{API_PREFIX}/user_doubts",
        headers={"Authorization": f"Bearer {user['access_token']}"},
    )
    assert response.status_code == 200
    body = response.json()
    doubts = body["items"]
    assert len(doubts) == 1
    assert body["pagination"]["total"] == 1
    assert doubts[0]["doubt_id"] == solved_doubt["doubt_id"]
    assert doubts[0]["question"] == "What is 2 + 2?"
    assert doubts[0]["subject"] == "Mathematics"
    assert doubts[0]["class_name"] == 8
    assert doubts[0]["answer"] == solved_doubt["answer"]
    assert doubts[0]["status"] == "solved"
    assert doubts[0]["is_bookmarked"] is False


def test_get_user_doubts_supports_filters_and_pagination(client, registered_user):
    token = registered_user["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    for subject, class_name, question in [
        ("Mathematics", "8", "Math one"),
        ("Physics", "9", "Physics one"),
        ("Mathematics", "8", "Math two"),
    ]:
        response = client.post(
            f"{API_PREFIX}/doubts/solve-doubt",
            headers=headers,
            data={
                "question": question,
                "subject": subject,
                "class_name": class_name,
            },
        )
        assert response.status_code == 200, response.text

    filtered = client.get(
        f"{API_PREFIX}/user_doubts",
        headers=headers,
        params={"subject": "Mathematics", "class_name": 8, "page": 1, "page_size": 1},
    )
    assert filtered.status_code == 200
    body = filtered.json()
    assert body["pagination"]["total"] == 2
    assert body["pagination"]["page_size"] == 1
    assert body["pagination"]["total_pages"] == 2
    assert len(body["items"]) == 1
    assert body["items"][0]["subject"] == "Mathematics"


def test_user_history_hides_old_doubts_and_deletes_old_images(
    client, solved_doubt, db_engine, tmp_path
):
    from models.doubt_models import DoubtModel
    from sqlalchemy.orm import sessionmaker

    old_image = tmp_path / "old.png"
    old_image.write_bytes(_png_bytes())
    old_time = (datetime.datetime.now() - datetime.timedelta(days=11)).timestamp()
    os.utime(old_image, (old_time, old_time))

    Session = sessionmaker(bind=db_engine)
    with Session() as session:
        doubt = session.query(DoubtModel).filter(
            DoubtModel.id == uuid.UUID(solved_doubt["doubt_id"])
        ).one()
        doubt.created_at = datetime.datetime.utcnow() - datetime.timedelta(days=11)
        doubt.image_url = "uploads/old.png"
        session.commit()

    response = client.get(
        f"{API_PREFIX}/user_doubts",
        headers={"Authorization": f"Bearer {solved_doubt['user']['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert not old_image.exists()


def test_submit_feedback_success(client, solved_doubt):
    response = client.post(
        f"{API_PREFIX}/feedback",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
        json={
            "doubt_id": solved_doubt["doubt_id"],
            "is_doubt_helpful": True,
        },
    )
    assert response.status_code == 200
    assert response.json() == {"isFeedbackSubmitted": True}

    history = client.get(
        f"{API_PREFIX}/user_doubts",
        headers={
            "Authorization": f"Bearer {solved_doubt['user']['access_token']}"
        },
    )
    assert history.status_code == 200
    assert history.json()["items"][0]["is_doubt_helpful"] is True


def test_submit_feedback_doubt_not_found(client, registered_user):
    response = client.post(
        f"{API_PREFIX}/feedback",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        json={
            "doubt_id": str(uuid.uuid4()),
            "is_doubt_helpful": False,
        },
    )
    assert response.status_code == 400
    assert "couldn't find" in error_message(response).lower()
