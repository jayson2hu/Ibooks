"""
Site settings management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.models.site_settings import SiteSetting
from app.schemas.site_settings import (
    SiteSettingResponse,
    SiteSettingUpdate,
    SiteSettingsBatchUpdate,
    SiteSettingsGroup
)
from app.schemas.common import Message


router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=List[SiteSettingResponse])
async def get_public_settings(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get public site settings (no authentication required).
    
    Only returns settings from 'footer', 'general', and 'appearance' categories.
    """
    query = select(SiteSetting).where(
        SiteSetting.category.in_(["footer", "general", "appearance"])
    )
    
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


@router.get("/{key}", response_model=SiteSettingResponse)
async def get_setting(
    key: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific setting by key.
    
    Public settings only (footer, general, appearance categories).
    """
    result = await db.execute(
        select(SiteSetting).where(
            SiteSetting.key == key,
            SiteSetting.category.in_(["footer", "general", "appearance"])
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
    current_user = Depends(get_current_admin)
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
    
    # Update setting
    setting.value = setting_update.value
    if setting_update.updated_by:
        setting.updated_by = setting_update.updated_by
    elif hasattr(current_user, 'username'):
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
        
        if not key or value is None:
            continue
        
        result = await db.execute(
            select(SiteSetting).where(SiteSetting.key == key)
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
            if hasattr(current_user, 'username'):
                setting.updated_by = current_user.username
            updated_count += 1
    
    await db.commit()
    
    return {"message": f"Successfully updated {updated_count} settings"}
