"""
Helpers for site settings values.
"""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site_settings import SiteSetting


SIGNIN_ENABLED_KEY = "signin_enabled"
SIGNIN_REWARD_COINS_KEY = "signin_reward_coins"
SIGNIN_CATEGORY = "signin"

CRAWLER_CATEGORY = "crawler"

CRAWLER_1024_DEFAULT_SETTINGS = [
    {
        "key": "crawler_1024_enabled",
        "value": "false",
        "category": CRAWLER_CATEGORY,
        "description": "Whether the 1024 crawler scheduler is enabled.",
        "updated_by": "system",
    },
    {
        "key": "crawler_1024_interval_minutes",
        "value": "180",
        "category": CRAWLER_CATEGORY,
        "description": "Crawler scheduler interval in minutes.",
        "updated_by": "system",
    },
    {
        "key": "crawler_1024_max_pages",
        "value": "2",
        "category": CRAWLER_CATEGORY,
        "description": "Maximum listing pages to crawl per run.",
        "updated_by": "system",
    },
    {
        "key": "crawler_1024_request_timeout_seconds",
        "value": "15",
        "category": CRAWLER_CATEGORY,
        "description": "HTTP request timeout in seconds.",
        "updated_by": "system",
    },
    {
        "key": "crawler_1024_target_category_id",
        "value": "",
        "category": CRAWLER_CATEGORY,
        "description": "Optional target category ID for imported resources.",
        "updated_by": "system",
    },
    {
        "key": "crawler_1024_enabled_fields",
        "value": "excerpt,cover_image_url,resource_type,external_published_at,tags",
        "category": CRAWLER_CATEGORY,
        "description": "Comma-separated optional fields to sync.",
        "updated_by": "system",
    },
    {
        "key": "crawler_1024_last_run_at",
        "value": "",
        "category": CRAWLER_CATEGORY,
        "description": "Last crawler run timestamp.",
        "updated_by": "system",
    },
    {
        "key": "crawler_1024_last_status",
        "value": "idle",
        "category": CRAWLER_CATEGORY,
        "description": "Last crawler status.",
        "updated_by": "system",
    },
    {
        "key": "crawler_1024_last_message",
        "value": "",
        "category": CRAWLER_CATEGORY,
        "description": "Last crawler message.",
        "updated_by": "system",
    },
    {
        "key": "crawler_1024_last_count",
        "value": "0",
        "category": CRAWLER_CATEGORY,
        "description": "Last synced resource count.",
        "updated_by": "system",
    },
]


@dataclass
class Crawler1024Settings:
    """Runtime configuration for the 1024 metadata crawler."""

    enabled: bool
    interval_minutes: int
    max_pages: int
    request_timeout_seconds: int
    target_category_id: int | None
    enabled_fields: list[str]
    last_run_at: datetime | None
    last_status: str
    last_message: str | None
    last_count: int


async def get_setting_value(db: AsyncSession, key: str, default: str) -> str:
    """Return a setting value or a default if missing."""
    result = await db.execute(select(SiteSetting).where(SiteSetting.key == key))
    setting = result.scalar_one_or_none()
    return setting.value if setting else default


def _parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _parse_int(value: str, default: int, minimum: int | None = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    if minimum is not None:
        return max(parsed, minimum)
    return parsed


def _parse_optional_int(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_datetime(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_csv(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


async def upsert_setting(
    db: AsyncSession,
    *,
    key: str,
    value: str,
    category: str = CRAWLER_CATEGORY,
    description: str | None = None,
    updated_by: str = "system",
) -> SiteSetting:
    """Create or update a site setting."""
    result = await db.execute(select(SiteSetting).where(SiteSetting.key == key))
    setting = result.scalar_one_or_none()
    if setting is None:
        setting = SiteSetting(
            key=key,
            value=value,
            category=category,
            description=description,
            updated_by=updated_by,
        )
        db.add(setting)
    else:
        setting.value = value
        setting.category = category
        setting.description = description
        setting.updated_by = updated_by
    return setting


async def get_1024_crawler_settings(db: AsyncSession) -> Crawler1024Settings:
    """Return 1024 crawler settings with defaults for missing rows."""
    enabled = _parse_bool(await get_setting_value(db, "crawler_1024_enabled", "false"))
    interval_minutes = _parse_int(
        await get_setting_value(db, "crawler_1024_interval_minutes", "180"),
        180,
        minimum=10,
    )
    max_pages = _parse_int(
        await get_setting_value(db, "crawler_1024_max_pages", "2"),
        2,
        minimum=1,
    )
    request_timeout_seconds = _parse_int(
        await get_setting_value(db, "crawler_1024_request_timeout_seconds", "15"),
        15,
        minimum=1,
    )
    target_category_id = _parse_optional_int(
        await get_setting_value(db, "crawler_1024_target_category_id", "")
    )
    enabled_fields = _parse_csv(
        await get_setting_value(
            db,
            "crawler_1024_enabled_fields",
            "excerpt,cover_image_url,resource_type,external_published_at,tags",
        )
    )
    last_run_at = _parse_datetime(
        await get_setting_value(db, "crawler_1024_last_run_at", "")
    )
    last_status = await get_setting_value(db, "crawler_1024_last_status", "idle")
    last_message = await get_setting_value(db, "crawler_1024_last_message", "")
    last_count = _parse_int(
        await get_setting_value(db, "crawler_1024_last_count", "0"),
        0,
        minimum=0,
    )

    return Crawler1024Settings(
        enabled=enabled,
        interval_minutes=interval_minutes,
        max_pages=max_pages,
        request_timeout_seconds=request_timeout_seconds,
        target_category_id=target_category_id,
        enabled_fields=enabled_fields,
        last_run_at=last_run_at,
        last_status=last_status,
        last_message=last_message or None,
        last_count=last_count,
    )


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
