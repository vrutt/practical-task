from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_async_db
from app.modules.user.models import User
from app.modules.user.repository import RefreshTokenRepository, UserRepository
from app.modules.user.schemas import RoleType
from app.security.jwt_service import JWTService
from app.utils.constant import ApiMessages, AuthValues

# Subclassing HTTPBearer registers the same scheme in OpenAPI and validates it here.
Db = Annotated[AsyncSession, Depends(get_async_db, scope="function")]


class AccessTokenAuth(HTTPBearer):
    def __init__(self):
        super().__init__(
            scheme_name="AccessToken",
            bearerFormat="JWT",
            auto_error=False,
            description="Paste an access JWT without the Bearer prefix.",
        )
        self.jwt = JWTService()

    async def __call__(self, request: Request) -> dict:
        """Authenticate a bearer header or the existing HTTP-only access cookie."""
        credentials = await super().__call__(request)
        if request.headers.get("authorization") and credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail=ApiMessages.INVALID_AUTH_HEADER_MESSAGE
            )
        token = credentials.credentials if credentials else request.cookies.get(AuthValues.ACCESS_COOKIE)
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ApiMessages.AUTH_REQUIRED_MESSAGE)
        return self.jwt.decode(token, AuthValues.ACCESS_TOKEN)


access_token_auth = AccessTokenAuth()


async def current_user(db: Db, claims: Annotated[dict, Depends(access_token_auth)]) -> User:
    """Require a current session and load its user for each protected request."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session = await RefreshTokenRepository(db).active_session(claims["sid"], claims["sub"], now)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ApiMessages.INVALID_SESSION_MESSAGE)
    user = await UserRepository(db).by_id(claims["sub"])
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=ApiMessages.INVALID_SESSION_MESSAGE)
    return user


class RequireRoles:
    def __init__(self, *roles: RoleType):
        self.roles = frozenset(roles)

    async def __call__(self, user: Annotated[User, Depends(current_user)]) -> User:
        """Reject users whose current role is not permitted."""
        if user.role not in self.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=ApiMessages.FORBIDDEN_MESSAGE)
        return user
