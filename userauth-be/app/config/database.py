from typing import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import settings


def create_database_engine() -> AsyncEngine:
    """Create the async database engine using configured pool settings."""
    options = {"echo": False, "pool_pre_ping": True}
    # SQLite in-memory tests use StaticPool, which does not accept queue pool options.
    if not settings.ASYNC_DATABASE_URL.startswith("sqlite"):
        options.update(
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_timeout=settings.DATABASE_POOL_TIMEOUT,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
        )
    return create_async_engine(settings.ASYNC_DATABASE_URL, **options)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a factory for request-scoped async sessions."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


async def get_async_db(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    """Yield a session and commit or roll back its transaction."""
    session_factory = request.app.state.db_session_factory

    async with session_factory() as session:
        try:
            yield session
            await session.commit()

        except Exception:
            await session.rollback()
            raise
