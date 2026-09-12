"""
Pydantic schemas for Resource model.
"""
from pydantic import BaseModel, Field, ConfigDict, ValidationInfo, field_validator
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from urllib.parse import urlsplit


MAX_RESOURCE_URLS = 20
MAX_RESOURCE_URL_LENGTH = 2048


def validate_resource_url_list(value: object, info: ValidationInfo) -> list[str]:
    """Validate JSON URL arrays without coercing or silently normalizing input."""
    if not isinstance(value, list):
        raise ValueError(f"{info.field_name} must be an array of URLs")
    if len(value) > MAX_RESOURCE_URLS:
        raise ValueError(
            f"{info.field_name} must contain at most {MAX_RESOURCE_URLS} URLs"
        )

    validated: list[str] = []
    seen: set[str] = set()
    for index, raw_url in enumerate(value, start=1):
        if not isinstance(raw_url, str):
            raise ValueError(f"{info.field_name} item {index} must be a string")
        if raw_url != raw_url.strip():
            raise ValueError(
                f"{info.field_name} item {index} must not have surrounding whitespace"
            )
        if not raw_url or len(raw_url) > MAX_RESOURCE_URL_LENGTH:
            raise ValueError(
                f"{info.field_name} item {index} must be 1-{MAX_RESOURCE_URL_LENGTH} characters"
            )
        if any(character.isspace() for character in raw_url):
            raise ValueError(f"{info.field_name} item {index} must not contain whitespace")

        try:
            parsed = urlsplit(raw_url)
            parsed.port
        except ValueError as exc:
            raise ValueError(f"{info.field_name} item {index} is not a valid URL") from exc

        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            raise ValueError(
                f"{info.field_name} item {index} must be an HTTP or HTTPS URL"
            )
        if parsed.username is not None or parsed.password is not None:
            raise ValueError(
                f"{info.field_name} item {index} must not include URL credentials"
            )
        if raw_url in seen:
            raise ValueError(f"{info.field_name} must not contain duplicate URLs")

        seen.add(raw_url)
        validated.append(raw_url)

    return validated


class ResourceBase(BaseModel):
    """Base resource schema."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    excerpt: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = None
    tags: List[str] = Field(default_factory=list)
    price: Decimal = Field(default=Decimal("0.00"), ge=0)
    coin_price: int = Field(default=0, ge=0)
    original_price: Optional[Decimal] = Field(None, ge=0)
    is_free: bool = False
    file_size: Optional[str] = None
    file_format: Optional[str] = None
    resource_type: Optional[str] = None
    cover_image_url: Optional[str] = None


class ResourceCreate(ResourceBase):
    """Schema for creating a resource."""
    cloud_link: Optional[str] = None
    backup_links: List[str] = Field(default_factory=list, max_length=MAX_RESOURCE_URLS)
    access_code: Optional[str] = None
    preview_images: List[str] = Field(default_factory=list, max_length=MAX_RESOURCE_URLS)
    is_published: bool = True
    is_featured: bool = False
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None

    _validate_resource_urls = field_validator(
        "backup_links", "preview_images", mode="before"
    )(validate_resource_url_list)


class ResourceUpdate(BaseModel):
    """Schema for updating a resource."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    excerpt: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[List[str]] = None
    price: Optional[Decimal] = Field(None, ge=0)
    coin_price: Optional[int] = Field(None, ge=0)
    original_price: Optional[Decimal] = None
    is_free: Optional[bool] = None
    cloud_link: Optional[str] = None
    backup_links: List[str] = Field(default_factory=list, max_length=MAX_RESOURCE_URLS)
    access_code: Optional[str] = None
    file_size: Optional[str] = None
    file_format: Optional[str] = None
    resource_type: Optional[str] = None
    cover_image_url: Optional[str] = None
    preview_images: List[str] = Field(default_factory=list, max_length=MAX_RESOURCE_URLS)
    is_published: Optional[bool] = None
    is_featured: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = None

    _validate_resource_urls = field_validator(
        "backup_links", "preview_images", mode="before"
    )(validate_resource_url_list)


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
    """Schema for public resource details."""
    preview_images: List[str] = Field(default_factory=list)


class AdminResourceResponse(ResourceResponse):
    """Resource response for administrators, including delivery fields."""
    cloud_link: Optional[str] = None
    access_code: Optional[str] = None
    backup_links: List[str] = Field(default_factory=list)
    preview_images: List[str] = Field(default_factory=list)


class ResourceAccessCheckResponse(BaseModel):
    """Successful permission check without resource delivery secrets."""
    has_access: bool = True


class ResourceAccessResponse(BaseModel):
    """Authorized delivery data returned only by the download endpoint."""
    cloud_link: Optional[str] = None
    backup_links: List[str] = Field(default_factory=list)
    access_code: Optional[str] = None


class ResourceListResponse(BaseModel):
    """Schema for paginated resource list."""
    items: List[ResourceResponse]
    total: int
    page: int
    page_size: int
    pages: int
