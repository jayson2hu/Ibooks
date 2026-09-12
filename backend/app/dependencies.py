"""
Shared dependencies for FastAPI endpoints.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional
from app.database import get_db
from app.utils.security import ACCESS_TOKEN_TYPE, decode_access_token
from app.utils.token_blacklist import is_token_blacklisted
from app.models.user import User, UserRole
from app.utils.logging import get_logger
from sqlalchemy import select


# Security scheme
security = HTTPBearer()
logger = get_logger(__name__)


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_user_from_token_payload(
    payload: dict[str, Any],
    db: AsyncSession,
    *,
    expected_token_type: str,
    allow_legacy_untyped: bool = True,
) -> User:
    """Validate token purpose, subject, account status, and auth version."""
    token_type = payload.get("typ")
    if token_type != expected_token_type and not (
        allow_legacy_untyped and token_type is None
    ):
        raise _invalid_credentials()

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise _invalid_credentials() from None

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )

    token_auth_version = payload.get("auth_version")
    if token_auth_version is None:
        version_matches = user.auth_version == 0
    else:
        try:
            version_matches = int(token_auth_version) == user.auth_version
        except (TypeError, ValueError):
            version_matches = False
    if not version_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已失效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user.
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    try:
        token_is_blacklisted = await is_token_blacklisted(token)
    except (RedisError, OSError) as exc:
        logger.warning(
            "Token blacklist backend unavailable",
            extra={
                "event": "token_blacklist_unavailable",
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="认证服务暂不可用，请稍后再试",
        ) from exc

    if token_is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已失效，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return await get_user_from_token_payload(
        payload,
        db,
        expected_token_type=ACCESS_TOKEN_TYPE,
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    return current_user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to require admin role.
    
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_current_staff(
    current_user: User = Depends(get_current_user),
) -> User:
    """Require an administrator or moderator for content operations."""
    if current_user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to get current user if authenticated, None otherwise.
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
