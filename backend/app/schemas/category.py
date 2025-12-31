"""
Pydantic schemas for Category model.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List


class CategoryBase(BaseModel):
    """Base category schema."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    cover_image_url: Optional[str] = None


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class CategoryResponse(CategoryBase):
    """Schema for category response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    is_active: bool
    sort_order: int
    resource_count: int
    created_at: datetime


class CategoryTreeResponse(CategoryResponse):
    """Schema for hierarchical category tree."""
    children: List['CategoryTreeResponse'] = Field(default_factory=list)
