"""User-facing error copy. Technical details stay in logs only."""

from __future__ import annotations

DEFAULT_MESSAGE = "Something went wrong. Please try again."

# Stable codes → short messages users can understand (no API/DB jargon).
CODE_MESSAGES: dict[str, str] = {
    "AUTHENTICATION_ERROR": "Please sign in again.",
    "VALIDATION_ERROR": "Please check your input and try again.",
    "DATABASE_ERROR": DEFAULT_MESSAGE,
    "DATABASE_CONSTRAINT_ERROR": DEFAULT_MESSAGE,
    "INTERNAL_SERVER_ERROR": DEFAULT_MESSAGE,
    "NOT_FOUND": "We couldn't find what you're looking for.",
    "HTTP_ERROR": DEFAULT_MESSAGE,
    "LLM_PROVIDER_ERROR": (
        "The AI service is temporarily unavailable. Please try again later."
    ),
    "LLM_INVALID_REQUEST": (
        "We couldn't process this doubt right now. Please try again."
    ),
    "RATE_LIMIT_EXCEEDED": "Too many requests. Please try again later.",
    "REGISTRATION_ERROR": DEFAULT_MESSAGE,
    "LOGIN_ERROR": DEFAULT_MESSAGE,
    "USER_PROFILE_ERROR": DEFAULT_MESSAGE,
    "SOLVE_DOUBT_ERROR": DEFAULT_MESSAGE,
    "DELETE_DOUBT_ERROR": DEFAULT_MESSAGE,
    "BOOKMARK_ERROR": DEFAULT_MESSAGE,
    "FEEDBACK_ERROR": DEFAULT_MESSAGE,
    "DOUBT_HISTORY_ERROR": DEFAULT_MESSAGE,
    "BOOKMARK_HISTORY_ERROR": DEFAULT_MESSAGE,
}

# Explicit strings that are already safe to show as-is.
ALLOWED_MESSAGES: frozenset[str] = frozenset(
    {
        "Invalid email or password",
        "An account with this email already exists.",
        "You've used all your free doubts.",
        "We couldn't find that doubt.",
        "We couldn't find that solution.",
        "We couldn't find your account.",
        "Please check the date range and try again.",
        "Only .jpg, .jpeg, .png, and .webp images are allowed.",
        "Image must be 5 MB or smaller.",
        "Uploaded file is not a valid image.",
        "Image content must be JPEG, PNG, or WebP.",
        "Image extension does not match its content.",
        "Too many requests. Please try again later.",
        "Please sign in again.",
        "Please check your input and try again.",
        "We couldn't find what you're looking for.",
        "The AI service is temporarily unavailable. Please try again later.",
        "We couldn't process this doubt right now. Please try again.",
        "You don't have permission to do that.",
        "That action isn't allowed.",
        "That file is too large. Please try a smaller one.",
        DEFAULT_MESSAGE,
    }
)

STATUS_MESSAGES: dict[int, str] = {
    400: DEFAULT_MESSAGE,
    401: "Please sign in again.",
    403: "You don't have permission to do that.",
    404: "We couldn't find what you're looking for.",
    405: "That action isn't allowed.",
    409: DEFAULT_MESSAGE,
    413: "That file is too large. Please try a smaller one.",
    422: "Please check your input and try again.",
    429: "Too many requests. Please try again later.",
    500: DEFAULT_MESSAGE,
    502: DEFAULT_MESSAGE,
    503: DEFAULT_MESSAGE,
}


def resolve_user_message(
    code: str,
    message: str | None = None,
    *,
    status_code: int | None = None,
) -> str:
    """Pick a basic user message; never echo technical backend detail."""
    if isinstance(message, str) and message in ALLOWED_MESSAGES:
        return message

    # File validation messages are crafted for users; allow them through.
    if code == "FILE_VALIDATION_ERROR" and isinstance(message, str) and message.strip():
        return message.strip()

    # Prefer status-specific copy for generic HTTP errors (403, 413, etc.).
    if (
        code == "HTTP_ERROR"
        and status_code is not None
        and status_code in STATUS_MESSAGES
    ):
        return STATUS_MESSAGES[status_code]

    if code in CODE_MESSAGES:
        return CODE_MESSAGES[code]

    if status_code is not None and status_code in STATUS_MESSAGES:
        return STATUS_MESSAGES[status_code]

    return DEFAULT_MESSAGE
