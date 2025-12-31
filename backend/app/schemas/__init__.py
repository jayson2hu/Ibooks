"""
Schemas package.
"""
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserUpdateAdmin,
    UserResponse,
    UserLogin,
    Token,
    TokenPayload
)
from app.schemas.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceResponse,
    ResourceDetailResponse,
    ResourceListResponse
)
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryTreeResponse
)
from app.schemas.contact import (
    ContactCreate,
    ContactUpdate,
    ContactResponse
)
from app.schemas.common import (
    PaginationParams,
    PaginatedResponse,
    Message,
    ErrorResponse
)

__all__ = [
    # User
    "UserCreate",
    "UserUpdate",
    "UserUpdateAdmin",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenPayload",
    # Resource
    "ResourceCreate",
    "ResourceUpdate",
    "ResourceResponse",
    "ResourceDetailResponse",
    "ResourceListResponse",
    # Category
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    "CategoryTreeResponse",
    # Contact
    "ContactCreate",
    "ContactUpdate",
    "ContactResponse",
    # Common
    "PaginationParams",
    "PaginatedResponse",
    "Message",
    "ErrorResponse",
]
