"""
Pydantic schemas for Contact model.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.contact import ContactType


class ContactBase(BaseModel):
    """Base contact schema."""
    type: ContactType
    label: str = Field(..., min_length=1, max_length=200)
    value: str = Field(..., min_length=1)
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class ContactCreate(ContactBase):
    """Schema for creating a contact."""
    qr_code_url: Optional[str] = None
    is_copyable: bool = True
    is_clickable: bool = False
    link_url: Optional[str] = None
    display_order: int = 0
    show_in_header: bool = False
    show_in_footer: bool = True
    show_in_contact_page: bool = True
    show_in_sidebar: bool = False


class ContactUpdate(BaseModel):
    """Schema for updating a contact."""
    label: Optional[str] = Field(None, min_length=1, max_length=200)
    value: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    qr_code_url: Optional[str] = None
    is_copyable: Optional[bool] = None
    is_clickable: Optional[bool] = None
    link_url: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None
    show_in_header: Optional[bool] = None
    show_in_footer: Optional[bool] = None
    show_in_contact_page: Optional[bool] = None
    show_in_sidebar: Optional[bool] = None


class ContactResponse(ContactBase):
    """Schema for contact response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    qr_code_url: Optional[str] = None
    is_copyable: bool
    is_clickable: bool
    link_url: Optional[str] = None
    is_active: bool
    display_order: int
    show_in_header: bool
    show_in_footer: bool
    show_in_contact_page: bool
    show_in_sidebar: bool
    created_at: datetime
