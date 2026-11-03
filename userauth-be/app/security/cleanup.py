"""Cleanup of authentication records no longer needed for validation."""

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.user.repository import RefreshTokenRepository
from app.utils.constant import AuthenticationPolicy


async def cleanup_auth_records(factory: async_sessionmaker[AsyncSession]) -> int:
    """Delete expired or revoked tokens beyond the retention period."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    async with factory.begin() as session:
        token_cutoff = now - timedelta(days=AuthenticationPolicy.AUTH_RECORD_RETENTION_DAYS)
        tokens = await RefreshTokenRepository(session).delete_old(token_cutoff)
    return tokens
