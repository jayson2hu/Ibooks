"""
Tests for search APIs.
"""
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from redis.exceptions import RedisError

from app.api.v1 import search as search_module
from app.database import AsyncSessionLocal
from app.main import app
from app.models.resource import Resource


async def create_resource(
    slug: str,
    title: str,
    *,
    description: str = "",
    excerpt: str = "",
    meta_keywords: str = "",
    is_published: bool = True,
    is_featured: bool = False,
    view_count: int = 0,
) -> Resource:
    """Create a searchable resource directly in the database."""
    async with AsyncSessionLocal() as session:
        resource = Resource(
            title=title,
            slug=slug,
            description=description,
            excerpt=excerpt,
            meta_keywords=meta_keywords,
            tags=[],
            price=Decimal("0.00"),
            coin_price=0,
            is_free=True,
            is_published=is_published,
            is_featured=is_featured,
            cloud_link=f"https://pan.example.com/{slug}",
            backup_links=[],
            access_code="abcd",
            preview_images=[],
            view_count=view_count,
        )
        session.add(resource)
        await session.commit()
        await session.refresh(resource)
        return resource


@pytest.mark.asyncio
async def test_search_matches_title_description_excerpt_and_keywords():
    """Search matches supported text fields and excludes unpublished resources."""
    title_match = await create_resource("python-title", "Python Handbook", view_count=5)
    description_match = await create_resource("python-desc", "Backend Notes", description="Learn Python APIs", view_count=10)
    excerpt_match = await create_resource("python-excerpt", "Course Notes", excerpt="Python quick start", view_count=2)
    keyword_match = await create_resource("python-keywords", "Keyword Resource", meta_keywords="python,ebook", view_count=8)
    await create_resource("python-draft", "Python Draft", is_published=False, view_count=100)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/search", params={"q": "Python", "page": 1, "page_size": 10})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4
    assert [item["id"] for item in data["items"]] == [
        description_match.id,
        keyword_match.id,
        title_match.id,
        excerpt_match.id,
    ]


@pytest.mark.asyncio
async def test_search_excludes_unpublished_featured_resources():
    """Featuring a draft must not make it visible to public search."""
    await create_resource(
        "featured-draft",
        "Featured Draft Python",
        is_published=False,
        is_featured=True,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/search", params={"q": "Python"})

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_search_paginates_results():
    """Search results expose consistent pagination metadata."""
    first = await create_resource("search-page-1", "Go Search", view_count=3)
    second = await create_resource("search-page-2", "Go Search Advanced", view_count=2)
    await create_resource("search-page-3", "Go Search Basics", view_count=1)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/search", params={"q": "Go", "page": 1, "page_size": 2})

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["pages"] == 2
    assert [item["id"] for item in data["items"]] == [first.id, second.id]


@pytest.mark.asyncio
async def test_search_filters_by_resource_scope():
    """Homepage search scopes are enforced by the backend."""
    ebook = await create_resource(
        "python-ebook",
        "Python Learning Resource",
        view_count=3,
    )
    video = await create_resource(
        "python-video",
        "Python Learning Resource",
        view_count=2,
    )
    document = await create_resource(
        "python-document",
        "Python Learning Resource",
        view_count=1,
    )

    async with AsyncSessionLocal() as session:
        for resource, resource_type in (
            (ebook, "ebook"),
            (video, "video"),
            (document, "document"),
        ):
            stored = await session.get(Resource, resource.id)
            stored.resource_type = resource_type
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        course_response = await client.get(
            "/api/v1/search",
            params={"q": "Python", "scope": "course"},
        )
        ebook_response = await client.get(
            "/api/v1/search",
            params={"q": "Python", "scope": "ebook"},
        )
        doc_response = await client.get(
            "/api/v1/search",
            params={"q": "Python", "scope": "doc"},
        )

    assert [item["id"] for item in course_response.json()["items"]] == [video.id]
    assert [item["id"] for item in ebook_response.json()["items"]] == [ebook.id]
    assert [item["id"] for item in doc_response.json()["items"]] == [document.id]


@pytest.mark.asyncio
async def test_search_rejects_unknown_scope():
    """Unsupported scopes fail validation instead of silently broadening results."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/search",
            params={"q": "Python", "scope": "unknown"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_no_results_returns_empty_page():
    """No-result search returns an empty page rather than an error."""
    await create_resource("unrelated", "Unrelated Resource")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/search", params={"q": "NotFound"})

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["pages"] == 0


@pytest.mark.asyncio
async def test_search_requires_non_empty_query():
    """Search query must have at least one character."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/search", params={"q": ""})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_search_rejects_excessively_long_query(monkeypatch):
    """Bound query size before it reaches Redis or the database."""
    rate_limit = AsyncMock(return_value=True)
    monkeypatch.setattr(search_module, "check_rate_limit", rate_limit)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/search", params={"q": "x" * 101})

    assert response.status_code == 422
    rate_limit.assert_not_awaited()


@pytest.mark.asyncio
async def test_search_returns_429_when_rate_limit_is_exhausted(monkeypatch):
    """Public search enforces the configured fixed-window request budget."""

    async def deny_search(*args, **kwargs):
        return False

    monkeypatch.setattr(search_module, "check_rate_limit", deny_search)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/search", params={"q": "Python"})

    assert response.status_code == 429
    assert response.json()["detail"] == "搜索请求过于频繁，请稍后再试"


@pytest.mark.asyncio
async def test_search_fails_open_when_rate_limit_backend_is_unavailable(monkeypatch):
    """A Redis outage is observable but does not take public search offline."""
    await create_resource("redis-outage-search", "Redis Outage Search")

    async def unavailable(*args, **kwargs):
        raise RedisError("redis unavailable")

    monkeypatch.setattr(search_module, "check_rate_limit", unavailable)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/search", params={"q": "Redis Outage"})

    assert response.status_code == 200
    assert response.json()["total"] == 1
