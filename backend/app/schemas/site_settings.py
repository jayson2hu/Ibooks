"""Site settings schemas for API requests and responses."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SiteSettingBase(BaseModel):
    """Base schema for site settings."""
    value: str = Field(..., description="Setting value")
    category: str = Field(default="general", description="Setting category")
    description: Optional[str] = Field(None, description="Setting description")


class SiteSettingCreate(SiteSettingBase):
    """Schema for creating a site setting."""
    key: str = Field(..., min_length=1, max_length=100, description="Setting key")


class SiteSettingUpdate(BaseModel):
    """Schema for updating a site setting."""

    value: str = Field(..., description="Setting value")

    # Older clients may still send ``updated_by``. Ignore it instead of
    # trusting it; the authenticated administrator is the sole audit source.
    model_config = ConfigDict(extra="ignore")


class PublicSiteSettingResponse(BaseModel):
    """Public presentation setting without administrative metadata."""

    key: str
    value: str

    model_config = ConfigDict(from_attributes=True)


class SiteSettingResponse(SiteSettingBase):
    """Schema for site setting response."""
    key: str
    updated_at: datetime
    updated_by: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class SiteSettingsBatchUpdate(BaseModel):
    """Schema for batch updating multiple settings."""
    settings: List[dict] = Field(..., description="List of settings to update")
    # Format: [{"key": "copyright_text", "value": "new value"}, ...]


class SiteSettingsGroup(BaseModel):
    """Schema for grouped settings by category."""
    category: str
    settings: List[SiteSettingResponse]
