"""
Standardized API response schemas for consistent responses across all endpoints.
"""
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Optional, Any, Union
from enum import Enum
from datetime import datetime

T = TypeVar('T')


class ResponseStatus(str, Enum):
    """Standard response status codes."""
    SUCCESS = "success"
    ERROR = "error"
    VALIDATION_ERROR = "validation_error"


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard API response wrapper for all endpoints.

    Provides consistent response format:
    ```json
    {
        "status": "success",
        "code": 200,
        "data": {...},
        "message": "Operation successful"
    }
    ```
    """
    status: ResponseStatus = ResponseStatus.SUCCESS
    code: int = 200
    data: Optional[T] = None
    message: str = "Success"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorDetail(BaseModel):
    """Error detail with field information."""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """
    Standard error response format.

    Example:
    ```json
    {
        "status": "error",
        "code": 400,
        "errors": [
            {"field": "email", "message": "Invalid email format", "code": "INVALID_EMAIL"}
        ],
        "message": "Validation failed"
    }
    ```
    """
    status: ResponseStatus = ResponseStatus.ERROR
    code: int = 400
    errors: List[ErrorDetail] = []
    message: str = "An error occurred"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there's a next page")
    has_prev: bool = Field(..., description="Whether there's a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard paginated response with metadata.

    Example:
    ```json
    {
        "status": "success",
        "code": 200,
        "data": [...],
        "meta": {
            "total": 100,
            "page": 1,
            "page_size": 20,
            "pages": 5,
            "has_next": true,
            "has_prev": false
        },
        "message": "Retrieved successfully"
    }
    ```
    """
    status: ResponseStatus = ResponseStatus.SUCCESS
    code: int = 200
    data: List[T]
    meta: PaginationMeta
    message: str = "Retrieved successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Message(BaseModel):
    """Simple message response."""
    message: str
    code: Optional[str] = None


def success_response(
    data: Optional[T] = None,
    message: str = "Success",
    code: int = 200
) -> ApiResponse:
    """Create a standard success response."""
    return ApiResponse(
        status=ResponseStatus.SUCCESS,
        code=code,
        data=data,
        message=message
    )


def error_response(
    message: str = "An error occurred",
    code: int = 400,
    errors: Optional[List[ErrorDetail]] = None
) -> ErrorResponse:
    """Create a standard error response."""
    return ErrorResponse(
        status=ResponseStatus.ERROR,
        code=code,
        errors=errors or [],
        message=message
    )


def paginated_response(
    data: List[T],
    total: int,
    page: int,
    page_size: int,
    message: str = "Retrieved successfully"
) -> PaginatedResponse:
    """Create a paginated response with metadata."""
    total_pages = (total + page_size - 1) // page_size
    return PaginatedResponse(
        status=ResponseStatus.SUCCESS,
        code=200,
        data=data,
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=page_size,
            pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        ),
        message=message
    )
