"""
FAQ schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class FAQBase(BaseModel):
    """Base FAQ schema."""
    category: str = Field(..., max_length=100, description="FAQ category")
    question: str = Field(..., description="Question text")
    answer: str = Field(..., description="Answer text")
    display_order: int = Field(default=0, description="Display order")
    is_active: bool = Field(default=True, description="Is active")


class FAQCreate(FAQBase):
    """Schema for creating a FAQ."""
    pass


class FAQUpdate(BaseModel):
    """Schema for updating a FAQ."""
    category: Optional[str] = Field(None, max_length=100)
    question: Optional[str] = None
    answer: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class FAQResponse(FAQBase):
    """Schema for FAQ response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
