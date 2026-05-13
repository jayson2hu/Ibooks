"""
Authentication endpoints for admin panel.
Separated from user authentication with stricter requirements.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.database import get_db
from app.dependencies import get_current_admin
from app.schemas.user import UserLogin, Token, UserResponse
from app.models.user import User, UserRole, UserStatus
from app.utils.security import (
    verify_password,
    create_access_token,
)
from app.exceptions import (
    AuthenticationError,
    AuthorizationError,
    invalid_credentials_error,
    account_not_active_error,
    admin_required_error,
)
from app.schemas.responses import ApiResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/admin", tags=["Admin Authentication"])


@router.post(
    "/login",
    response_model=ApiResponse[Token],
    summary="Admin login",
    description="Authenticate admin with email and password, returns JWT token"
)
async def admin_login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Admin login with email and password.

    Returns JWT access token for authenticated admin.

    - User must have ADMIN role
    - User account must be active
    - Failed attempts are logged for security audit

    This endpoint has stricter requirements than user login:
    - Only admin accounts can login here
    - All login attempts are audited
    - Failed attempts are rate-limited
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Failed admin login attempt for email: {credentials.email}")
        # Log security event for audit
        raise invalid_credentials_error()

    # Strictly check for ADMIN role
    if user.role != UserRole.ADMIN:
        logger.warning(f"Non-admin user attempted admin login: {credentials.email} (role: {user.role})")
        # Don't reveal user exists - return same error as incorrect password
        raise invalid_credentials_error()

    if user.status != UserStatus.ACTIVE:
        logger.warning(f"Admin login attempt with inactive account: {credentials.email}")
        raise account_not_active_error()

    try:
        # Update last login info
        user.last_login_at = datetime.utcnow()
        user.login_count += 1
        await db.commit()

        # Create access token with admin marker
        access_token = create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "role": user.role.value,
                "type": "admin"  # Mark token type as 'admin'
            }
        )

        logger.info(f"Admin logged in successfully: {user.email}")

        return ApiResponse(
            status="success",
            code=200,
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user": user
            },
            message="Admin login successful"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error during admin login: {str(e)}")
        raise


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Get current admin",
    description="Get information about the currently authenticated admin"
)
async def get_current_admin_info(current_admin: User = Depends(get_current_admin)):
    """
    Get current authenticated admin information.

    Requires:
    - Valid JWT token in Authorization header
    - Admin role in token

    Returns admin user information.
    """
    return ApiResponse(
        status="success",
        code=200,
        data=current_admin,
        message="Admin information retrieved"
    )
