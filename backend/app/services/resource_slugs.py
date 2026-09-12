"""Helpers for allocating unique resource slugs."""

from collections.abc import Collection

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resource import Resource
from app.utils.seo import generate_slug


async def generate_unique_slug(
    db: AsyncSession,
    title: str,
    *,
    exclude_resource_id: int | None = None,
    reserved_slugs: Collection[str] | None = None,
) -> str:
    """Return a stable numeric slug unique in both the database and current batch."""
    base_slug = generate_slug(title) or "resource"
    reserved = reserved_slugs if reserved_slugs is not None else ()
    candidate = base_slug
    suffix = 2

    while True:
        if candidate not in reserved:
            query = select(Resource.id).where(Resource.slug == candidate)
            if exclude_resource_id is not None:
                query = query.where(Resource.id != exclude_resource_id)
            result = await db.execute(query)
            if result.scalar_one_or_none() is None:
                return candidate

        candidate = f"{base_slug}-{suffix}"
        suffix += 1
