from datetime import datetime, timedelta, timezone

import jwt
from conftest import ORIGIN, USER
from httpx import ASGITransport, AsyncClient

from app.config.database import get_async_db
from app.config.settings import settings
from app.main import app


async def test_registration_duplicate_and_validation(client):
    response = await client.post("/auth/register", json=USER)
    assert response.status_code == 201
    assert "password" not in response.json()
    assert (await client.post("/auth/register", json=USER)).status_code == 409
    invalid = await client.post("/auth/register", json={**USER, "email": "bad"})
    assert invalid.status_code == 422
    assert invalid.json()["success"] is False
    assert invalid.json()["errors"][0]["field"] == "email"
    assert USER["password"] not in invalid.text
    assert response.json()["success"] is True
    assert "data" in response.json()
    created_at = response.json()["data"]["created_at"]
    assert datetime.fromisoformat(created_at.replace("Z", "+00:00")).utcoffset() == timedelta(0)


async def test_login_and_protected_profile(client):
    assert (await client.get("/auth/me")).status_code == 401
    await client.post("/auth/register", json=USER)
    assert (await client.post("/auth/login", json={"email": USER["email"], "password": "wrong"})).status_code == 401
    response = await client.post("/auth/login", json={"email": USER["email"], "password": USER["password"]})
    assert response.status_code == 200
    assert all("HttpOnly" in cookie for cookie in response.headers.get_list("set-cookie"))
    assert (await client.get("/auth/me")).json()["data"]["name"] == "Ada"


async def test_refresh_rotation_and_logout(client):
    await client.post("/auth/register", json=USER)
    await client.post("/auth/login", json={"email": USER["email"], "password": USER["password"]})
    old = client.cookies["refresh_token"]
    assert (await client.post("/auth/refresh")).status_code == 200
    new = client.cookies["refresh_token"]
    assert old != new
    client.cookies.set("refresh_token", old, domain="test.local", path="/")
    assert (await client.post("/auth/refresh")).status_code == 401
    client.cookies.set("refresh_token", new, domain="test.local", path="/")
    assert (await client.post("/auth/logout")).status_code == 200
    client.cookies.set("refresh_token", new, domain="test.local", path="/")
    assert (await client.post("/auth/refresh")).status_code == 401
    assert (await client.get("/auth/me")).status_code == 401


async def test_expired_refresh_and_origin_rejected(client):
    await client.post("/auth/register", json=USER)
    response = await client.post("/auth/login", json={"email": USER["email"], "password": USER["password"]})
    payload = jwt.decode(
        client.cookies["refresh_token"], settings.JWT_REFRESH_TOKEN_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    payload["exp"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    expired = jwt.encode(payload, settings.JWT_REFRESH_TOKEN_SECRET, algorithm=settings.JWT_ALGORITHM)
    client.cookies.set("refresh_token", expired, domain="test.local", path="/")
    assert (await client.post("/auth/refresh")).status_code == 401
    assert (await client.post("/auth/logout", headers={"Origin": "https://attacker.example"})).status_code == 403
    assert response.status_code == 200


async def test_openapi_documents_response_models(client):
    spec = (await client.get("/openapi.json")).json()
    responses = spec["paths"]["/auth/register"]["post"]["responses"]
    assert "201" in responses and "422" in responses and "409" in responses
    assert responses["422"]["content"]["application/json"]["schema"]["$ref"].endswith("/ErrorResponse")


async def test_bearer_access_token_and_swagger_security(client):
    await client.post("/auth/register", json=USER)
    await client.post("/auth/login", json={"email": USER["email"], "password": USER["password"]})
    token = client.cookies["access_token"]
    client.cookies.clear()
    assert (await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})).status_code == 200
    assert (await client.get("/auth/me", headers={"Authorization": "Bearer invalid"})).status_code == 401
    assert (await client.get("/auth/me")).status_code == 401
    spec = (await client.get("/openapi.json")).json()
    assert spec["components"]["securitySchemes"]["AccessToken"]["scheme"] == "bearer"
    assert {"AccessToken": []} in spec["paths"]["/auth/me"]["get"]["security"]


async def test_admin_access_and_registration_cannot_assign_role(client):
    from sqlalchemy import select

    from app.modules.user.models import User
    from app.modules.user.schemas import RoleType

    assert (await client.post("/auth/register", json={**USER, "role": "Admin"})).status_code == 422
    await client.post("/auth/register", json=USER)
    await client.post("/auth/login", json={"email": USER["email"], "password": USER["password"]})
    assert (await client.get("/auth/users")).status_code == 403
    async with client.test_sessions() as session:
        user = await session.scalar(select(User).where(User.email == USER["email"]))
        user.role = RoleType.Admin
        await session.commit()
    response = await client.get("/auth/users")
    assert response.status_code == 200
    assert response.json()["data"][0]["role"] == "Admin"
    assert "password" not in response.json()["data"][0]


async def test_invalid_header_cannot_fall_back_to_valid_cookie(client):
    await client.post("/auth/register", json=USER)
    await client.post("/auth/login", json={"email": USER["email"], "password": USER["password"]})
    assert (await client.get("/auth/me", headers={"Authorization": "Basic bad"})).status_code == 401
    assert (await client.get("/auth/me")).status_code == 200


async def test_commit_failure_does_not_return_success_or_set_cookies(client):
    await client.post("/auth/register", json=USER)

    async def failing_transaction():
        async with client.test_sessions() as session:
            try:
                yield session
                raise RuntimeError("simulated commit failure")
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_async_db] = failing_transaction
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test", headers=ORIGIN
    ) as failing_client:
        response = await failing_client.post("/auth/login", json={"email": USER["email"], "password": USER["password"]})
        assert response.status_code == 500
        assert response.json()["success"] is False
        assert not response.headers.get_list("set-cookie")

    from sqlalchemy import func, select

    from app.modules.user.models import RefreshToken

    async with client.test_sessions() as session:
        assert await session.scalar(select(func.count()).select_from(RefreshToken)) == 0


async def test_unique_errors_are_generic_and_do_not_expose_values(client, monkeypatch):
    from sqlalchemy.exc import IntegrityError

    from app.modules.user.repository import UserRepository

    class FakeUniqueViolation(Exception):
        sqlstate = "23505"

    async def fail_insert(self, entity):
        raise IntegrityError("INSERT ...", {"password": "private-value"}, FakeUniqueViolation("private-value"))

    monkeypatch.setattr(UserRepository, "add", fail_insert)
    response = await client.post("/auth/register", json=USER)
    assert response.status_code == 409
    assert "private-value" not in response.text
    assert response.json()["message"] == "A record with this value already exists"


async def test_cors_and_origin_guard_share_configured_origins(client):
    for origin in ("http://localhost:3000", "http://localhost:3001"):
        preflight = await client.options(
            "/auth/register",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            },
        )
        assert preflight.status_code == 200
        assert preflight.headers["access-control-allow-origin"] == origin
        response = await client.post("/auth/logout", headers={"Origin": origin})
        assert response.status_code == 200
    denied = await client.options(
        "/auth/register", headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST"}
    )
    assert denied.status_code == 400
    assert (await client.post("/auth/logout", headers={"Origin": "https://untrusted.example"})).status_code == 403
    assert (await client.post("/auth/logout", headers={"Origin": "null"})).status_code == 403
    assert (await client.post("/auth/logout", headers={"Origin": ""})).status_code == 403
    assert (
        await client.options(
            "/auth/register", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "DELETE"}
        )
    ).status_code == 400
    assert (
        await client.options(
            "/auth/register",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "X-Unknown",
            },
        )
    ).status_code == 400


async def test_configured_lifetime_used_by_jwt_and_cookie(client, monkeypatch):
    monkeypatch.setattr(settings, "JWT_ACCESS_TOKEN_LIFETIME", "0,0,2,3")
    monkeypatch.setattr(settings, "JWT_REFRESH_TOKEN_LIFETIME", "1,2,3,4")
    await client.post("/auth/register", json=USER)
    response = await client.post("/auth/login", json={"email": USER["email"], "password": USER["password"]})
    access = jwt.decode(client.cookies["access_token"], settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    refresh = jwt.decode(
        client.cookies["refresh_token"], settings.JWT_REFRESH_TOKEN_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )
    assert access["exp"] - access["iat"] == 123
    assert refresh["exp"] - refresh["iat"] == 93784
    cookies = response.headers.get_list("set-cookie")
    assert any("Max-Age=123" in cookie for cookie in cookies)
    assert any("Max-Age=93784" in cookie for cookie in cookies)
    from sqlalchemy import select

    from app.modules.user.models import RefreshToken
    from app.security.jwt_service import JWTService

    async with client.test_sessions() as session:
        record = await session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == JWTService.digest(client.cookies["refresh_token"]))
        )
        jwt_expiry = datetime.fromtimestamp(refresh["exp"], timezone.utc).replace(tzinfo=None)
        assert abs((record.expires_at - jwt_expiry).total_seconds()) < 2


async def test_swagger_uses_relative_schema_and_documents_authorization(client):
    from urllib.parse import urljoin

    response = await client.get("/docs")
    assert response.status_code == 200
    assert "url: 'openapi.json'" in response.text
    assert urljoin("http://127.0.0.1:8000/docs", "openapi.json") == "http://127.0.0.1:8000/openapi.json"
    assert urljoin("http://localhost:3000/api/docs", "openapi.json") == "http://localhost:3000/api/openapi.json"
    spec = (await client.get("/openapi.json")).json()
    assert spec["servers"] == [{"url": "."}]
    assert spec["components"]["securitySchemes"]["AccessToken"]["scheme"] == "bearer"
    assert {"AccessToken": []} in spec["paths"]["/auth/me"]["get"]["security"]


async def test_registration_password_complexity(client):
    invalid_passwords = [
        "password1!",  # Missing uppercase.
        "PASSWORD1!",  # Missing lowercase.
        "Password!!",  # Missing digit.
        "Password12",  # Missing special character.
        "Aa1!",  # Too short.
    ]
    for password in invalid_passwords:
        response = await client.post("/auth/register", json={**USER, "password": password})
        assert response.status_code == 422
        assert response.json()["errors"][0]["field"] == "password"
        assert password not in response.text
    assert (await client.post("/auth/register", json={**USER, "password": "ValidPass1_"})).status_code == 201


async def test_existing_users_can_login_with_old_password(client):
    from app.modules.user.models import User
    from app.security.password_helpers import password_helper

    old_password = "old-password"
    async with client.test_sessions() as session:
        session.add(User(name="Existing", email="existing@example.com", password=password_helper.hash(old_password)))
        await session.commit()
    response = await client.post("/auth/login", json={"email": "existing@example.com", "password": old_password})
    assert response.status_code == 200
