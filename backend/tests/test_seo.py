"""
Tests for SEO generation APIs.
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient

from app.database import AsyncSessionLocal
from app.main import app
from app.models.resource import Resource
from app.models.user import User, UserRole
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
        await session.commit()
        await session.refresh(user)

        token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )
        return user, token


async def create_resource(slug: str, *, is_published: bool) -> Resource:
    """Create a resource for static page generation tests."""
    async with AsyncSessionLocal() as session:
        resource = Resource(
            title=f"SEO {slug}",
            slug=slug,
            description="SEO description",
            excerpt="SEO excerpt",
            tags=[],
            price=Decimal("9.90"),
            coin_price=10,
            is_free=False,
            is_published=is_published,
            backup_links=[],
            preview_images=[],
        )
        session.add(resource)
        await session.commit()
        await session.refresh(resource)
        return resource


@pytest.mark.asyncio
async def test_regular_user_cannot_generate_seo_files():
    """SEO generation endpoints are admin-only."""
    _, token = await create_user("seo-user@example.com")

    async with AsyncClient(app=app, base_url="http://test") as client:
        sitemap_response = await client.post(
            "/api/v1/seo/generate-sitemap",
            headers={"Authorization": f"Bearer {token}"},
        )
        robots_response = await client.post(
            "/api/v1/seo/generate-robots",
            headers={"Authorization": f"Bearer {token}"},
        )
        static_response = await client.post(
            "/api/v1/seo/generate-static-pages",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert sitemap_response.status_code == 403
    assert robots_response.status_code == 403
    assert static_response.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_start_sitemap_rss_and_all_generation(monkeypatch):
    """Admin SEO endpoints schedule sitemap/rss generation tasks."""
    _, token = await create_user("seo-admin@example.com", UserRole.ADMIN)
    calls: list[str] = []

    async def fake_save_sitemap(db):
        calls.append("sitemap")

    async def fake_save_rss_feed(db):
        calls.append("rss")

    def fake_save_robots_txt():
        calls.append("robots")

    monkeypatch.setattr("app.api.v1.seo.save_sitemap", fake_save_sitemap)
    monkeypatch.setattr("app.api.v1.seo.save_rss_feed", fake_save_rss_feed)
    monkeypatch.setattr("app.api.v1.seo.save_robots_txt", fake_save_robots_txt)

    async with AsyncClient(app=app, base_url="http://test") as client:
        sitemap_response = await client.post(
            "/api/v1/seo/generate-sitemap",
            headers={"Authorization": f"Bearer {token}"},
        )
        rss_response = await client.post(
            "/api/v1/seo/generate-rss",
            headers={"Authorization": f"Bearer {token}"},
        )
        all_response = await client.post(
            "/api/v1/seo/generate-all",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert sitemap_response.status_code == 200
    assert sitemap_response.json()["message"] == "Sitemap generation started"
    assert rss_response.status_code == 200
    assert rss_response.json()["message"] == "RSS feed generation started"
    assert all_response.status_code == 200
    assert all_response.json()["message"] == "SEO file generation started"
    assert calls == ["sitemap", "rss", "sitemap", "rss", "robots"]


@pytest.mark.asyncio
async def test_admin_generate_robots_writes_robots_file(tmp_path, monkeypatch):
    """Admin can generate robots.txt in the configured static directory."""
    monkeypatch.setattr("app.static_generator.robots.settings.STATIC_PAGES_DIR", str(tmp_path))
    monkeypatch.setattr("app.static_generator.robots.settings.SITE_URL", "https://ibooks.test")
    _, token = await create_user("seo-robots-admin@example.com", UserRole.ADMIN)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/seo/generate-robots",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "robots.txt generated successfully"
    robots = (tmp_path / "robots.txt").read_text()
    assert "Sitemap: https://ibooks.test/sitemap.xml" in robots
    assert "Disallow: /api/" in robots


@pytest.mark.asyncio
async def test_admin_generate_static_pages_for_published_resources(monkeypatch):
    """Static page generation exports only published resources."""
    _, token = await create_user("seo-static-admin@example.com", UserRole.ADMIN)
    published = await create_resource("published-static", is_published=True)
    await create_resource("draft-static", is_published=False)
    generated: list[dict] = []

    def fake_save_resource_html(resource_data):
        generated.append(resource_data)

    monkeypatch.setattr("app.api.v1.seo.save_resource_html", fake_save_resource_html)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/seo/generate-static-pages",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Static page generation started"
    assert generated == [
        {
            "title": published.title,
            "slug": "published-static",
            "description": "SEO description",
            "excerpt": "SEO excerpt",
            "meta_title": None,
            "meta_description": None,
            "meta_keywords": None,
            "cover_image_url": None,
            "price": 9.9,
        }
    ]
