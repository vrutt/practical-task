from sqlalchemy import select
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

    async def by_hash_for_update(self, token_hash: str) -> RefreshToken | None:
        """Lock a refresh-token record for safe rotation or revocation."""
        return await self.db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update())
