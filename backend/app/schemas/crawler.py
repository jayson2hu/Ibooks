"""
Schemas for crawler management endpoints.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


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


class CrawlerRunResponse(BaseModel):
    """Crawler execution summary."""

    imported_count: int
    updated_count: int
    skipped_count: int
    total_count: int
    started_at: datetime
    finished_at: datetime
    message: str
