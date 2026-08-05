"""Unit tests for user-facing error message resolution."""

from user_messages import resolve_user_message


def test_allowed_message_passthrough():
    assert (
        resolve_user_message(
            "SOLVE_DOUBT_ERROR",
            "You've used all your free doubts.",
        )
        == "You've used all your free doubts."
    )


def test_technical_message_is_replaced():
    assert (
        resolve_user_message(
            "DATABASE_ERROR",
            "psycopg2.OperationalError: connection refused",
        )
        == "Something went wrong. Please try again."
    )


def test_auth_login_message_kept():
    assert (
        resolve_user_message(
            "AUTHENTICATION_ERROR",
            "Invalid email or password",
        )
        == "Invalid email or password"
    )


def test_auth_token_jargon_replaced():
    assert (
        resolve_user_message(
            "AUTHENTICATION_ERROR",
            "Invalid or expired authentication token",
        )
        == "Please sign in again."
    )


def test_http_status_fallback():
    assert (
        resolve_user_message("NOT_FOUND", status_code=404)
        == "We couldn't find what you're looking for."
    )
    assert (
        resolve_user_message("HTTP_ERROR", status_code=403)
        == "You don't have permission to do that."
    )
