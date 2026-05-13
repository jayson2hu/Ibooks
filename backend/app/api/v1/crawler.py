"""
Crawler management endpoints.
"""
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_admin
from app.schemas.crawler import CrawlerRunResponse, CrawlerStatusResponse
from app.services.crawler_service import source_1024_crawler_manager


router = APIRouter(prefix="/crawler", tags=["Crawler"])


@router.get("/1024/status", response_model=CrawlerStatusResponse)
async def get_1024_crawler_status(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Get crawler runtime status and effective settings."""
    return await source_1024_crawler_manager.get_status(db)


@router.post("/1024/run", response_model=CrawlerRunResponse)
async def run_1024_crawler(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
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
