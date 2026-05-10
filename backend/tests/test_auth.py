"""
Basic tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.main import app
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.api.v1 import auth
from app.utils.security import get_password_hash


@pytest.mark.asyncio
async def test_register_user():
    """Test user registration."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "testuser",
                "password": "Test1234",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"


@pytest.mark.asyncio
async def test_login():
    """Test user login."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First register
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "username": "loginuser",
                "password": "Test1234"
            }
        )
        
        # Then login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "Test1234"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_admin_login_rejects_regular_user():
    """Regular users cannot use the admin login endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "regular@example.com",
                "username": "regularuser",
                "password": "Test1234"
            }
        )

        response = await client.post(
            "/api/v1/auth/admin/login",
            json={
                "email": "regular@example.com",
                "password": "Test1234"
            }
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "无管理员权限"


@pytest.mark.asyncio
async def test_admin_login_accepts_admin_user():
    """Admin users can use the admin login endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin@example.com",
                "username": "adminuser",
                "password": "Test1234"
            }
        )

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == "admin@example.com"))
            user = result.scalar_one()
            user.role = UserRole.ADMIN
            await session.commit()

        response = await client.post(
            "/api/v1/auth/admin/login",
            json={
                "email": "admin@example.com",
                "password": "Test1234"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_admin_login_accepts_moderator_user():
    """Moderator users can use the admin login endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "moderator@example.com",
                "username": "moderatoruser",
                "password": "Test1234"
            }
        )

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == "moderator@example.com"))
            user = result.scalar_one()
            user.role = UserRole.MODERATOR
            await session.commit()

        response = await client.post(
            "/api/v1/auth/admin/login",
            json={
                "email": "moderator@example.com",
                "password": "Test1234"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "moderator"


@pytest.mark.asyncio
async def test_admin_login_rejects_invalid_password():
    """Admin login rejects invalid passwords."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrong-password@example.com",
                "username": "wrongpassword",
                "password": "Test1234"
            }
        )

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == "wrong-password@example.com"))
            user = result.scalar_one()
            user.role = UserRole.ADMIN
            await session.commit()

        response = await client.post(
            "/api/v1/auth/admin/login",
            json={
                "email": "wrong-password@example.com",
                "password": "Wrong1234"
            }
        )

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_rate_limit_returns_429(monkeypatch):
    """Registration is rate-limited per client IP."""
    calls = 0

    async def fake_check_rate_limit(key: str, max_calls: int, window_seconds: int) -> bool:
        nonlocal calls
        calls += 1
        assert key == "rate_limit:auth:register:127.0.0.1"
        assert max_calls == 3
        assert window_seconds == 60
        return calls <= 3

    monkeypatch.setattr(auth, "check_rate_limit", fake_check_rate_limit)

    async with AsyncClient(app=app, base_url="http://test") as client:
        for index in range(3):
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"limited-register-{index}@example.com",
                    "username": f"limitedregister{index}",
                    "password": "Test1234",
                },
            )
            assert response.status_code == 201

        limited_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "limited-register-4@example.com",
                "username": "limitedregister4",
                "password": "Test1234",
            },
        )

    assert limited_response.status_code == 429
    assert limited_response.json()["detail"] == "请求过于频繁，请稍后再试"


@pytest.mark.asyncio
async def test_login_rate_limit_returns_429(monkeypatch):
    """User login is rate-limited per client IP."""
    calls = 0

    async def fake_check_rate_limit(key: str, max_calls: int, window_seconds: int) -> bool:
        nonlocal calls
        calls += 1
        assert key == "rate_limit:auth:login:127.0.0.1"
        assert max_calls == 10
        assert window_seconds == 60
        return calls <= 10

    monkeypatch.setattr(auth, "check_rate_limit", fake_check_rate_limit)

    async with AsyncSessionLocal() as session:
        session.add(User(
            email="limited-login@example.com",
            username="limitedlogin",
            password_hash=get_password_hash("Test1234"),
        ))
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        for _ in range(10):
            response = await client.post(
                "/api/v1/auth/login",
                json={"email": "limited-login@example.com", "password": "Wrong1234"},
            )
            assert response.status_code == 401

        limited_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "limited-login@example.com", "password": "Wrong1234"},
        )

    assert limited_response.status_code == 429
    assert limited_response.json()["detail"] == "请求过于频繁，请稍后再试"
