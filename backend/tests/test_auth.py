"""
Basic tests for authentication endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.main import app
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.site_settings import SiteSetting
from app import dependencies
from app.api.v1 import auth
from app.services.wallet import get_or_create_wallet
from app.utils.security import create_access_token, decode_access_token
from app.utils.security import get_password_hash


def test_only_canonical_auth_routes_are_registered():
    """Legacy auth modules must not reintroduce duplicate or stale HTTP contracts."""
    route_paths = [route.path for route in app.routes]

    assert route_paths.count("/api/v1/auth/login") == 1
    assert route_paths.count("/api/v1/auth/admin/login") == 1
    assert route_paths.count("/api/v1/auth/register") == 1
    assert "/api/v1/auth/user/login" not in route_paths
    assert "/api/v1/auth/user/register" not in route_paths
    assert "/api/v1/auth/admin/me" not in route_paths


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


@pytest.mark.asyncio
async def test_registration_runtime_setting_disables_registration():
    """Persisted registration setting is enforced at request time."""
    async with AsyncSessionLocal() as session:
        session.add(
            SiteSetting(
                key="user_registration_enabled",
                value="false",
                category="features",
            )
        )
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "closed@example.com",
                "username": "closeduser",
                "password": "Test1234",
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "用户注册已关闭"


@pytest.mark.asyncio
async def test_login_runtime_settings_control_limit_and_session(monkeypatch):
    """Persisted security settings drive limiter and access-token lifetime."""
    observed_max_calls: list[int] = []

    async def capture_limit(key: str, max_calls: int, window_seconds: int) -> bool:
        observed_max_calls.append(max_calls)
        return True

    monkeypatch.setattr(auth, "check_rate_limit", capture_limit)
    async with AsyncSessionLocal() as session:
        session.add_all(
            [
                User(
                    email="runtime-login@example.com",
                    username="runtimelogin",
                    password_hash=get_password_hash("Test1234"),
                ),
                SiteSetting(
                    key="max_login_attempts",
                    value="3",
                    category="security",
                ),
                SiteSetting(
                    key="session_timeout_minutes",
                    value="15",
                    category="security",
                ),
            ]
        )
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "runtime-login@example.com", "password": "Test1234"},
        )

    assert response.status_code == 200
    assert observed_max_calls == [3]
    payload = decode_access_token(response.json()["access_token"])
    assert payload is not None
    assert 895 <= payload["exp"] - payload["iat"] <= 905


@pytest.mark.asyncio
async def test_auth_rate_limit_ignores_untrusted_forwarded_for(monkeypatch):
    """Clients cannot evade the limiter by spoofing proxy headers."""
    observed_keys: list[str] = []

    async def fake_check_rate_limit(
        key: str,
        max_calls: int,
        window_seconds: int,
    ) -> bool:
        observed_keys.append(key)
        return True

    monkeypatch.setattr(auth, "check_rate_limit", fake_check_rate_limit)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            headers={"X-Forwarded-For": "203.0.113.99"},
            json={"email": "missing@example.com", "password": "Wrong1234"},
        )

    assert response.status_code == 401
    assert observed_keys == ["rate_limit:auth:login:127.0.0.1"]


@pytest.mark.asyncio
async def test_auth_rate_limit_backend_failure_returns_503(monkeypatch):
    """Authentication does not silently lose brute-force protection."""

    async def unavailable_rate_limit(
        key: str,
        max_calls: int,
        window_seconds: int,
    ) -> bool:
        raise auth.RedisError("redis unavailable")

    monkeypatch.setattr(auth, "check_rate_limit", unavailable_rate_limit)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "missing@example.com", "password": "Wrong1234"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "认证保护服务暂不可用，请稍后再试"


@pytest.mark.asyncio
async def test_refresh_token_returns_new_access_token():
    """Authenticated users can refresh their access token."""
    async with AsyncSessionLocal() as session:
        user = User(
            email="refresh@example.com",
            username="refreshuser",
            password_hash=get_password_hash("Test1234"),
        )
        session.add(user)
        await session.flush()
        await get_or_create_wallet(session, user.id)
        await session.commit()
        await session.refresh(user)
        token = auth.create_session_refresh_token(user)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]
    assert decode_access_token(data["access_token"])["typ"] == "access"
    assert decode_access_token(data["refresh_token"])["typ"] == "refresh"
    assert data["user"]["email"] == "refresh@example.com"


@pytest.mark.asyncio
async def test_refresh_endpoint_rejects_typed_access_token():
    """New access tokens cannot be used as refresh credentials."""
    async with AsyncSessionLocal() as session:
        user = User(
            email="access-not-refresh@example.com",
            username="accessnotrefresh",
            password_hash=get_password_hash("Test1234"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        token = auth.create_session_access_token(user, 30)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_cannot_authenticate_access_endpoint():
    """Refresh credentials are not bearer access tokens."""
    async with AsyncSessionLocal() as session:
        user = User(
            email="refresh-not-access@example.com",
            username="refreshnotaccess",
            password_hash=get_password_hash("Test1234"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        token = auth.create_session_refresh_token(user)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_is_single_use(monkeypatch):
    """Refresh rotation consumes a token atomically."""
    consumed: set[str] = set()

    async def consume_once(token: str, ttl_seconds: int) -> bool:
        assert ttl_seconds > 0
        if token in consumed:
            return False
        consumed.add(token)
        return True

    monkeypatch.setattr(auth, "blacklist_token_once", consume_once)
    async with AsyncSessionLocal() as session:
        user = User(
            email="single-refresh@example.com",
            username="singlerefresh",
            password_hash=get_password_hash("Test1234"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        token = auth.create_session_refresh_token(user)

    async with AsyncClient(app=app, base_url="http://test") as client:
        first = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        replay = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert first.status_code == 200
    assert replay.status_code == 401
    assert replay.json()["detail"] == "刷新令牌已使用或已撤销，请重新登录"


@pytest.mark.asyncio
async def test_refresh_token_requires_authentication():
    """Refresh endpoint rejects anonymous requests."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/refresh")

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_logout_blacklists_current_token(monkeypatch):
    """Logout stores the token in a blacklist and rejects later reuse."""
    blacklisted_tokens: set[str] = set()

    async def fake_blacklist_token(token: str, ttl_seconds: int) -> None:
        assert ttl_seconds > 0
        blacklisted_tokens.add(token)

    async def fake_is_token_blacklisted(token: str) -> bool:
        return token in blacklisted_tokens

    monkeypatch.setattr(auth, "blacklist_token", fake_blacklist_token)
    monkeypatch.setattr(dependencies, "is_token_blacklisted", fake_is_token_blacklisted)

    async with AsyncSessionLocal() as session:
        user = User(
            email="logout@example.com",
            username="logoutuser",
            password_hash=get_password_hash("Test1234"),
        )
        session.add(user)
        await session.flush()
        await get_or_create_wallet(session, user.id)
        await session.commit()
        await session.refresh(user)
        token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )

    async with AsyncClient(app=app, base_url="http://test") as client:
        logout_response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "已登出"
    assert me_response.status_code == 401
    assert me_response.json()["detail"] == "Token 已失效，请重新登录"


@pytest.mark.asyncio
async def test_logout_revokes_existing_refresh_tokens(monkeypatch):
    """Logout advances auth version so copied refresh tokens stop working."""

    async def blacklist_succeeds(token: str, ttl_seconds: int) -> None:
        return None

    monkeypatch.setattr(auth, "blacklist_token", blacklist_succeeds)
    async with AsyncSessionLocal() as session:
        user = User(
            email="logout-refresh@example.com",
            username="logoutrefresh",
            password_hash=get_password_hash("Test1234"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        access_token = auth.create_session_access_token(user, 30)
        refresh_token = auth.create_session_refresh_token(user)

    async with AsyncClient(app=app, base_url="http://test") as client:
        logout_response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )

    assert logout_response.status_code == 200
    assert refresh_response.status_code == 401
    assert refresh_response.json()["detail"] == "Token 已失效，请重新登录"


@pytest.mark.asyncio
async def test_blacklist_backend_failure_returns_503(monkeypatch):
    """A blacklist outage cannot make potentially revoked tokens valid again."""

    async def unavailable_blacklist(token: str) -> bool:
        raise auth.RedisError("redis unavailable")

    monkeypatch.setattr(
        dependencies,
        "is_token_blacklisted",
        unavailable_blacklist,
    )

    async with AsyncSessionLocal() as session:
        user = User(
            email="blacklist-outage@example.com",
            username="blacklistoutage",
            password_hash=get_password_hash("Test1234"),
        )
        session.add(user)
        await session.flush()
        await get_or_create_wallet(session, user.id)
        await session.commit()
        await session.refresh(user)
        token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "认证服务暂不可用，请稍后再试"
