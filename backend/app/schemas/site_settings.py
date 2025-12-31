"""
Site settings schemas for API requests and responses.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List


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
    updated_by: Optional[str] = None


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
