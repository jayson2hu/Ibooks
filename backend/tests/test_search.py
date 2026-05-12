"""
Tests for search APIs.
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient

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
