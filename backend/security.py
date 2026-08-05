import datetime
import hashlib
from dataclasses import dataclass
from uuid import UUID, uuid4

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

import database
from config import (
    ACCESS_TOKEN_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET,
    REFRESH_TOKEN_DAYS,
)
from models.doubt_models import RefreshTokenModel, UserDetailsModel
from errors import AuthenticationError


password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class TokenPair:
    user_id: UUID
    access_token: str
    refresh_token: str


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        return password_hash.verify(password, stored_hash)
    except Exception:
        return False


def _encode_token(user_id: UUID, token_type: str, expires_at: datetime.datetime, **claims) -> str:
    now = datetime.datetime.utcnow()
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": expires_at,
        "jti": str(claims.pop("jti", uuid4())),
        **claims,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _decode_token(token: str, expected_type: str, verify_exp: bool = True) -> dict:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"verify_exp": verify_exp},
        )
        if payload.get("type") != expected_type or not payload.get("sub"):
            raise ValueError("Unexpected token type")
        return payload
    except (jwt.PyJWTError, ValueError, TypeError) as error:
        raise AuthenticationError("Please sign in again.") from error


def create_token_pair(
    user_id: UUID,
    session: Session,
    family_id: UUID | None = None,
) -> TokenPair:
    now = datetime.datetime.utcnow()
    family_id = family_id or uuid4()
    refresh_jti = uuid4()
    access_token = _encode_token(
        user_id,
        "access",
        now + datetime.timedelta(minutes=ACCESS_TOKEN_MINUTES),
    )
    refresh_expires_at = now + datetime.timedelta(days=REFRESH_TOKEN_DAYS)
    refresh_token = _encode_token(
        user_id,
        "refresh",
        refresh_expires_at,
        jti=refresh_jti,
        family_id=str(family_id),
    )
    session.add(
        RefreshTokenModel(
            user_id=user_id,
            family_id=family_id,
            jti=refresh_jti,
            token_hash=_token_digest(refresh_token),
            expires_at=refresh_expires_at,
        )
    )
    session.flush()
    return TokenPair(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
    )


def rotate_refresh_token(refresh_token: str, session: Session) -> TokenPair:
    payload = _decode_token(refresh_token, "refresh")
    token_jti = UUID(payload["jti"])
    family_id = UUID(payload["family_id"])
    stored_token = (
        session.query(RefreshTokenModel)
        .filter(
            RefreshTokenModel.jti == token_jti,
            RefreshTokenModel.token_hash == _token_digest(refresh_token),
        )
        .first()
    )
    if not stored_token or stored_token.revoked_at is not None:
        session.query(RefreshTokenModel).filter(
            RefreshTokenModel.family_id == family_id,
            RefreshTokenModel.revoked_at.is_(None),
        ).update({"revoked_at": datetime.datetime.utcnow()})
        raise AuthenticationError("Please sign in again.")

    now = datetime.datetime.utcnow()
    if stored_token.expires_at <= now:
        stored_token.revoked_at = now
        raise AuthenticationError("Please sign in again.")

    replacement = create_token_pair(stored_token.user_id, session, family_id=family_id)
    replacement_payload = _decode_token(replacement.refresh_token, "refresh")
    stored_token.revoked_at = now
    stored_token.replaced_by_jti = UUID(replacement_payload["jti"])
    session.flush()
    return replacement


def revoke_refresh_token(refresh_token: str, session: Session) -> None:
    try:
        payload = _decode_token(refresh_token, "refresh", verify_exp=False)
        token_jti = UUID(payload["jti"])
    except (AuthenticationError, ValueError, KeyError):
        return

    stored_token = (
        session.query(RefreshTokenModel)
        .filter(
            RefreshTokenModel.jti == token_jti,
            RefreshTokenModel.token_hash == _token_digest(refresh_token),
        )
        .first()
    )
    if stored_token and stored_token.revoked_at is None:
        stored_token.revoked_at = datetime.datetime.utcnow()
        session.flush()


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None:
        raise AuthenticationError()

    payload = _decode_token(credentials.credentials, "access")
    try:
        user_id = UUID(payload["sub"])
    except (ValueError, TypeError) as error:
        raise AuthenticationError("Please sign in again.") from error

    session = database.SessionLocal()
    try:
        user = (
            session.query(UserDetailsModel)
            .filter(
                UserDetailsModel.id == user_id,
                UserDetailsModel.is_active.is_(True),
            )
            .first()
        )
        if not user:
            raise AuthenticationError("Please sign in again.")
        entity = UserDetailsModel.to_entity(user)
        request.state.user_id = entity.id
        return entity
    finally:
        session.close()
