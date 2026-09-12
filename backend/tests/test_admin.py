"""
Tests for core admin APIs.
"""
from datetime import datetime
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


async def seed_admin_resource_list_data() -> tuple[Category, Category, Resource]:
    """Create published and draft resources across two categories."""
    async with AsyncSessionLocal() as session:
        books = Category(name="Books", slug="admin-books")
        courses = Category(name="Courses", slug="admin-courses")
        session.add_all([books, courses])
        await session.flush()

        resources = [
            Resource(
                title="Python Handbook",
                slug="admin-python-handbook",
                description="Published Python reference",
                category_id=books.id,
                is_free=True,
                is_published=True,
            ),
            Resource(
                title="Python Draft Notes",
                slug="admin-python-draft-notes",
                description="Unpublished Python notes",
                category_id=books.id,
                is_free=True,
                is_published=False,
            ),
            Resource(
                title="Video Course Draft",
                slug="admin-video-course-draft",
                category_id=courses.id,
                is_free=True,
                is_published=False,
            ),
            Resource(
                title="Rust Handbook",
                slug="admin-rust-handbook",
                category_id=courses.id,
                is_free=True,
                is_published=True,
            ),
        ]
        session.add_all(resources)
        await session.commit()
        return books, courses, resources[1]


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
async def test_admin_resource_list_requires_staff_permissions():
    """The administrative resource inventory rejects anonymous and regular users."""
    _, token = await create_user("resource-list-regular@example.com")

    async with AsyncClient(app=app, base_url="http://test") as client:
        anonymous_response = await client.get("/api/v1/admin/resources")
        regular_response = await client.get(
            "/api/v1/admin/resources",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert anonymous_response.status_code == 401
    assert regular_response.status_code == 403


@pytest.mark.asyncio
async def test_admin_resource_list_includes_drafts_without_exposing_them_publicly():
    """Staff inventory includes drafts while the public endpoint remains published-only."""
    _, token = await create_user("resource-list-admin@example.com", UserRole.ADMIN)
    _, _, draft = await seed_admin_resource_list_data()

    async with AsyncClient(app=app, base_url="http://test") as client:
        admin_response = await client.get(
            "/api/v1/admin/resources",
            headers={"Authorization": f"Bearer {token}"},
        )
        draft_detail_response = await client.get(
            f"/api/v1/admin/resources/{draft.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        public_response = await client.get("/api/v1/resources")

    assert admin_response.status_code == 200
    admin_data = admin_response.json()
    assert admin_data["total"] == 4
    assert admin_data["page"] == 1
    assert admin_data["page_size"] == 20
    assert admin_data["pages"] == 1
    assert {item["is_published"] for item in admin_data["items"]} == {True, False}
    assert draft_detail_response.status_code == 200
    assert draft_detail_response.json()["is_published"] is False

    assert public_response.status_code == 200
    public_data = public_response.json()
    assert public_data["total"] == 2
    assert all(item["is_published"] for item in public_data["items"])


@pytest.mark.asyncio
async def test_moderator_resource_list_supports_filters_and_pagination():
    """Moderators can combine draft, category, search, and page filters."""
    _, token = await create_user(
        "resource-list-moderator@example.com",
        UserRole.MODERATOR,
    )
    books, _, _ = await seed_admin_resource_list_data()

    async with AsyncClient(app=app, base_url="http://test") as client:
        filtered_response = await client.get(
            "/api/v1/admin/resources",
            params={
                "search": "Python",
                "category_id": books.id,
                "is_published": False,
                "page": 1,
                "page_size": 10,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        page_response = await client.get(
            "/api/v1/admin/resources",
            params={"page": 2, "page_size": 2},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert filtered_response.status_code == 200
    filtered_data = filtered_response.json()
    assert filtered_data["total"] == 1
    assert filtered_data["pages"] == 1
    assert [item["title"] for item in filtered_data["items"]] == [
        "Python Draft Notes"
    ]

    assert page_response.status_code == 200
    page_data = page_response.json()
    assert page_data["total"] == 4
    assert page_data["page"] == 2
    assert page_data["page_size"] == 2
    assert page_data["pages"] == 2
    assert len(page_data["items"]) == 2


@pytest.mark.asyncio
async def test_moderator_can_manage_content_but_not_accounts_or_wallets():
    """Moderators get content tooling without administrator-only privileges."""
    _, token = await create_user("content-moderator@example.com", UserRole.MODERATOR)

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/resources",
            json={
                "title": "Moderator Resource",
                "description": "Created by a content moderator",
                "is_free": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        stats_response = await client.get(
            "/api/v1/admin/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        users_response = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        wallets_response = await client.get(
            "/api/v1/admin/wallets",
            headers={"Authorization": f"Bearer {token}"},
        )
        import_response = await client.get(
            "/api/v1/bulk-import/template",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert create_response.status_code == 201
    assert stats_response.status_code == 200
    assert users_response.status_code == 403
    assert wallets_response.status_code == 403
    assert import_response.status_code == 403


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
    list_data = list_response.json()
    assert {item["email"] for item in list_data["items"]} == {
        "users-admin@example.com",
        "managed-user@example.com",
    }
    assert list_data["total"] == 2
    assert list_data["page"] == 1
    assert list_data["page_size"] == 20
    assert list_data["pages"] == 1
    assert update_response.status_code == 200
    assert update_response.json()["role"] == "moderator"
    assert update_response.json()["status"] == "suspended"

    async with AsyncSessionLocal() as session:
        refreshed = await session.get(User, user.id)
    assert refreshed.role == UserRole.MODERATOR
    assert refreshed.status == UserStatus.SUSPENDED


@pytest.mark.asyncio
async def test_admin_user_pagination_is_stable_when_created_at_values_tie():
    """The ID tie-breaker prevents duplicate or skipped users across pages."""
    admin, admin_token = await create_user("pagination-admin@example.com", UserRole.ADMIN)
    users_and_tokens = [
        await create_user(f"pagination-user-{index}@example.com")
        for index in range(4)
    ]
    all_user_ids = [admin.id, *(user.id for user, _ in users_and_tokens)]

    async with AsyncSessionLocal() as session:
        for user_id in all_user_ids:
            stored_user = await session.get(User, user_id)
            assert stored_user is not None
            stored_user.created_at = datetime(2026, 1, 1)
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        responses = [
            await client.get(
                "/api/v1/admin/users",
                params={"page": page, "page_size": 2},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            for page in range(1, 4)
        ]

    assert all(response.status_code == 200 for response in responses)
    pages = [response.json() for response in responses]
    listed_ids = [item["id"] for page in pages for item in page["items"]]
    assert listed_ids == sorted(all_user_ids, reverse=True)
    assert len(listed_ids) == len(set(listed_ids)) == 5
    assert [(page["page"], page["pages"], page["total"]) for page in pages] == [
        (1, 3, 5),
        (2, 3, 5),
        (3, 3, 5),
    ]


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


@pytest.mark.asyncio
async def test_admin_audit_logs_reject_invalid_action_before_querying_database():
    """Invalid enum filters return a stable validation response."""
    _, admin_token = await create_user("invalid-audit-filter-admin@example.com", UserRole.ADMIN)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/admin/audit-logs",
            params={"action": "not-a-real-action"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert response.status_code == 422
