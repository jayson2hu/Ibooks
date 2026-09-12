"""
Site settings management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.database import get_db
from app.dependencies import get_current_admin
from app.models.site_settings import SiteSetting
from app.models.user import User
from app.schemas.site_settings import (
    PublicSiteSettingResponse,
    SiteSettingResponse,
    SiteSettingUpdate,
    SiteSettingsBatchUpdate,
    SiteSettingsGroup
)
from app.schemas.common import Message
from app.services.site_settings import (
    MAX_LOGIN_ATTEMPTS,
    MAX_LOGIN_ATTEMPTS_KEY,
    MAX_SESSION_TIMEOUT_MINUTES,
    MIN_LOGIN_ATTEMPTS,
    MIN_SESSION_TIMEOUT_MINUTES,
    SESSION_TIMEOUT_MINUTES_KEY,
    SIGNIN_REWARD_COINS_KEY,
    USER_REGISTRATION_ENABLED_KEY,
)
from app.utils import email as email_utils
from app.utils.logging import get_logger


router = APIRouter(prefix="/settings", tags=["Settings"])
logger = get_logger(__name__)

TEST_EMAIL_SUBJECT = "iBooks SMTP 配置测试"
TEST_EMAIL_BODY = """
<p>这是 iBooks 管理后台发出的 SMTP 配置测试邮件。</p>
<p>如果您收到此邮件，说明当前运行环境的邮件发送配置可用。</p>
""".strip()
TEST_EMAIL_FAILURE_MESSAGE = "测试邮件发送失败，请检查后端 SMTP 环境配置后重试"
PUBLIC_SETTING_KEYS = frozenset(
    {
        "site_name",
        "site_description",
        "theme_mode",
        "primary_color",
        "copyright_text",
        "footer_brand_text",
    }
)


def validate_setting_value(key: str, value: str) -> None:
    """Validate special setting values before persistence."""
    if key == USER_REGISTRATION_ENABLED_KEY:
        if value.strip().lower() not in {
            "0",
            "1",
            "false",
            "no",
            "off",
            "on",
            "true",
            "yes",
        }:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户注册开关必须是布尔值",
            )
        return

    if key in {MAX_LOGIN_ATTEMPTS_KEY, SESSION_TIMEOUT_MINUTES_KEY}:
        if key == MAX_LOGIN_ATTEMPTS_KEY:
            minimum = MIN_LOGIN_ATTEMPTS
            maximum = MAX_LOGIN_ATTEMPTS
            message = f"最大登录尝试次数必须是 {minimum} 到 {maximum} 之间的整数"
        else:
            minimum = MIN_SESSION_TIMEOUT_MINUTES
            maximum = MAX_SESSION_TIMEOUT_MINUTES
            message = f"会话超时时间必须是 {minimum} 到 {maximum} 之间的整数"

        try:
            parsed = int(value)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message,
            ) from None
        if not minimum <= parsed <= maximum:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message,
            )
        return

    if key == SIGNIN_REWARD_COINS_KEY:
        try:
            reward = int(value)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="签到奖励币数必须为正整数"
            )
        if reward <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="签到奖励币数必须为正整数"
            )


@router.get("", response_model=List[PublicSiteSettingResponse])
async def get_public_settings(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get public site settings (no authentication required).
    
    Only returns explicitly approved presentation settings. Category names alone
    are not a security boundary because private values may share a category.
    """
    query = select(SiteSetting).where(SiteSetting.key.in_(PUBLIC_SETTING_KEYS))
    
    if category:
        query = query.where(SiteSetting.category == category)
    
    result = await db.execute(query)
    settings = result.scalars().all()
    
    return settings


@router.get("/admin", response_model=List[SiteSettingResponse])
async def get_all_settings(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Get all site settings (Admin only).
    """
    result = await db.execute(select(SiteSetting))
    settings = result.scalars().all()
    
    return settings


@router.get("/grouped", response_model=List[SiteSettingsGroup])
async def get_settings_grouped(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Get all settings grouped by category (Admin only).
    """
    result = await db.execute(select(SiteSetting))
    settings = result.scalars().all()
    
    # Group by category
    grouped = {}
    for setting in settings:
        if setting.category not in grouped:
            grouped[setting.category] = []
        grouped[setting.category].append(setting)
    
    return [
        {"category": cat, "settings": items}
        for cat, items in grouped.items()
    ]


@router.post("/test-email", response_model=Message)
async def send_test_email(
    current_user: User = Depends(get_current_admin),
):
    """Send a fixed SMTP test message to the current administrator."""
    try:
        delivered = await email_utils.send_email(
            current_user.email,
            TEST_EMAIL_SUBJECT,
            TEST_EMAIL_BODY,
        )
    except Exception as exc:
        logger.warning(
            "Administrator SMTP test failed unexpectedly",
            extra={
                "event": "admin_test_email_failed",
                "error_type": type(exc).__name__,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=TEST_EMAIL_FAILURE_MESSAGE,
        ) from exc

    if not delivered:
        logger.warning(
            "Administrator SMTP test was not delivered",
            extra={"event": "admin_test_email_failed"},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=TEST_EMAIL_FAILURE_MESSAGE,
        )

    return {"message": "测试邮件已发送到当前管理员邮箱"}


@router.get("/{key}", response_model=PublicSiteSettingResponse)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific setting by key.
    
    Public presentation settings only.
    """
    result = await db.execute(
        select(SiteSetting).where(
            SiteSetting.key == key,
            SiteSetting.key.in_(PUBLIC_SETTING_KEYS),
        )
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found"
        )

    return setting


@router.put("/{key}", response_model=SiteSettingResponse)
async def update_setting(
    key: str,
    setting_update: SiteSettingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin),
):
    """
    Update a setting (Admin only).
    """
    result = await db.execute(
        select(SiteSetting).where(SiteSetting.key == key)
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found"
        )

    validate_setting_value(key, setting_update.value)
    
    # The authenticated administrator, never request data, owns the audit trail.
    setting.value = setting_update.value
    setting.updated_by = current_user.username
    
    await db.commit()
    await db.refresh(setting)
    
    return setting


@router.post("/batch", response_model=Message)
async def batch_update_settings(
    batch_update: SiteSettingsBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Batch update multiple settings (Admin only).
    
    Request body format:
    {
        "settings": [
            {"key": "copyright_text", "value": "new value"},
            {"key": "site_name", "value": "new name"}
        ]
    }
    """
    updated_count = 0
    
    for item in batch_update.settings:
        key = item.get("key")
        value = item.get("value")
        category = item.get("category", "general")
        
        if not key or value is None:
            continue

        validate_setting_value(key, value)
        
        result = await db.execute(
            select(SiteSetting).where(SiteSetting.key == key)
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
            if hasattr(current_user, 'username'):
                setting.updated_by = current_user.username
            updated_count += 1
        else:
            db.add(SiteSetting(
                key=key,
                value=value,
                category=category,
                updated_by=current_user.username if hasattr(current_user, 'username') else None
            ))
            updated_count += 1
    
    await db.commit()
    
    return {"message": f"Successfully updated {updated_count} settings"}
