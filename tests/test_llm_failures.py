"""LLM failure and solve-doubt edge cases (Gemini client mocked)."""

import uuid
from unittest.mock import patch

from errors import LLMInvalidRequestError, LLMProviderError
from conftest import API_PREFIX


def test_llm_provider_failure_returns_503(client, registered_user):
    with patch(
        "service.doubt_service.doubt_solver.solve_doubt",
        side_effect=LLMProviderError("AI provider error (400): API key not valid"),
    ):
        response = client.post(
            f"{API_PREFIX}/doubts/solve-doubt",
            headers={"Authorization": f"Bearer {registered_user['access_token']}"},
            data={
                "question": "Explain photosynthesis",
                "subject": "Biology",
                "class_name": "8",
            },
        )

    assert response.status_code == 503
    body = response.json()["error"]
    assert body["code"] == "LLM_PROVIDER_ERROR"
    assert body["message"] == (
        "The AI service is temporarily unavailable. Please try again later."
    )
    assert "api key" not in body["message"].lower()


def test_llm_invalid_request_returns_502(client, registered_user):
    with patch(
        "service.doubt_service.doubt_solver.solve_doubt",
        side_effect=LLMInvalidRequestError("AI provider error (400): API key not valid"),
    ):
        response = client.post(
            f"{API_PREFIX}/doubts/solve-doubt",
            headers={"Authorization": f"Bearer {registered_user['access_token']}"},
            data={
                "question": "Explain gravity",
                "subject": "Physics",
                "class_name": "9",
            },
        )

    assert response.status_code == 502
    body = response.json()["error"]
    assert body["code"] == "LLM_INVALID_REQUEST"
    assert body["message"] == (
        "We couldn't process this doubt right now. Please try again."
    )
    assert "api key" not in body["message"].lower()


def test_llm_failure_rolls_back_and_does_not_consume_credit(
    client, registered_user, db_engine
):
    from models.doubt_models import DoubtModel, UserDetailsModel
    from sqlalchemy.orm import sessionmaker

    with patch(
        "service.doubt_service.doubt_solver.solve_doubt",
        side_effect=LLMProviderError(),
    ):
        response = client.post(
            f"{API_PREFIX}/doubts/solve-doubt",
            headers={"Authorization": f"Bearer {registered_user['access_token']}"},
            data={
                "question": "Will this roll back?",
                "subject": "Mathematics",
                "class_name": "8",
            },
        )
    assert response.status_code == 503

    Session = sessionmaker(bind=db_engine)
    with Session() as session:
        user = (
            session.query(UserDetailsModel)
            .filter(UserDetailsModel.id == uuid.UUID(registered_user["user_id"]))
            .one()
        )
        assert user.available_free_doubts == registered_user["available_free_doubts"]
        assert session.query(DoubtModel).count() == 0


def test_solve_doubt_missing_fields_rejected(client, registered_user):
    response = client.post(
        f"{API_PREFIX}/doubts/solve-doubt",
        headers={"Authorization": f"Bearer {registered_user['access_token']}"},
        data={"question": "Only a question"},
    )
    assert response.status_code == 422
