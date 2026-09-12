"""
Security utilities for password hashing and JWT token management.
"""
from datetime import timedelta
import secrets
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from jwt.exceptions import PyJWTError
from app.config import settings
from app.utils.datetime_utils import utc_now


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def _create_token(
    data: Dict[str, Any],
    *,
    expires_delta: timedelta,
    token_type: str,
) -> str:
    """Create a typed JWT with a unique identifier."""
    to_encode = data.copy()
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    now = utc_now()
    to_encode.update(
        {
            "exp": now + expires_delta,
            "iat": now,
            "jti": secrets.token_urlsafe(16),
            "typ": token_type,
        }
    )
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary to encode in the token (usually contains user_id, email)
        expires_delta: Optional custom expiration time
    
    Returns:
        Encoded JWT token string
    """
    return _create_token(
        data,
        expires_delta=expires_delta
        or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type=ACCESS_TOKEN_TYPE,
    )


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a refresh-only JWT with the configured lifetime."""
    return _create_token(
        data,
        expires_delta=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        token_type=REFRESH_TOKEN_TYPE,
    )


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except PyJWTError:
        return None


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password meets security requirements.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
    
    # Add more validations as needed
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and digits"
    
    return True, None
