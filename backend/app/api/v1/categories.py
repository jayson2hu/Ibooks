"""
Category management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from typing import List
from app.database import get_db
from app.dependencies import get_current_staff
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryTreeResponse
)
from app.schemas.common import Message
from app.models.category import Category
from app.models.resource import Resource
from app.utils.datetime_utils import utc_now
from app.utils.seo import generate_slug


router = APIRouter(prefix="/categories", tags=["Categories"])

CATEGORY_NOT_EMPTY_DETAIL = (
    "Category cannot be deleted while it has child categories or resources"
)


def category_query_with_published_count():
    """Select categories with a live count that never includes public drafts."""
    published_count = (
        select(func.count(Resource.id))
        .where(
            Resource.category_id == Category.id,
            Resource.is_published.is_(True),
        )
        .correlate(Category)
        .scalar_subquery()
    )
    return select(Category, published_count.label("published_resource_count"))


def category_response(category: Category, published_count: int) -> CategoryResponse:
    """Build a response without mutating the stale denormalized model column."""
    return CategoryResponse.model_validate(category).model_copy(
        update={"resource_count": int(published_count or 0)}
    )


@router.get("", response_model=List[CategoryResponse])
async def list_categories(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    List all categories.
    
    - **active_only**: Only return active categories (default: True)
    """
    query = category_query_with_published_count().order_by(
        Category.sort_order,
        Category.name,
    )
    
    if active_only:
        query = query.where(Category.is_active)
    
    result = await db.execute(query)
    rows = result.all()

    return [category_response(category, count) for category, count in rows]


@router.get("/tree", response_model=List[CategoryTreeResponse])
async def get_category_tree(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Get categories as a hierarchical tree.
    """
    query = category_query_with_published_count().order_by(
        Category.sort_order,
        Category.name,
    )
    
    if active_only:
        query = query.where(Category.is_active)
    
    result = await db.execute(query)
    rows = result.all()
    all_categories = [category for category, _ in rows]
    count_by_category_id = {
        category.id: int(count or 0) for category, count in rows
    }
    
    children_by_parent: dict[int | None, list[Category]] = {}
    for category in all_categories:
        children_by_parent.setdefault(category.parent_id, []).append(category)

    def build_node(category: Category) -> CategoryTreeResponse:
        node = CategoryTreeResponse(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description,
            parent_id=category.parent_id,
            icon=category.icon,
            color=category.color,
            cover_image_url=category.cover_image_url,
            is_active=category.is_active,
            sort_order=category.sort_order,
            resource_count=count_by_category_id[category.id],
            created_at=category.created_at,
            children=[build_node(child) for child in children_by_parent.get(category.id, [])],
        )
        return node

    return [build_node(category) for category in children_by_parent.get(None, [])]


@router.get("/{slug}", response_model=CategoryResponse)
async def get_category(slug: str, db: AsyncSession = Depends(get_db)):
    """Get category by slug."""
    result = await db.execute(
        category_query_with_published_count().where(Category.slug == slug)
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    category, count = row
    return category_response(category, count)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_staff)
):
    """Create a new category (Admin only)."""
    # Generate slug
    slug = generate_slug(category_data.name)
    
    # Check if slug exists
    result = await db.execute(select(Category).where(Category.slug == slug))
    if result.scalar_one_or_none():
        slug = f"{slug}-{int(utc_now().timestamp())}"
    
    # Create category
    new_category = Category(
        **category_data.model_dump(exclude_unset=True),
        slug=slug
    )
    
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    
    return new_category


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_staff)
):
    """Update a category (Admin only)."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Update fields
    update_data = category_data.model_dump(exclude_unset=True)
    
    # Update slug if name changed
    if "name" in update_data:
        new_slug = generate_slug(update_data["name"])
        if new_slug != category.slug:
            update_data["slug"] = new_slug
    
    for field, value in update_data.items():
        setattr(category, field, value)
    
    await db.commit()
    await db.refresh(category)
    
    return category


@router.delete("/{category_id}", response_model=Message)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_staff)
):
    """Delete a category (Admin only)."""
    result = await db.execute(
        select(Category).where(Category.id == category_id).with_for_update()
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    dependency_result = await db.execute(
        select(
            select(Category.id)
            .where(Category.parent_id == category_id)
            .exists(),
            select(Resource.id)
            .where(Resource.category_id == category_id)
            .exists(),
        )
    )
    has_children, has_resources = dependency_result.one()
    if has_children or has_resources:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CATEGORY_NOT_EMPTY_DETAIL,
        )

    try:
        await db.delete(category)
        await db.commit()
    except IntegrityError as exc:
        # A dependent row may be inserted after the explicit checks. The
        # database RESTRICT constraints remain the final fail-closed guard.
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CATEGORY_NOT_EMPTY_DETAIL,
        ) from exc
    
    return {"message": "Category deleted successfully"}
