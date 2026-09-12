"""
Unified exception handling system with standard error responses.
"""
from fastapi import HTTPException, status
from typing import Optional, List, Dict
from app.schemas.responses import ErrorDetail


class AppException(HTTPException):
    """Base application exception with standardized response."""

    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        message: str = "An error occurred",
        detail: Optional[str] = None,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize exception with details."""
        self.status_code = status_code
        self.message = message
        self.detail = detail or message
        self.error_code = error_code

        super().__init__(
            status_code=status_code,
            detail=detail or message,
            headers=headers,
        )


class ValidationError(AppException):
    """Validation error for invalid input data."""

    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[List[ErrorDetail]] = None,
        error_code: str = "VALIDATION_ERROR",
    ):
        """Initialize validation error with field errors."""
        self.errors = errors or []
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            message=message,
            detail=message,
            error_code=error_code,
        )


class AuthenticationError(AppException):
    """Authentication error for invalid credentials."""

    def __init__(
        self,
        message: str = "Invalid authentication credentials",
        error_code: str = "AUTH_ERROR",
    ):
        """Initialize authentication error."""
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            detail=message,
            error_code=error_code,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(AppException):
    """Authorization error for insufficient permissions."""

    def __init__(
        self,
        message: str = "Not enough permissions",
        error_code: str = "FORBIDDEN",
    ):
        """Initialize authorization error."""
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            detail=message,
            error_code=error_code,
        )


class NotFoundError(AppException):
    """Resource not found error."""

    def __init__(
        self,
        resource: str = "Resource",
        error_code: str = "NOT_FOUND",
    ):
        """Initialize not found error."""
        message = f"{resource} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            detail=message,
            error_code=error_code,
        )


class ConflictError(AppException):
    """Resource conflict error (e.g., duplicate entry)."""

    def __init__(
        self,
        message: str = "Resource already exists",
        error_code: str = "CONFLICT",
    ):
        """Initialize conflict error."""
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            detail=message,
            error_code=error_code,
        )


class RateLimitError(AppException):
    """Rate limit exceeded error."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
    ):
        """Initialize rate limit error."""
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)

        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            detail=message,
            error_code="RATE_LIMIT_EXCEEDED",
            headers=headers,
        )


class InternalServerError(AppException):
    """Internal server error."""

    def __init__(
        self,
        message: str = "Internal server error",
        error_code: str = "INTERNAL_ERROR",
    ):
        """Initialize internal server error."""
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            detail=message,
            error_code=error_code,
        )


class DatabaseError(InternalServerError):
    """Database operation error."""

    def __init__(
        self,
        message: str = "Database operation failed",
        error_code: str = "DATABASE_ERROR",
    ):
        """Initialize database error."""
        super().__init__(
            message=message,
            error_code=error_code,
        )


class TransactionError(DatabaseError):
    """Transaction operation error."""

    def __init__(
        self,
        message: str = "Transaction failed",
        error_code: str = "TRANSACTION_ERROR",
    ):
        """Initialize transaction error."""
        super().__init__(
            message=message,
            error_code=error_code,
        )


# Convenience functions for common errors

def email_already_exists_error() -> ConflictError:
    """Email already registered error."""
    return ConflictError(
        message="Email already registered",
        error_code="EMAIL_EXISTS"
    )


def username_already_taken_error() -> ConflictError:
    """Username already taken error."""
    return ConflictError(
        message="Username already taken",
        error_code="USERNAME_EXISTS"
    )


def invalid_credentials_error() -> AuthenticationError:
    """Invalid credentials error."""
    return AuthenticationError(
        message="Incorrect email or password",
        error_code="INVALID_CREDENTIALS"
    )


def account_not_active_error() -> AuthorizationError:
    """Account not active error."""
    return AuthorizationError(
        message="Account is not active",
        error_code="ACCOUNT_INACTIVE"
    )


def admin_required_error() -> AuthorizationError:
    """Admin role required error."""
    return AuthorizationError(
        message="Admin privileges required",
        error_code="ADMIN_REQUIRED"
    )


def invalid_password_error(reason: str = "") -> ValidationError:
    """Invalid password error."""
    message = "Invalid password"
    if reason:
        message += f": {reason}"
    return ValidationError(
        message=message,
        error_code="INVALID_PASSWORD",
        errors=[
            ErrorDetail(
                field="password",
                message=reason or "Password does not meet requirements",
                code="PASSWORD_INVALID"
            )
        ]
    )
