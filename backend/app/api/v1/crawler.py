"""
Crawler management endpoints.
"""
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_staff
from app.models.category import Category
from app.schemas.crawler import (
    CRAWLER_OPTIONAL_FIELD_KEYS,
    CrawlerConfigResponse,
    CrawlerConfigUpdate,
    CrawlerRunResponse,
    CrawlerStatusResponse,
)
from app.services.crawler_service import (
    CrawlerAlreadyRunningError,
    CrawlerCoordinationUnavailableError,
    source_1024_crawler_manager,
)
from app.services.site_settings import (
    CRAWLER_1024_DEFAULT_SETTINGS,
    get_1024_crawler_settings,
    upsert_setting,
)


router = APIRouter(prefix="/crawler", tags=["Crawler"])

CRAWLER_CONFIG_SETTING_KEYS = {
    "crawler_1024_enabled",
    "crawler_1024_interval_minutes",
    "crawler_1024_max_pages",
    "crawler_1024_request_timeout_seconds",
    "crawler_1024_target_category_id",
    "crawler_1024_enabled_fields",
}
CRAWLER_SETTING_METADATA = {
    setting["key"]: setting
    for setting in CRAWLER_1024_DEFAULT_SETTINGS
    if setting["key"] in CRAWLER_CONFIG_SETTING_KEYS
}


async def get_effective_crawler_config(db: AsyncSession) -> CrawlerConfigResponse:
    """Load only editable crawler configuration with safe effective defaults."""
    crawler_settings = await get_1024_crawler_settings(db)
    selected_fields = set(crawler_settings.enabled_fields)
    target_category_id = crawler_settings.target_category_id
    if target_category_id is not None:
        target_category_id = await db.scalar(
            select(Category.id).where(Category.id == target_category_id)
        )
    return CrawlerConfigResponse(
        enabled=crawler_settings.enabled,
        interval_minutes=min(10080, max(10, crawler_settings.interval_minutes)),
        max_pages=min(50, max(1, crawler_settings.max_pages)),
        request_timeout_seconds=min(
            120, max(1, crawler_settings.request_timeout_seconds)
        ),
        target_category_id=target_category_id,
        enabled_fields=[
            field
            for field in CRAWLER_OPTIONAL_FIELD_KEYS
            if field in selected_fields
        ],
    )


@router.get("/1024/config", response_model=CrawlerConfigResponse)
async def get_1024_crawler_config(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_staff),
):
    """Return editable 1024 crawler configuration to staff users."""
    return await get_effective_crawler_config(db)


@router.put("/1024/config", response_model=CrawlerConfigResponse)
async def update_1024_crawler_config(
    config_update: CrawlerConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_staff),
):
    """Update only allowlisted 1024 crawler configuration as one transaction."""
    if config_update.target_category_id is not None:
        category_id = await db.scalar(
            select(Category.id).where(Category.id == config_update.target_category_id)
        )
        if category_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target category does not exist",
            )

    values = {
        "crawler_1024_enabled": str(config_update.enabled).lower(),
        "crawler_1024_interval_minutes": str(config_update.interval_minutes),
        "crawler_1024_max_pages": str(config_update.max_pages),
        "crawler_1024_request_timeout_seconds": str(
            config_update.request_timeout_seconds
        ),
        "crawler_1024_target_category_id": (
            str(config_update.target_category_id)
            if config_update.target_category_id is not None
            else ""
        ),
        "crawler_1024_enabled_fields": ",".join(config_update.enabled_fields),
    }
    updated_by = getattr(current_user, "username", "staff")

    for key, value in values.items():
        metadata = CRAWLER_SETTING_METADATA[key]
        await upsert_setting(
            db,
            key=key,
            value=value,
            category=metadata["category"],
            description=metadata["description"],
            updated_by=updated_by,
        )

    await db.commit()
    return await get_effective_crawler_config(db)


@router.get("/1024/status", response_model=CrawlerStatusResponse)
async def get_1024_crawler_status(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_staff),
):
    """Get crawler runtime status and effective settings."""
    return await source_1024_crawler_manager.get_status(db)


@router.post("/1024/run", response_model=CrawlerRunResponse)
async def run_1024_crawler(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_staff),
):
    """Run the 1024 metadata crawler immediately."""
    updated_by = getattr(current_user, "username", "admin")

    try:
        result = await source_1024_crawler_manager.run(
            db,
            trigger="manual",
            updated_by=updated_by,
        )
        return CrawlerRunResponse(**result.__dict__)
    except CrawlerAlreadyRunningError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Crawler is already running",
        ) from exc
    except CrawlerCoordinationUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Crawler coordination service is unavailable",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch source site: {exc}",
        ) from exc
