from fastapi import APIRouter, Cookie, Depends, Response

import database
from config import (
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    REFRESH_COOKIE_NAME,
    REFRESH_TOKEN_DAYS,
)
from service import doubt_service
from dtos.request import AddUserRequest, LoginUserRequest
from dtos.response import (
    AuthResponse,
    LoginUserResponse,
    LogoutResponse,
)
from enums.doubt_enums import ErrorResponse
from security import (
    create_token_pair,
    get_current_user,
    revoke_refresh_token,
    rotate_refresh_token,
)
from errors import AppError, AuthenticationError

AUTH_COOKIE_PATH = "/api/v1/auth"

router = APIRouter(tags=["users"])
account_router = APIRouter(
    tags=["users"],
    dependencies=[Depends(get_current_user)],
)
users_router = APIRouter(
    tags=["users"],
    dependencies=[Depends(get_current_user)],
)


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        max_age=REFRESH_TOKEN_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path=AUTH_COOKIE_PATH,
    )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=200,
    summary="Register a new user",
    description=(
        "Create a student account. New users start with 10 free doubt credits. "
        "Email must be unique. Returns an access token and sets a refresh cookie."
    ),
)
def add_user(request: AddUserRequest, http_response: Response) -> AuthResponse:
    created, error = doubt_service.add_user(request)
    if error:
        raise AppError("REGISTRATION_ERROR", error.value, 400)

    user = LoginUserResponse(
        user_id=created.user_id,
        name=created.name,
        email=created.email,
        available_free_doubts=created.available_free_doubts,
    )

    session = database.SessionLocal()
    try:
        tokens = create_token_pair(user.user_id, session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    _set_refresh_cookie(http_response, tokens.refresh_token)
    return AuthResponse(access_token=tokens.access_token, user=user)


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=200,
    summary="Log in",
    description="Authenticate with email and password. Returns a short-lived access token.",
)
def login_user(request: LoginUserRequest, http_response: Response) -> AuthResponse:
    user, error = doubt_service.login_user(request)
    if error:
        if error in {ErrorResponse.USER_NOT_FOUND, ErrorResponse.PASSWORD_INCORRECT}:
            raise AuthenticationError("Invalid email or password")
        raise AppError("LOGIN_ERROR", error.value, 400)

    session = database.SessionLocal()
    try:
        tokens = create_token_pair(user.user_id, session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    _set_refresh_cookie(http_response, tokens.refresh_token)
    return AuthResponse(access_token=tokens.access_token, user=user)


@account_router.get(
    "/me",
    response_model=LoginUserResponse,
    status_code=200,
    summary="Get the authenticated user's profile",
    description="Returns the profile and usage counts for the access-token owner.",
)
def get_user_details(
    current_user=Depends(get_current_user),
) -> LoginUserResponse:
    response, error = doubt_service.get_user_details(current_user.id)
    if error:
        raise AppError("USER_PROFILE_ERROR", error.value, 400)
    return response


@users_router.get(
    "/me",
    response_model=LoginUserResponse,
    status_code=200,
    summary="Get the authenticated user (/users/me)",
    description=(
        "Canonical identity endpoint. Frontend session state should be derived "
        "from this authenticated response, not from locally editable storage."
    ),
)
def get_authenticated_user(
    current_user=Depends(get_current_user),
) -> LoginUserResponse:
    return get_user_details(current_user)


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Rotate the refresh token",
)
def refresh_access_token(
    http_response: Response,
    refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME),
) -> AuthResponse:
    if not refresh_token:
        raise AuthenticationError("Please sign in again.")

    session = database.SessionLocal()
    try:
        tokens = rotate_refresh_token(refresh_token, session)
        session.commit()
    except AuthenticationError:
        session.commit()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    user, error = doubt_service.get_user_details(tokens.user_id)
    if error:
        raise AuthenticationError("Please sign in again.")

    _set_refresh_cookie(http_response, tokens.refresh_token)
    return AuthResponse(access_token=tokens.access_token, user=user)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Log out and revoke the refresh token",
)
def logout(
    http_response: Response,
    refresh_token: str | None = Cookie(None, alias=REFRESH_COOKIE_NAME),
) -> LogoutResponse:
    if refresh_token:
        session = database.SessionLocal()
        try:
            revoke_refresh_token(refresh_token, session)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    http_response.delete_cookie(
        REFRESH_COOKIE_NAME,
        path=AUTH_COOKIE_PATH,
        secure=COOKIE_SECURE,
        httponly=True,
        samesite=COOKIE_SAMESITE,
    )
    return LogoutResponse(message="Logged out")
