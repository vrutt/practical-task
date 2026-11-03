"""Opt-in PostgreSQL integration test; use a dedicated, disposable test database."""

import asyncio
import os
from uuid import uuid4

import pytest
from conftest import APPLICATION_DATABASE_NAMES
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config.database import get_async_db
from app.main import app
from app.utils.base_model import Base

POSTGRES_URL = os.getenv("TEST_POSTGRES_DATABASE_URL")
pytestmark = pytest.mark.skipif(not POSTGRES_URL, reason="Set TEST_POSTGRES_DATABASE_URL to a dedicated test database")


async def test_concurrent_refresh_allows_only_one_use():
    """Two requests using one token cannot both rotate it on PostgreSQL."""
    test_url = make_url(POSTGRES_URL)
    if not test_url.database or not (test_url.database.startswith("test_") or test_url.database.endswith("_test")):
        raise RuntimeError("PostgreSQL tests require a dedicated database named test_* or *_test")
    if test_url.database in APPLICATION_DATABASE_NAMES:
        raise RuntimeError("The test database name must differ from the application database")
    schema = f"auth_test_{uuid4().hex}"
    admin_engine = create_async_engine(POSTGRES_URL)
    schema_created = False
    engine = None
    try:
        async with admin_engine.begin() as conn:
            # The schema is generated locally and contains only hex characters.
            await conn.execute(text(f'CREATE SCHEMA "{schema}"'))
            schema_created = True
        engine = create_async_engine(POSTGRES_URL, connect_args={"server_settings": {"search_path": schema}})
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
        transport = ASGITransport(app=app)
        headers = {"Origin": "http://localhost:3000"}
        async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
            payload = {"name": "Test", "email": "test@example.com", "password": "Secure-Password1!"}
            assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 201
            assert (
                await client.post(
                    "/api/v1/auth/login", json={"email": payload["email"], "password": payload["password"]}
                )
            ).status_code == 200
            old_token = client.cookies["refresh_token"]

        async def rotate():
            async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
                client.cookies.set("refresh_token", old_token, domain="test.local", path="/")
                return (await client.post("/api/v1/auth/refresh")).status_code

        assert sorted(await asyncio.gather(rotate(), rotate())) == [200, 401]
    finally:
        app.dependency_overrides.pop(get_async_db, None)
        if engine is not None:
            await engine.dispose()
        if schema_created:
            async with admin_engine.begin() as conn:
                await conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await admin_engine.dispose()
