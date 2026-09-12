"""
Pydantic schemas for User model.
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.models.user import UserRole, UserStatus


# Base schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=200)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    full_name: Optional[str] = Field(None, max_length=200)
    avatar_url: Optional[str] = None


class UserUpdateAdmin(UserUpdate):
    """Schema for admin updating user."""
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserResponse(UserBase):
    """Schema for user response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    role: UserRole
    status: UserStatus
    is_email_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    """Schema for requesting password reset."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Schema for resetting password with a token."""
    token: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)


class Token(BaseModel):
    """Schema for authentication token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    sub: int  # user_id
    email: str
    role: str
    exp: datetime
