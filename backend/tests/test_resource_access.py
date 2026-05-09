"""
Tests for resource cloud-link access.
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.database import AsyncSessionLocal
from app.main import app
from app.models.resource import Resource
from app.models.user import User
from app.utils.security import create_access_token, get_password_hash


async def create_resource(
    *,
    slug: str,
    is_free: bool,
    cloud_link: str = "https://pan.example.com/free-resource",
    access_code: str = "abcd",
) -> Resource:
    """Create a published resource for access tests."""
    async with AsyncSessionLocal() as session:
        resource = Resource(
            title=f"Resource {slug}",
            slug=slug,
            description="Test resource",
            tags=[],
            price=Decimal("0.00") if is_free else Decimal("99.00"),
            is_free=is_free,
            cloud_link=cloud_link,
            backup_links=["https://pan.example.com/backup"],
            access_code=access_code,
            preview_images=[],
            is_published=True,
        )
        session.add(resource)
        await session.commit()
        await session.refresh(resource)
        return resource


async def create_user_token() -> str:
    """Create an active user and return a JWT token."""
    async with AsyncSessionLocal() as session:
        user = User(
            email="buyer@example.com",
            username="buyer",
            password_hash=get_password_hash("Test1234"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        return create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )


@pytest.mark.asyncio
async def test_free_resource_access_returns_cloud_link():
    """Free resources expose cloud-link delivery data."""
    await create_resource(slug="free-resource", is_free=True)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/resources/free-resource/access")

    assert response.status_code == 200
    data = response.json()
    assert data["cloud_link"] == "https://pan.example.com/free-resource"
    assert data["backup_links"] == ["https://pan.example.com/backup"]
    assert data["access_code"] == "abcd"


@pytest.mark.asyncio
async def test_resource_detail_does_not_expose_delivery_fields():
    """Public resource details do not expose cloud-link delivery data."""
    await create_resource(slug="public-detail", is_free=True)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/resources/public-detail")

    assert response.status_code == 200
    data = response.json()
    assert "cloud_link" not in data
    assert "backup_links" not in data
    assert "access_code" not in data


@pytest.mark.asyncio
async def test_paid_resource_access_requires_login():
    """Anonymous users cannot access paid resource delivery data."""
    await create_resource(slug="paid-resource", is_free=False)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/resources/paid-resource/access")

    assert response.status_code == 401
    assert response.json()["detail"] == "请先登录"


@pytest.mark.asyncio
async def test_paid_resource_access_requires_purchase_for_logged_in_user():
    """Logged-in users still need an order before paid delivery is enabled."""
    await create_resource(slug="paid-resource-login", is_free=False)
    token = await create_user_token()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/resources/paid-resource-login/access",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 402
    assert response.json()["detail"] == "请先购买该资源"
