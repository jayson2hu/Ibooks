"""
Common schemas used across the application.
"""
from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class Message(BaseModel):
    """Generic message response."""
    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
    code: Optional[str] = None
