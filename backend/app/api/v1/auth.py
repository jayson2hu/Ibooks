"""
Authentication endpoints.
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import secrets
import time
import uuid
import redis.asyncio as redis
from app.database import get_db
from app.config import settings
from app.dependencies import get_current_user, get_user_from_token_payload, security
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
    create_refresh_token,
    decode_access_token,
    REFRESH_TOKEN_TYPE,
    validate_password_strength,
)
from app.utils.datetime_utils import utc_now
from app.utils.rate_limit import check_rate_limit
from app.utils.token_blacklist import blacklist_token, blacklist_token_once
from app.utils import email as email_utils
from app.utils.logging import get_logger
from app.services.site_settings import get_auth_runtime_settings
from app.services.wallet import get_or_create_wallet


router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)
FORGOT_PASSWORD_MAX_CALLS = 3
EMAIL_VERIFICATION_TTL_HOURS = 24


def get_client_ip(request: Request) -> str:
    """Return the connection peer used by the trusted ASGI server.

    Proxy headers must be validated by the server/proxy layer. Reading
    ``X-Forwarded-For`` directly here would let an internet client rotate the
    rate-limit key by supplying an arbitrary header value.
    """
    return request.client.host if request.client else "unknown"


async def enforce_auth_rate_limit(request: Request, action: str, max_calls: int) -> None:
    """Reject excessive auth requests from the same client IP."""
    client_ip = get_client_ip(request)
    key = f"rate_limit:auth:{action}:{client_ip}"
    try:
        allowed = await check_rate_limit(
            key,
            max_calls=max_calls,
            window_seconds=60,
        )
    except (RedisError, OSError) as exc:
        logger.warning(
            "Authentication rate-limit backend unavailable",
            extra={
                "event": "auth_rate_limit_unavailable",
                "action": action,
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="认证保护服务暂不可用，请稍后再试",
        ) from exc
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后再试",
        )


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


async def send_auth_email_best_effort(
    to: str,
    subject: str,
    html_body: str,
    *,
    purpose: str,
) -> bool:
    """Send an auth email without allowing delivery to change API success."""
    try:
        delivered = await email_utils.send_email(to, subject, html_body)
    except Exception as exc:
        # Email runs after the authoritative database operation. Never expose
        # message contents, recipient data, or verification/reset tokens here.
        logger.warning(
            "Auth email delivery failed unexpectedly",
            extra={
                "event": "auth_email_delivery_failed",
                "purpose": purpose,
                "error_type": type(exc).__name__,
            },
        )
        return False

    if not delivered:
        logger.info(
            "Auth email was not delivered",
            extra={
                "event": "auth_email_delivery_degraded",
                "purpose": purpose,
            },
        )
    return bool(delivered)


async def store_password_reset_token(token: str, user_id: int) -> None:
    """Store password reset token in Redis for one hour."""
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await client.setex(f"reset_pwd:{token}", 3600, str(user_id))
    finally:
        await client.aclose()


async def consume_password_reset_token(token: str) -> int | None:
    """Atomically read and delete a password reset token from Redis."""
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    key = f"reset_pwd:{token}"
    try:
        user_id = await client.getdel(key)
        return int(user_id) if user_id is not None else None
    finally:
        await client.aclose()


def create_session_access_token(user: User, session_timeout_minutes: int) -> str:
    """Issue an access token using the effective persisted session timeout."""
    return create_access_token(
        data={
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "auth_version": user.auth_version,
        },
        expires_delta=timedelta(minutes=session_timeout_minutes),
    )


def create_session_refresh_token(user: User) -> str:
    """Issue a refresh-only token bound to the user's auth version."""
    return create_refresh_token(
        data={
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "auth_version": user.auth_version,
        }
    )


def create_session_token_response(
    user: User,
    session_timeout_minutes: int,
) -> dict[str, object]:
    """Build the access/refresh token response used by login and rotation."""
    return {
        "access_token": create_session_access_token(
            user,
            session_timeout_minutes,
        ),
        "refresh_token": create_session_refresh_token(user),
        "token_type": "bearer",
        "user": user,
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user.
    
    - **email**: Valid email address
    - **username**: Unique username
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    """
    auth_settings = await get_auth_runtime_settings(
        db,
        default_session_timeout_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    if not auth_settings.user_registration_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户注册已关闭",
        )

    await enforce_auth_rate_limit(request, "register", max_calls=3)

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
        email_verification_expires_at=utc_now()
        + timedelta(hours=EMAIL_VERIFICATION_TTL_HOURS),
    )
    
    db.add(new_user)
    await db.flush()
    await get_or_create_wallet(db, new_user.id)
    await db.commit()
    await db.refresh(new_user)

    background_tasks.add_task(
        send_auth_email_best_effort,
        new_user.email,
        "请验证您的邮箱",
        build_verify_email_body(verification_token),
        purpose="email_verification",
    )
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password.
    
    Returns JWT access token.
    """
    auth_settings = await get_auth_runtime_settings(
        db,
        default_session_timeout_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    await enforce_auth_rate_limit(
        request,
        "login",
        max_calls=auth_settings.max_login_attempts,
    )

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
    user.last_login_at = utc_now()
    user.login_count += 1
    await db.commit()
    
    return create_session_token_response(
        user,
        auth_settings.session_timeout_minutes,
    )


@router.post("/admin/login", response_model=Token)
async def admin_login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Admin login with email and password.

    Only admin and moderator users can receive an admin token from this endpoint.
    """
    auth_settings = await get_auth_runtime_settings(
        db,
        default_session_timeout_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    await enforce_auth_rate_limit(
        request,
        "admin_login",
        max_calls=auth_settings.max_login_attempts,
    )

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

    user.last_login_at = utc_now()
    user.login_count += 1
    await db.commit()

    return create_session_token_response(
        user,
        auth_settings.session_timeout_minutes,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """Rotate a refresh token and issue a fresh access/refresh pair.

    Untyped JWTs issued before token-purpose claims were introduced remain
    accepted until their original expiry, but typed access tokens can never be
    used at this endpoint.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    current_user = await get_user_from_token_payload(
        payload,
        db,
        expected_token_type=REFRESH_TOKEN_TYPE,
        allow_legacy_untyped=True,
    )

    exp = payload.get("exp")
    ttl = max(int(exp or 0) - int(time.time()), 1)
    try:
        consumed = await blacklist_token_once(token, ttl)
    except (RedisError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="令牌刷新服务暂不可用，请稍后再试",
        ) from exc
    if not consumed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌已使用或已撤销，请重新登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_settings = await get_auth_runtime_settings(
        db,
        default_session_timeout_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return create_session_token_response(
        current_user,
        auth_settings.session_timeout_minutes,
    )


@router.post("/logout", response_model=Message)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Invalidate every access and refresh token for the current user."""
    token = credentials.credentials
    payload = decode_access_token(token)
    exp = payload.get("exp") if payload else None
    ttl = max(int(exp or 0) - int(time.time()), 1)

    # Database-backed versioning is the authoritative revocation mechanism and
    # also covers refresh tokens copied before logout.
    current_user.auth_version += 1
    await db.commit()

    try:
        await blacklist_token(token, ttl)
    except (RedisError, OSError) as exc:
        logger.warning(
            "Logout token blacklist backend unavailable",
            extra={
                "event": "logout_blacklist_unavailable",
                "error_type": type(exc).__name__,
            },
        )
    return {"message": "已登出"}


@router.get("/verify-email", response_model=Message)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Verify a user's email address."""
    result = await db.execute(
        select(User).where(User.email_verification_token == token)
    )
    user = result.scalar_one_or_none()

    if (
        not user
        or user.email_verification_expires_at is None
        or user.email_verification_expires_at <= utc_now()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效或已过期的验证链接"
        )

    user.is_email_verified = True
    user.email_verification_token = None
    user.email_verification_expires_at = None
    await db.commit()

    return {"message": "邮箱验证成功"}


@router.post("/forgot-password", response_model=Message)
async def forgot_password(
    request_data: ForgotPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a password reset email.

    Always returns success to avoid user enumeration.
    """
    await enforce_auth_rate_limit(
        request,
        "forgot_password",
        max_calls=FORGOT_PASSWORD_MAX_CALLS,
    )

    result = await db.execute(select(User).where(User.email == request_data.email))
    user = result.scalar_one_or_none()

    if user:
        token = secrets.token_urlsafe(32)
        try:
            await store_password_reset_token(token, user.id)
        except Exception as exc:
            logger.warning(
                "Password reset token storage failed",
                extra={
                    "event": "password_reset_token_storage_failed",
                    "error_type": type(exc).__name__,
                },
            )
        else:
            background_tasks.add_task(
                send_auth_email_best_effort,
                user.email,
                "重置您的密码",
                build_reset_password_body(token),
                purpose="password_reset",
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
    user.auth_version += 1
    await db.commit()

    return {"message": "密码重置成功"}
