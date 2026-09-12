"""Search endpoint."""
import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from math import ceil
from app.database import get_db
from app.schemas.resource import ResourceListResponse
from app.models.resource import Resource
from app.utils.rate_limit import check_rate_limit


router = APIRouter(prefix="/search", tags=["Search"])
logger = logging.getLogger(__name__)


async def enforce_search_rate_limit(request: Request) -> None:
    """Bound public search traffic without making Redis an availability dependency."""
    client_ip = request.client.host if request.client else "unknown"
    try:
        allowed = await check_rate_limit(
            f"rate_limit:search:{client_ip}",
            max_calls=30,
            window_seconds=60,
        )
    except (RedisError, OSError) as exc:
        logger.warning(
            "Search rate-limit backend unavailable",
            extra={
                "event": "search_rate_limit_unavailable",
                "error_type": type(exc).__name__,
            },
        )
        return

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="搜索请求过于频繁，请稍后再试",
        )


@router.get("", response_model=ResourceListResponse)
async def search_resources(
    request: Request,
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    scope: Literal["all", "course", "ebook", "doc"] = Query(
        "all",
        description="Limit results to a supported resource type",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Search resources by title, description, and tags.

    - **q**: Search query (minimum 1 character)
    - **scope**: all, course, ebook, or doc
    - **page**: Page number
    - **page_size**: Items per page
    """
    await enforce_search_rate_limit(request)
    search_term = f"%{q}%"

    # Public search must never expose drafts. Featured is presentation metadata,
    # not a publication override.
    query = select(Resource).where(
        Resource.is_published,
        or_(
            Resource.title.ilike(search_term),
            Resource.description.ilike(search_term),
            Resource.excerpt.ilike(search_term),
            Resource.meta_keywords.ilike(search_term)
        )
    )

    scope_filters = {
        "course": or_(
            func.lower(Resource.resource_type).in_(("course", "video")),
            Resource.resource_type.ilike("%课程%"),
        ),
        "ebook": or_(
            func.lower(Resource.resource_type).in_(("ebook", "book")),
            Resource.resource_type.ilike("%电子书%"),
        ),
        "doc": or_(
            func.lower(Resource.resource_type).in_(("doc", "document")),
            Resource.resource_type.ilike("%文档%"),
        ),
    }
    scope_filter = scope_filters.get(scope)
    if scope_filter is not None:
        query = query.where(scope_filter)

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
