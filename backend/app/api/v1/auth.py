"""
Authentication endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import secrets
import uuid
import redis.asyncio as redis
from app.database import get_db
from app.config import settings
from app.dependencies import get_current_user
from app.schemas.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
)
from app.schemas.common import Message
from app.models.user import User, UserRole
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    validate_password_strength
)
from app.utils import email as email_utils
from app.services.wallet import get_or_create_wallet


router = APIRouter(prefix="/auth", tags=["Authentication"])


def build_verify_email_body(token: str) -> str:
    """Build verification email HTML."""
    verify_url = f"{settings.SITE_URL}/verify-email?token={token}"
    return f"""
    <p>请点击下面的链接完成邮箱验证：</p>
    <p><a href="{verify_url}">{verify_url}</a></p>
    """


def build_reset_password_body(token: str) -> str:
    """Build password reset email HTML."""
    reset_url = f"{settings.SITE_URL}/reset-password?token={token}"
    return f"""
    <p>请点击下面的链接重置密码。该链接 1 小时内有效：</p>
    <p><a href="{reset_url}">{reset_url}</a></p>
    """


async def store_password_reset_token(token: str, user_id: int) -> None:
    """Store password reset token in Redis for one hour."""
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await client.setex(f"reset_pwd:{token}", 3600, str(user_id))
    finally:
        await client.aclose()


async def consume_password_reset_token(token: str) -> int | None:
    """Read and delete a password reset token from Redis."""
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    key = f"reset_pwd:{token}"
    try:
        user_id = await client.get(key)
        if user_id is None:
            return None
        await client.delete(key)
        return int(user_id)
    finally:
        await client.aclose()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user.
    
    - **email**: Valid email address
    - **username**: Unique username
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    """
    # Validate password strength
    is_valid, error_message = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    verification_token = str(uuid.uuid4())
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        email_verification_token=verification_token,
    )
    
    db.add(new_user)
    await db.flush()
    await get_or_create_wallet(db, new_user.id)
    await db.commit()
    await db.refresh(new_user)

    await email_utils.send_email(
        new_user.email,
        "请验证您的邮箱",
        build_verify_email_body(verification_token)
    )
    
    return new_user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password.
    
    Returns JWT access token.
    """
    # Find user by email
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active"
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    user.login_count += 1
    await db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/admin/login", response_model=Token)
async def admin_login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Admin login with email and password.

    Only admin and moderator users can receive an admin token from this endpoint.
    """
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号未激活"
        )

    if user.role not in (UserRole.ADMIN, UserRole.MODERATOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无管理员权限"
        )

    user.last_login_at = datetime.utcnow()
    user.login_count += 1
    await db.commit()

    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user


@router.get("/verify-email", response_model=Message)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Verify a user's email address."""
    result = await db.execute(
        select(User).where(User.email_verification_token == token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效或已过期的验证链接"
        )

    user.is_email_verified = True
    user.email_verification_token = None
    await db.commit()

    return {"message": "邮箱验证成功"}


@router.post("/forgot-password", response_model=Message)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a password reset email.

    Always returns success to avoid user enumeration.
    """
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if user:
        token = secrets.token_urlsafe(32)
        await store_password_reset_token(token, user.id)
        await email_utils.send_email(
            user.email,
            "重置您的密码",
            build_reset_password_body(token)
        )

    return {"message": "如果邮箱存在，我们已发送密码重置邮件"}


@router.post("/reset-password", response_model=Message)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Reset password with a valid reset token."""
    is_valid, error_message = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    user_id = await consume_password_reset_token(request.token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效或已过期的重置链接"
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效或已过期的重置链接"
        )

    user.password_hash = get_password_hash(request.password)
    await db.commit()

    return {"message": "密码重置成功"}
