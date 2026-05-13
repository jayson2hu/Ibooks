"""
Authentication endpoints for frontend users.
Separated from admin authentication for better security and control.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from app.models.user import User, UserRole, UserStatus
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    validate_password_strength
)
from app.exceptions import (
    ValidationError,
    email_already_exists_error,
    username_already_taken_error,
    invalid_credentials_error,
    account_not_active_error,
    invalid_password_error,
)
from app.schemas.responses import ApiResponse, success_response, error_response
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/user", tags=["User Authentication"])


@router.post(
    "/register",
    response_model=ApiResponse[Token],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password"
)
async def register_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.

    - **email**: Valid email address
    - **username**: Unique username
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)

    Returns newly created user with JWT token and HTTP 201 status.
    """
    # Validate password strength
    is_valid, error_message = validate_password_strength(user_data.password)
    if not is_valid:
        logger.warning(f"Password validation failed for email: {user_data.email}")
        raise invalid_password_error(error_message)

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        logger.warning(f"Registration attempt with existing email: {user_data.email}")
        raise email_already_exists_error()

    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        logger.warning(f"Registration attempt with existing username: {user_data.username}")
        raise username_already_taken_error()

    try:
        # Create new user with USER role (not ADMIN)
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            role=UserRole.USER,  # Always USER role for frontend registration
            status=UserStatus.ACTIVE,
            is_email_verified=False,  # Would be set to True after email verification
            last_login_at=datetime.utcnow(),
            login_count=1,
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        logger.info(f"User registered successfully: {new_user.email}")

        # Create access token for newly registered user
        access_token = create_access_token(
            data={
                "sub": new_user.id,
                "email": new_user.email,
                "role": new_user.role.value,
                "type": "user"  # Mark token type as 'user'
            }
        )

        return ApiResponse(
            status="success",
            code=201,
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user": new_user
            },
            message="User registered successfully"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error registering user: {str(e)}")
        raise


@router.post(
    "/login",
    response_model=ApiResponse[Token],
    summary="Login user",
    description="Authenticate user with email and password, returns JWT token"
)
async def login_user(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password.

    Returns JWT access token for authenticated user.

    - User must have USER role (not ADMIN)
    - User account must be active
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash):
        logger.warning(f"Failed login attempt for email: {credentials.email}")
        raise invalid_credentials_error()

    # Ensure user is not an admin (prevent admin login through user endpoint)
    if user.role == UserRole.ADMIN:
        logger.warning(f"Admin attempted login through user endpoint: {credentials.email}")
        raise invalid_credentials_error()  # Don't reveal that it's admin

    if user.status != UserStatus.ACTIVE:
        logger.warning(f"Login attempt with inactive account: {credentials.email}")
        raise account_not_active_error()

    try:
        # Update last login info
        user.last_login_at = datetime.utcnow()
        user.login_count += 1
        await db.commit()

        # Create access token
        access_token = create_access_token(
            data={
                "sub": user.id,
                "email": user.email,
                "role": user.role.value,
                "type": "user"  # Mark token type as 'user'
            }
        )

        logger.info(f"User logged in successfully: {user.email}")

        return ApiResponse(
            status="success",
            code=200,
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user": user
            },
            message="Login successful"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error during login: {str(e)}")
        raise


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Get current user",
    description="Get information about the currently authenticated user"
)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.
    """
    return ApiResponse(
        status="success",
        code=200,
        data=current_user,
        message="User information retrieved"
    )
