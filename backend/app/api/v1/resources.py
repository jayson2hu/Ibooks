"""
Resource management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, update
from sqlalchemy.exc import IntegrityError
from typing import Optional
from math import ceil
from app.database import get_db
from app.dependencies import get_current_staff, get_optional_user
from app.schemas.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceDetailResponse,
    AdminResourceResponse,
    ResourceAccessCheckResponse,
    ResourceAccessResponse,
    ResourceListResponse
)
from app.schemas.common import Message
from app.models.resource import Resource
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.utils.datetime_utils import utc_now
from app.services.resource_slugs import generate_unique_slug
from app.services.resource_pricing import is_free_resource


router = APIRouter(prefix="/resources", tags=["Resources"])


async def get_authorized_resource(
    db: AsyncSession,
    slug: str,
    current_user: Optional[User],
) -> Resource:
    """Return a published resource after enforcing its delivery policy."""
    result = await db.execute(
        select(Resource).where(Resource.slug == slug, Resource.is_published)
    )
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )

    if not is_free_resource(resource):
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="请先登录",
            )

        order_result = await db.execute(
            select(Order.id).where(
                Order.user_id == current_user.id,
                Order.resource_id == resource.id,
                Order.status == OrderStatus.PAID,
            )
        )
        if order_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="请先购买该资源",
            )

    return resource


def build_resource_access(resource: Resource) -> ResourceAccessResponse:
    """Build the delivery response without exposing the full resource row."""
    return ResourceAccessResponse(
        cloud_link=resource.cloud_link,
        backup_links=resource.backup_links or [],
        access_code=resource.access_code,
    )


@router.get("", response_model=ResourceListResponse)
async def list_resources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    is_featured: Optional[bool] = None,
    is_free: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all published resources with pagination and filters.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **category_id**: Filter by category
    - **resource_type**: Filter by resource type
    - **is_featured**: Filter featured resources
    - **is_free**: Filter free resources
    - **search**: Search in title and description
    """
    # Build query
    query = select(Resource).where(Resource.is_published)

    # Apply filters
    if category_id:
        query = query.where(Resource.category_id == category_id)

    if resource_type:
        query = query.where(Resource.resource_type == resource_type)

    if is_featured is not None:
        query = query.where(Resource.is_featured == is_featured)

    if is_free is not None:
        query = query.where(Resource.is_free == is_free)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Resource.title.ilike(search_term),
                Resource.description.ilike(search_term),
                Resource.excerpt.ilike(search_term)
            )
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Resource.sort_order.desc(), Resource.created_at.desc())

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


@router.get("/{slug}", response_model=ResourceDetailResponse)
async def get_resource(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get resource details by slug.

    Cloud links are only visible to authenticated users (or can be made public).
    """
    result = await db.execute(
        select(Resource).where(Resource.slug == slug, Resource.is_published)
    )
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )

    return resource


@router.post("/{slug}/view", status_code=status.HTTP_204_NO_CONTENT)
async def record_resource_view(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Atomically record one explicit client-side resource detail view."""
    result = await db.execute(
        update(Resource)
        .where(Resource.slug == slug, Resource.is_published)
        .values(view_count=Resource.view_count + 1)
        .returning(Resource.id)
    )
    if result.scalar_one_or_none() is None:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )
    await db.commit()


@router.get("/{slug}/access", response_model=ResourceAccessCheckResponse)
async def get_resource_access(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Check whether the caller may retrieve a resource.

    This endpoint intentionally returns no delivery links and does not count a
    download. Paid resources require a completed order owned by the current
    user.
    """
    await get_authorized_resource(db, slug, current_user)
    return ResourceAccessCheckResponse(has_access=True)


@router.post("/{slug}/download", response_model=ResourceAccessResponse)
async def download_resource(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """Explicitly retrieve delivery data and atomically count the download."""
    resource = await get_authorized_resource(db, slug, current_user)
    await db.execute(
        update(Resource)
        .where(Resource.id == resource.id)
        .values(download_count=Resource.download_count + 1)
    )
    await db.commit()
    return build_resource_access(resource)


@router.post("", response_model=AdminResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    resource_data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_staff)
):
    """
    Create a new resource (Admin only).
    """
    slug = await generate_unique_slug(db, resource_data.title)

    # Create resource
    new_resource = Resource(
        **resource_data.model_dump(exclude_unset=True),
        source_type="manual",
        slug=slug,
        published_at=utc_now() if resource_data.is_published else None
    )

    db.add(new_resource)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resource slug already exists; please retry",
        ) from None
    await db.refresh(new_resource)

    return new_resource


@router.patch("/{resource_id}", response_model=AdminResourceResponse)
async def update_resource(
    resource_id: int,
    resource_data: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_staff)
):
    """
    Update a resource (Admin only).
    """
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )

    # Update fields
    update_data = resource_data.model_dump(exclude_unset=True)

    # Update slug if title changed
    if "title" in update_data:
        new_slug = await generate_unique_slug(
            db,
            update_data["title"],
            exclude_resource_id=resource.id,
        )
        if new_slug != resource.slug:
            update_data["slug"] = new_slug

    for field, value in update_data.items():
        setattr(resource, field, value)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resource slug already exists; please retry",
        ) from None
    await db.refresh(resource)

    return resource


@router.delete("/{resource_id}", response_model=Message)
async def delete_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_staff)
):
    """
    Delete a resource (Admin only).
    """
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    resource = result.scalar_one_or_none()

    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )

    order_result = await db.execute(
        select(Order.id).where(Order.resource_id == resource.id).limit(1)
    )
    if order_result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该资源已有订单记录，无法删除；请改为下架资源",
        )

    await db.delete(resource)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该资源已有订单记录，无法删除；请改为下架资源",
        ) from None

    return {"message": "Resource deleted successfully"}
