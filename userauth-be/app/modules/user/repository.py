from datetime import datetime

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.models import RefreshToken, User
from app.utils.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)

    async def by_email(self, email: str) -> User | None:
        """Find a user by normalized email."""
        return await self.db.scalar(select(User).where(User.email == email))


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, RefreshToken)

    async def active_session(self, session_id: str, user_id: str, now: datetime) -> RefreshToken | None:
        """Find an unrevoked, unexpired session belonging to the user."""
        return await self.db.scalar(
            select(RefreshToken).where(
                RefreshToken.id == session_id,
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > now,
            )
        )

    async def delete_old(self, cutoff: datetime) -> int:
        """Remove records whose expiry or revocation predates the cutoff."""
        result = await self.db.execute(
            delete(RefreshToken).where(
                or_(
                    RefreshToken.expires_at <= cutoff,
                    RefreshToken.revoked_at <= cutoff,
                )
            )
        )
        return result.rowcount

    async def by_hash_for_update(self, token_hash: str) -> RefreshToken | None:
        """Lock a refresh-token record for safe rotation or revocation."""
        return await self.db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update())


