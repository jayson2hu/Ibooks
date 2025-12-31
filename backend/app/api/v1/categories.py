"""
Category management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_db
from app.dependencies import get_current_admin
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryTreeResponse
)
from app.schemas.common import Message
from app.models.category import Category
from app.utils.seo import generate_slug
from datetime import datetime


router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse])
async def list_categories(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    List all categories.
    
    - **active_only**: Only return active categories (default: True)
    """
    query = select(Category).order_by(Category.sort_order, Category.name)
    
    if active_only:
        query = query.where(Category.is_active == True)
    
    result = await db.execute(query)
    categories = result.scalars().all()
    
    return categories


@router.get("/tree", response_model=List[CategoryTreeResponse])
async def get_category_tree(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Get categories as a hierarchical tree.
    """
    query = select(Category).order_by(Category.sort_order, Category.name)
    
    if active_only:
        query = query.where(Category.is_active == True)
    
    result = await db.execute(query)
    all_categories = result.scalars().all()
    
    # Build tree structure
    category_dict = {cat.id: cat for cat in all_categories}
    tree = []
    
    for category in all_categories:
        if category.parent_id is None:
            # Root category
            category_response = CategoryTreeResponse.model_validate(category)
            tree.append(category_response)
        else:
            # Child category - add to parent's children
            parent = category_dict.get(category.parent_id)
            if parent:
                if not hasattr(parent, '_children'):
                    parent._children = []
                parent._children.append(CategoryTreeResponse.model_validate(category))
    
    return tree


@router.get("/{slug}", response_model=CategoryResponse)
async def get_category(slug: str, db: AsyncSession = Depends(get_db)):
    """Get category by slug."""
    result = await db.execute(select(Category).where(Category.slug == slug))
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Create a new category (Admin only)."""
    # Generate slug
    slug = generate_slug(category_data.name)
    
    # Check if slug exists
    result = await db.execute(select(Category).where(Category.slug == slug))
    if result.scalar_one_or_none():
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"
    
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
    current_user = Depends(get_current_admin)
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
    current_user = Depends(get_current_admin)
):
    """Delete a category (Admin only)."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    await db.delete(category)
    await db.commit()
    
    return {"message": "Category deleted successfully"}
