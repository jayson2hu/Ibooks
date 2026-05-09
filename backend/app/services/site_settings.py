"""
Helpers for site settings values.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site_settings import SiteSetting


SIGNIN_ENABLED_KEY = "signin_enabled"
SIGNIN_REWARD_COINS_KEY = "signin_reward_coins"
SIGNIN_CATEGORY = "signin"


async def get_setting_value(db: AsyncSession, key: str, default: str) -> str:
    """Return a setting value or a default if missing."""
    result = await db.execute(select(SiteSetting).where(SiteSetting.key == key))
    setting = result.scalar_one_or_none()
    return setting.value if setting else default


async def get_signin_enabled(db: AsyncSession) -> bool:
    """Return whether daily sign-in is enabled."""
    value = await get_setting_value(db, SIGNIN_ENABLED_KEY, "false")
    return value.strip().lower() in ("1", "true", "yes", "on")


async def get_signin_reward_coins(db: AsyncSession) -> int:
    """Return configured sign-in reward coins."""
    value = await get_setting_value(db, SIGNIN_REWARD_COINS_KEY, "5")
    try:
        reward = int(value)
    except ValueError:
        reward = 5
    return reward if reward > 0 else 5
