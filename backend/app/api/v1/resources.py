"""
Resource management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional, List
from math import ceil
from app.database import get_db
from app.dependencies import get_current_admin, get_optional_user
from app.schemas.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
    ResourceDetailResponse,
    ResourceListResponse
)
from app.schemas.common import Message
from app.models.resource import Resource
from app.models.user import User
from app.utils.seo import generate_slug
from datetime import datetime


router = APIRouter(prefix="/resources", tags=["Resources"])


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
    query = select(Resource).where(Resource.is_published == True)
    
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
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Get resource details by slug.
    
    Cloud links are only visible to authenticated users (or can be made public).
    """
    result = await db.execute(
        select(Resource).where(Resource.slug == slug, Resource.is_published == True)
    )
    resource = result.scalar_one_or_none()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    
    # Increment view count
    resource.view_count += 1
    await db.commit()
    
    return resource


@router.post("", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
async def create_resource(
    resource_data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new resource (Admin only).
    """
    # Generate slug from title
    slug = generate_slug(resource_data.title)
    
    # Check if slug already exists
    result = await db.execute(select(Resource).where(Resource.slug == slug))
    if result.scalar_one_or_none():
        # Add timestamp to make it unique
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"
    
    # Create resource
    new_resource = Resource(
        **resource_data.model_dump(exclude_unset=True),
        slug=slug,
        published_at=datetime.utcnow() if resource_data.is_published else None
    )
    
    db.add(new_resource)
    await db.commit()
    await db.refresh(new_resource)
    
    return new_resource


@router.patch("/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: int,
    resource_data: ResourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
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
        new_slug = generate_slug(update_data["title"])
        if new_slug != resource.slug:
            update_data["slug"] = new_slug
    
    for field, value in update_data.items():
        setattr(resource, field, value)
    
    await db.commit()
    await db.refresh(resource)
    
    return resource


@router.delete("/{resource_id}", response_model=Message)
async def delete_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin)
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
    
    await db.delete(resource)
    await db.commit()
    
    return {"message": "Resource deleted successfully"}
