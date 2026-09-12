"""
Schemas for crawler management endpoints.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


CrawlerOptionalField = Literal[
    "excerpt",
    "cover_image_url",
    "resource_type",
    "external_published_at",
    "tags",
]

CRAWLER_OPTIONAL_FIELD_KEYS = (
    "excerpt",
    "cover_image_url",
    "resource_type",
    "external_published_at",
    "tags",
)


class CrawlerFieldOption(BaseModel):
    """Selectable crawler field metadata shown in admin UI."""

    key: str
    label: str
    description: str
    required: bool
    enabled: bool


class CrawlerStatusResponse(BaseModel):
    """Crawler runtime status for the admin UI."""

    source_key: str
    source_name: str
    source_site: str
    enabled: bool
    interval_minutes: int
    max_pages: int
    request_timeout_seconds: int
    target_category_id: Optional[int] = None
    available_fields: list[CrawlerFieldOption] = []
    is_running: bool
    last_run_at: Optional[datetime] = None
    last_status: str
    last_message: Optional[str] = None
    last_count: int = 0


class CrawlerConfigUpdate(BaseModel):
    """Strict allowlisted configuration accepted from crawler staff."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(strict=True)
    interval_minutes: int = Field(ge=10, le=10080, strict=True)
    max_pages: int = Field(ge=1, le=50, strict=True)
    request_timeout_seconds: int = Field(ge=1, le=120, strict=True)
    target_category_id: Optional[int] = Field(ge=1, strict=True)
    enabled_fields: list[CrawlerOptionalField] = Field(max_length=5)

    @field_validator("enabled_fields")
    @classmethod
    def validate_enabled_fields(
        cls, enabled_fields: list[CrawlerOptionalField]
    ) -> list[CrawlerOptionalField]:
        """Reject duplicates and persist fields in a stable canonical order."""
        if len(enabled_fields) != len(set(enabled_fields)):
            raise ValueError("enabled_fields must not contain duplicates")
        selected = set(enabled_fields)
        return [
            field
            for field in CRAWLER_OPTIONAL_FIELD_KEYS
            if field in selected
        ]


class CrawlerConfigResponse(CrawlerConfigUpdate):
    """Effective editable configuration returned to crawler staff."""


class CrawlerRunResponse(BaseModel):
    """Crawler execution summary."""

    imported_count: int
    updated_count: int
    skipped_count: int
    total_count: int
    started_at: datetime
    finished_at: datetime
    message: str
