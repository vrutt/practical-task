import hashlib
import uuid
from datetime import datetime, timezone
from typing import Literal

import jwt
from fastapi import HTTPException, status

from app.config.settings import settings
from app.utils.constant import ApiMessages, AuthValues

TokenKind = Literal["access", "refresh"]


class JWTService:
    @staticmethod
    def digest(token: str) -> str:
        """Hash a token before storing it in the database."""
        return hashlib.sha256(token.encode()).hexdigest()

    def create(self, user_id: str, kind: TokenKind, session_id: str | None = None) -> str:
        """Create a signed token with the appropriate lifetime."""
        now = datetime.now(timezone.utc)
        lifetime = settings.access_lifetime if kind == AuthValues.ACCESS_TOKEN else settings.refresh_lifetime
        secret = settings.JWT_SECRET_KEY if kind == AuthValues.ACCESS_TOKEN else settings.JWT_REFRESH_TOKEN_SECRET
        payload = {"sub": str(user_id), "type": kind, "jti": str(uuid.uuid4()), "iat": now, "exp": now + lifetime}
        if kind == AuthValues.ACCESS_TOKEN:
            if session_id is None:
                raise ValueError("Access tokens require a session ID")
            payload["sid"] = str(session_id)
        return jwt.encode(payload, secret, algorithm=settings.JWT_ALGORITHM)

    def decode(self, token: str, kind: TokenKind) -> dict:
        """Validate a token and return its claims."""
        secret = settings.JWT_SECRET_KEY if kind == AuthValues.ACCESS_TOKEN else settings.JWT_REFRESH_TOKEN_SECRET
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=[settings.JWT_ALGORITHM],
                options={"require": ["sub", "type", "exp", "iat", "jti"]},
            )
            if payload["type"] != kind:
                raise jwt.InvalidTokenError("Wrong token type")
            uuid.UUID(payload["sub"])
            if kind == AuthValues.ACCESS_TOKEN:
                uuid.UUID(payload["sid"])
            return payload
        except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ApiMessages.INVALID_SESSION_MESSAGE)
