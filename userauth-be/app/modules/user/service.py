from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.modules.user.models import RefreshToken, User
from app.modules.user.repository import RefreshTokenRepository, UserRepository
from app.modules.user.schemas import InvalidCredentialsError, InvalidSessionError, Registration
from app.security.jwt_service import JWTService
from app.security.password_helpers import password_helper
from app.utils.constant import AuthValues


class UserService:
    def __init__(self, db: AsyncSession):
        self.users = UserRepository(db)
        self.tokens = RefreshTokenRepository(db)
        self.jwt = JWTService()

    async def register(self, data: Registration) -> User:
        """Create a user with a securely hashed password."""
        user = User(name=data.name, email=str(data.email).lower(), password=password_helper.hash(data.password))
        return await self.users.add(user)

    async def authenticate(self, email: str, password: str) -> User:
        """Validate credentials without revealing whether the email exists."""
        user = await self.users.by_email(email.lower())
        valid = password_helper.verify(password, user.password if user else None)
        if not valid or user is None:
            raise InvalidCredentialsError()
        return user

    async def login(self, email: str, password: str) -> tuple[User, tuple[str, str]]:
        """Authenticate the user and issue a token pair."""
        user = await self.authenticate(email, password)
        return user, await self.issue_tokens(user)

    async def issue_tokens(self, user: User) -> tuple[str, str]:
        """Issue access and refresh tokens and persist the refresh-token hash."""
        access = self.jwt.create(user.id, AuthValues.ACCESS_TOKEN)
        refresh = self.jwt.create(user.id, AuthValues.REFRESH_TOKEN)
        expires = datetime.now(timezone.utc).replace(tzinfo=None) + settings.refresh_lifetime
        await self.tokens.add(RefreshToken(user_id=user.id, token_hash=self.jwt.digest(refresh), expires_at=expires))
        return access, refresh

    async def rotate(self, token: str | None) -> tuple[str, str]:
        """Revoke a valid refresh token and issue a new pair atomically."""
        if not token:
            raise InvalidSessionError()
        payload = self.jwt.decode(token, AuthValues.REFRESH_TOKEN)
        record = await self.tokens.by_hash_for_update(self.jwt.digest(token))
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if not record or record.revoked_at or record.expires_at <= now or str(record.user_id) != payload["sub"]:
            raise InvalidSessionError()
        user = await self.users.by_id(record.user_id)
        if user is None:
            raise InvalidSessionError()
        await self.tokens.update(record, revoked_at=now)
        return await self.issue_tokens(user)

    async def revoke(self, token: str | None) -> None:
        """Revoke a refresh token if it exists."""
        if not token:
            return
        record = await self.tokens.by_hash_for_update(self.jwt.digest(token))
        if record and not record.revoked_at:
            await self.tokens.update(record, revoked_at=datetime.now(timezone.utc).replace(tzinfo=None))

    async def list_users(self) -> list[User]:
        """Return users for an authorized caller."""
        return await self.users.list_all()
