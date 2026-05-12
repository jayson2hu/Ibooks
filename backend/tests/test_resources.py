"""
Tests for resource APIs.
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.database import AsyncSessionLocal
from app.main import app
from app.models.category import Category
from app.models.resource import Resource
from app.models.user import User, UserRole
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


async def create_category(name: str = "Books") -> Category:
    """Create a category for resource filtering tests."""
    async with AsyncSessionLocal() as session:
        category = Category(name=name, slug=name.lower())
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category


async def create_resource(
    slug: str,
    title: str | None = None,
    *,
    category_id: int | None = None,
    is_published: bool = True,
    is_free: bool = False,
    is_featured: bool = False,
    resource_type: str = "ebook",
) -> Resource:
    """Create a resource directly in the database."""
    async with AsyncSessionLocal() as session:
        resource = Resource(
            title=title or f"Resource {slug}",
            slug=slug,
            description=f"Description for {slug}",
            excerpt=f"Excerpt for {slug}",
            category_id=category_id,
            tags=["test"],
            price=Decimal("0.00") if is_free else Decimal("19.90"),
            coin_price=0 if is_free else 20,
            is_free=is_free,
            is_featured=is_featured,
            is_published=is_published,
            resource_type=resource_type,
            cloud_link=f"https://pan.example.com/{slug}",
            backup_links=[],
            access_code="abcd",
            preview_images=[],
        )
        session.add(resource)
        await session.commit()
        await session.refresh(resource)
        return resource


@pytest.mark.asyncio
async def test_list_resources_paginates_and_filters_published_resources():
    """Resource listing supports pagination and public filters."""
    category = await create_category("Programming")
    first = await create_resource(
        "python-guide",
        "Python Guide",
        category_id=category.id,
        is_free=True,
        is_featured=True,
        resource_type="ebook",
    )
    await create_resource("draft-guide", "Draft Guide", is_published=False)
    await create_resource("video-course", "Video Course", resource_type="course")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/resources",
            params={
                "page": 1,
                "page_size": 10,
                "category_id": category.id,
                "is_free": True,
                "is_featured": True,
                "resource_type": "ebook",
                "search": "Python",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["pages"] == 1
    assert data["items"][0]["id"] == first.id
    assert data["items"][0]["slug"] == "python-guide"


@pytest.mark.asyncio
async def test_resource_detail_increments_view_count_and_hides_delivery_fields():
    """Public resource detail increments views but does not expose cloud links."""
    resource = await create_resource("detail-resource", is_free=True)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/resources/detail-resource")

    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "detail-resource"
    assert "cloud_link" not in data
    assert "access_code" not in data

    async with AsyncSessionLocal() as session:
        refreshed = await session.get(Resource, resource.id)
    assert refreshed.view_count == 1


@pytest.mark.asyncio
async def test_regular_user_cannot_create_resource():
    """Resource creation is admin-only."""
    _, token = await create_user("resource-user@example.com")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/resources",
            json={
                "title": "User Created Resource",
                "description": "Should fail",
                "is_free": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_create_update_and_delete_resource():
    """Admins can create, update, and delete resources."""
    _, token = await create_user("resource-admin@example.com", UserRole.ADMIN)

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/resources",
            json={
                "title": "Admin Resource",
                "description": "Created by admin",
                "is_free": True,
                "cloud_link": "https://pan.example.com/admin-resource",
                "access_code": "code",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        resource_id = create_response.json()["id"]
        update_response = await client.patch(
            f"/api/v1/resources/{resource_id}",
            json={"title": "Updated Admin Resource", "is_featured": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        delete_response = await client.delete(
            f"/api/v1/resources/{resource_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        get_response = await client.get("/api/v1/resources/updated-admin-resource")

    assert create_response.status_code == 201
    assert create_response.json()["slug"] == "admin-resource"
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "Updated Admin Resource"
    assert update_response.json()["slug"] == "updated-admin-resource"
    assert update_response.json()["is_featured"] is True
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Resource deleted successfully"
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_create_resource_slug_conflict_gets_unique_suffix():
    """Create endpoint avoids duplicate slugs by appending a timestamp suffix."""
    _, token = await create_user("resource-slug-admin@example.com", UserRole.ADMIN)
    existing = await create_resource("duplicate-title", "Duplicate Title")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/resources",
            json={
                "title": "Duplicate Title",
                "description": "Conflict title",
                "is_free": True,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["slug"].startswith("duplicate-title-")
    assert data["slug"] != existing.slug
