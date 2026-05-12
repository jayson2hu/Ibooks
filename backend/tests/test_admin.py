"""
Tests for core admin APIs.
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.database import AsyncSessionLocal
from app.main import app
from app.models.audit_log import AuditAction, AuditLog
from app.models.category import Category
from app.models.resource import Resource
from app.models.user import User, UserRole, UserStatus
from app.services.wallet import get_or_create_wallet
from app.utils.security import create_access_token, get_password_hash


async def create_user(email: str, role: UserRole = UserRole.USER) -> tuple[User, str]:
    """Create a user and return it with an auth token."""
    async with AsyncSessionLocal() as session:
        user = User(
            email=email,
            username=email.split("@")[0],
            role=role,
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
        return user, token


async def seed_stats_data() -> None:
    """Create resources and categories used by stats tests."""
    async with AsyncSessionLocal() as session:
        category = Category(name="Stats Category", slug="stats-category")
        published = Resource(
            title="Published Resource",
            slug="published-resource",
            tags=[],
            price=Decimal("0.00"),
            coin_price=0,
            is_free=True,
            is_published=True,
            view_count=7,
            download_count=3,
            backup_links=[],
            preview_images=[],
        )
        draft = Resource(
            title="Draft Resource",
            slug="draft-resource",
            tags=[],
            price=Decimal("0.00"),
            coin_price=0,
            is_free=True,
            is_published=False,
            view_count=5,
            download_count=2,
            backup_links=[],
            preview_images=[],
        )
        session.add_all([category, published, draft])
        await session.commit()


async def create_audit_log(user: User) -> AuditLog:
    """Create an audit log entry."""
    async with AsyncSessionLocal() as session:
        log = AuditLog(
            action=AuditAction.LOGIN,
            user_id=user.id,
            user_email=user.email,
            ip_address="127.0.0.1",
            request_method="POST",
            request_path="/api/v1/auth/login",
            success=True,
            details={"source": "test"},
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)
        return log


@pytest.mark.asyncio
async def test_non_admin_cannot_access_admin_endpoints():
    """Admin endpoints reject regular users."""
    _, token = await create_user("admin-regular@example.com")

    async with AsyncClient(app=app, base_url="http://test") as client:
        stats_response = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        users_response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        audit_response = await client.get(
            "/api/v1/admin/audit-logs",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert stats_response.status_code == 403
    assert users_response.status_code == 403
    assert audit_response.status_code == 403


@pytest.mark.asyncio
async def test_admin_stats_returns_platform_counts():
    """Admin stats returns user, resource, category, and aggregate counters."""
    _, admin_token = await create_user("stats-admin@example.com", UserRole.ADMIN)
    await create_user("stats-user@example.com")
    await seed_stats_data()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["users"] == 2
    assert data["resources"] == 2
    assert data["published_resources"] == 1
    assert data["categories"] == 1
    assert data["total_views"] == 12
    assert data["total_downloads"] == 5


@pytest.mark.asyncio
async def test_admin_can_list_and_update_users():
    """Admin user management can list and update user role/status."""
    _, admin_token = await create_user("users-admin@example.com", UserRole.ADMIN)
    user, _ = await create_user("managed-user@example.com")

    async with AsyncClient(app=app, base_url="http://test") as client:
        list_response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        update_response = await client.patch(
            f"/api/v1/admin/users/{user.id}",
            json={"role": "moderator", "status": "suspended"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert list_response.status_code == 200
    assert {item["email"] for item in list_response.json()} == {
        "users-admin@example.com",
        "managed-user@example.com",
    }
    assert update_response.status_code == 200
    assert update_response.json()["role"] == "moderator"
    assert update_response.json()["status"] == "suspended"

    async with AsyncSessionLocal() as session:
        refreshed = await session.get(User, user.id)
    assert refreshed.role == UserRole.MODERATOR
    assert refreshed.status == UserStatus.SUSPENDED


@pytest.mark.asyncio
async def test_admin_update_missing_user_returns_404():
    """Updating a missing user returns 404."""
    _, admin_token = await create_user("missing-admin@example.com", UserRole.ADMIN)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.patch(
            "/api/v1/admin/users/99999",
            json={"status": "suspended"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_admin_audit_logs_support_filters_and_pagination():
    """Audit logs can be filtered by action and user."""
    _, admin_token = await create_user("audit-admin@example.com", UserRole.ADMIN)
    user, _ = await create_user("audit-user@example.com")
    log = await create_audit_log(user)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/admin/audit-logs",
            params={"action": "login", "user_id": user.id, "page": 1, "page_size": 10},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["pages"] == 1
    assert data["items"][0]["id"] == log.id
    assert data["items"][0]["action"] == "login"
    assert data["items"][0]["user_email"] == "audit-user@example.com"
