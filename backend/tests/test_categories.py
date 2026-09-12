"""
Tests for category APIs.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.database import AsyncSessionLocal
from app.main import app
from app.models.category import Category
from app.models.resource import Resource
from app.models.user import User, UserRole
from app.services.wallet import get_or_create_wallet
from app.utils.security import create_access_token, get_password_hash


CATEGORY_NOT_EMPTY_DETAIL = (
    "Category cannot be deleted while it has child categories or resources"
)


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


async def create_resource(
    category_id: int,
    *,
    slug: str,
    is_published: bool = True,
) -> Resource:
    """Create a resource assigned to a category."""
    async with AsyncSessionLocal() as session:
        resource = Resource(
            title=f"Resource {slug}",
            slug=slug,
            category_id=category_id,
            price=0,
            is_free=True,
            is_published=is_published,
        )
        session.add(resource)
        await session.commit()
        await session.refresh(resource)
        return resource


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
async def test_category_resource_count_is_computed_from_published_resources():
    """Category counts stay accurate without leaking or counting drafts."""
    category = await create_category("Counted", "counted")
    await create_resource(category.id, slug="counted-one")
    await create_resource(category.id, slug="counted-two")
    await create_resource(
        category.id,
        slug="counted-draft",
        is_published=False,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        list_response = await client.get("/api/v1/categories")
        detail_response = await client.get("/api/v1/categories/counted")
        tree_response = await client.get("/api/v1/categories/tree")

    assert list_response.status_code == 200
    assert list_response.json()[0]["resource_count"] == 2
    assert detail_response.status_code == 200
    assert detail_response.json()["resource_count"] == 2
    assert tree_response.status_code == 200
    assert tree_response.json()[0]["resource_count"] == 2


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
async def test_admin_can_create_update_and_delete_empty_category():
    """Admins can delete a category only after it is empty."""
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

    async with AsyncSessionLocal() as session:
        assert await session.get(Category, category_id) is None


@pytest.mark.asyncio
async def test_delete_category_with_child_returns_409_and_preserves_both():
    """A parent category cannot recursively delete its child category."""
    _, token = await create_user("category-child-admin@example.com", UserRole.ADMIN)
    parent = await create_category("Parent to keep", "parent-to-keep")
    child = await create_category(
        "Child to keep",
        "child-to-keep",
        parent_id=parent.id,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/categories/{parent.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 409
    assert response.json()["detail"] == CATEGORY_NOT_EMPTY_DETAIL
    async with AsyncSessionLocal() as session:
        stored_parent = await session.get(Category, parent.id)
        stored_child = await session.get(Category, child.id)
        assert stored_parent is not None
        assert stored_child is not None
        assert stored_child.parent_id == parent.id


@pytest.mark.asyncio
async def test_delete_category_with_resource_returns_409_and_preserves_both():
    """Deleting a category cannot delete or detach an assigned resource."""
    _, token = await create_user(
        "category-resource-admin@example.com",
        UserRole.ADMIN,
    )
    category = await create_category("Resource parent", "resource-parent")
    resource = await create_resource(category.id, slug="resource-to-keep")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/categories/{category.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 409
    assert response.json()["detail"] == CATEGORY_NOT_EMPTY_DETAIL
    async with AsyncSessionLocal() as session:
        stored_category = await session.get(Category, category.id)
        stored_resource = await session.get(Resource, resource.id)
        assert stored_category is not None
        assert stored_resource is not None
        assert stored_resource.category_id == category.id


def test_category_relationships_never_cascade_deletes():
    """ORM relationships must leave deletion decisions to RESTRICT FKs."""
    category_mapper = inspect(Category)

    for relationship_name in ("children", "resources"):
        relationship = category_mapper.relationships[relationship_name]
        assert "delete" not in relationship.cascade
        assert "delete-orphan" not in relationship.cascade
        assert relationship.passive_deletes == "all"

    parent_fk = next(iter(Category.__table__.c.parent_id.foreign_keys))
    resource_fk = next(iter(Resource.__table__.c.category_id.foreign_keys))
    assert parent_fk.ondelete == "RESTRICT"
    assert resource_fk.ondelete == "RESTRICT"


@pytest.mark.asyncio
async def test_sqlite_restrict_foreign_keys_block_direct_parent_delete():
    """SQLite connections enforce RESTRICT without per-session setup."""
    parent = await create_category("Direct parent", "direct-parent")
    child = await create_category(
        "Direct child",
        "direct-child",
        parent_id=parent.id,
    )
    resource = await create_resource(parent.id, slug="direct-resource")

    async with AsyncSessionLocal() as session:
        foreign_keys_enabled = await session.scalar(text("PRAGMA foreign_keys"))
        assert foreign_keys_enabled == 1

        category_fks = (
            await session.execute(text("PRAGMA foreign_key_list(categories)"))
        ).mappings().all()
        resource_fks = (
            await session.execute(text("PRAGMA foreign_key_list(resources)"))
        ).mappings().all()
        assert any(
            row["from"] == "parent_id" and row["on_delete"] == "RESTRICT"
            for row in category_fks
        )
        assert any(
            row["from"] == "category_id" and row["on_delete"] == "RESTRICT"
            for row in resource_fks
        )

        stored_parent = await session.get(Category, parent.id)
        await session.delete(stored_parent)
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()

    async with AsyncSessionLocal() as session:
        assert await session.get(Category, parent.id) is not None
        assert await session.get(Category, child.id) is not None
        stored_resource = await session.get(Resource, resource.id)
        assert stored_resource is not None
        assert stored_resource.category_id == parent.id
