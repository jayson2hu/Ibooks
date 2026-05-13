"""
Search endpoint.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List
from math import ceil
from app.database import get_db
from app.schemas.resource import ResourceResponse, ResourceListResponse
from app.models.resource import Resource


router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=ResourceListResponse)
async def search_resources(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search resources by title, description, and tags.

    - **q**: Search query (minimum 1 character)
    - **page**: Page number
    - **page_size**: Items per page
    """
    search_term = f"%{q}%"

    # Build search query
    # Search in both published and featured resources
    query = select(Resource).where(
        or_(
            Resource.is_published == True,
            Resource.is_featured == True
        ),
        or_(
            Resource.title.ilike(search_term),
            Resource.description.ilike(search_term),
            Resource.excerpt.ilike(search_term),
            Resource.meta_keywords.ilike(search_term)
        )
    )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Resource.view_count.desc(), Resource.created_at.desc())

    # Execute query
    result = await db.execute(query)
    resources = result.scalars().all()

    return {
        "items": resources,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": ceil(total / page_size) if total > 0 else 0
    }
