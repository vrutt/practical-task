"""Load isolated test settings before importing the application."""

import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import make_url

backend_dir = Path(__file__).resolve().parents[1]
application_urls = [os.environ.get("ASYNC_DATABASE_URL"), dotenv_values(backend_dir / ".env").get("ASYNC_DATABASE_URL")]
APPLICATION_DATABASE_NAMES = {make_url(url).database for url in application_urls if url}
config = dotenv_values(backend_dir / ".env.test")
if config.get("ASYNC_DATABASE_URL") != "sqlite+aiosqlite:///:memory:" or config.get("ENVIRONMENT") != "test":
    raise RuntimeError("The test configuration must use the isolated in-memory database")
os.environ.update({key: value for key, value in config.items() if value is not None})

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.config.database import get_async_db  # noqa: E402
from app.main import app  # noqa: E402
from app.utils.base_model import Base  # noqa: E402

ORIGIN = {"Origin": "http://localhost:3000"}
USER = {"name": "Ada", "email": "ada@example.com", "password": "Correct-Horse1!"}


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def override():
        async with sessions() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_async_db] = override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", headers=ORIGIN) as c:
        c.test_sessions = sessions
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()
