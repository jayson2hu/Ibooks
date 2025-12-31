"""
Pydantic schemas for Resource model.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from decimal import Decimal


class ResourceBase(BaseModel):
    """Base resource schema."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    excerpt: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    price: Decimal = Field(default=Decimal("0.00"), ge=0)
    original_price: Optional[Decimal] = Field(None, ge=0)
    is_free: bool = False
    file_size: Optional[str] = None
    file_format: Optional[str] = None
    resource_type: Optional[str] = None
    cover_image_url: Optional[str] = None


class ResourceCreate(ResourceBase):
    """Schema for creating a resource."""
    cloud_link: Optional[str] = None
    access_code: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None


class ResourceUpdate(BaseModel):
    """Schema for updating a resource."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    excerpt: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    price: Optional[Decimal] = Field(None, ge=0)
    original_price: Optional[Decimal] = None
    is_free: Optional[bool] = None
    cloud_link: Optional[str] = None
    access_code: Optional[str] = None
    file_size: Optional[str] = None
    file_format: Optional[str] = None
    resource_type: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None


class ResourceResponse(ResourceBase):
    """Schema for resource response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    slug: str
    is_published: bool
    is_featured: bool
    view_count: int
    download_count: int
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None


class ResourceDetailResponse(ResourceResponse):
    """Schema for detailed resource response (includes cloud link)."""
    cloud_link: Optional[str] = None
    access_code: Optional[str] = None
    backup_links: List[str] = Field(default_factory=list)
    preview_images: List[str] = Field(default_factory=list)


class ResourceListResponse(BaseModel):
    """Schema for paginated resource list."""
    items: List[ResourceResponse]
    total: int
    page: int
    page_size: int
    pages: int
