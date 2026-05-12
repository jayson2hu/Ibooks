"""
Tests for category APIs.
"""
import pytest
from httpx import AsyncClient

from app.database import AsyncSessionLocal
from app.main import app
from app.models.category import Category
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


async def create_category(
    name: str,
    slug: str,
    *,
    parent_id: int | None = None,
    is_active: bool = True,
    sort_order: int = 0,
) -> Category:
    """Create a category directly in the database."""
    async with AsyncSessionLocal() as session:
        category = Category(
            name=name,
            slug=slug,
            parent_id=parent_id,
            is_active=is_active,
            sort_order=sort_order,
        )
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category


@pytest.mark.asyncio
async def test_list_categories_filters_inactive_by_default():
    """Category list returns active categories unless inactive are requested."""
    active = await create_category("Active", "active")
    inactive = await create_category("Inactive", "inactive", is_active=False)

    async with AsyncClient(app=app, base_url="http://test") as client:
        active_response = await client.get("/api/v1/categories")
        all_response = await client.get("/api/v1/categories?active_only=false")

    assert active_response.status_code == 200
    assert [item["id"] for item in active_response.json()] == [active.id]
    assert all_response.status_code == 200
    assert {item["id"] for item in all_response.json()} == {active.id, inactive.id}


@pytest.mark.asyncio
async def test_category_tree_contains_nested_children():
    """Category tree nests child categories under root categories."""
    parent = await create_category("Parent", "parent")
    child = await create_category("Child", "child", parent_id=parent.id)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/categories/tree")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == parent.id
    assert data[0]["children"][0]["id"] == child.id


@pytest.mark.asyncio
async def test_get_category_by_slug_and_404():
    """Category detail can be fetched by slug."""
    category = await create_category("Lookup", "lookup")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/categories/lookup")
        missing_response = await client.get("/api/v1/categories/missing")

    assert response.status_code == 200
    assert response.json()["id"] == category.id
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_regular_user_cannot_create_category():
    """Category creation is admin-only."""
    _, token = await create_user("category-user@example.com")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/categories",
            json={"name": "User Category"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_create_update_and_delete_category():
    """Admins can create, update, and delete categories."""
    _, token = await create_user("category-admin@example.com", UserRole.ADMIN)

    async with AsyncClient(app=app, base_url="http://test") as client:
        create_response = await client.post(
            "/api/v1/categories",
            json={"name": "Admin Category", "description": "Created"},
            headers={"Authorization": f"Bearer {token}"},
        )
        category_id = create_response.json()["id"]
        update_response = await client.patch(
            f"/api/v1/categories/{category_id}",
            json={"name": "Updated Category", "is_active": False, "sort_order": 5},
            headers={"Authorization": f"Bearer {token}"},
        )
        delete_response = await client.delete(
            f"/api/v1/categories/{category_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert create_response.status_code == 201
    assert create_response.json()["slug"] == "admin-category"
    assert update_response.status_code == 200
    assert update_response.json()["slug"] == "updated-category"
    assert update_response.json()["is_active"] is False
    assert update_response.json()["sort_order"] == 5
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Category deleted successfully"
