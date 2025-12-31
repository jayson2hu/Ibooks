"""
Admin endpoints for user management and statistics.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from math import ceil
from app.database import get_db
from app.dependencies import get_current_admin
from app.schemas.user import UserResponse, UserUpdateAdmin
from app.models.user import User
from app.models.resource import Resource
from app.models.category import Category
from app.models.audit_log import AuditLog


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """
    Get platform statistics (Admin only).
    
    Returns counts for users, resources, categories, etc.
    """
    # Get counts
    user_count = await db.scalar(select(func.count()).select_from(User))
    resource_count = await db.scalar(select(func.count()).select_from(Resource))
    category_count = await db.scalar(select(func.count()).select_from(Category))
    published_resources = await db.scalar(
        select(func.count()).select_from(Resource).where(Resource.is_published == True)
    )
    
    # Get total views
    total_views = await db.scalar(select(func.sum(Resource.view_count)))
    total_downloads = await db.scalar(select(func.sum(Resource.download_count)))
    
    return {
        "users": user_count or 0,
        "resources": resource_count or 0,
        "published_resources": published_resources or 0,
        "categories": category_count or 0,
        "total_views": total_views or 0,
        "total_downloads": total_downloads or 0
    }


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """List all users (Admin only)."""
    query = select(User).order_by(User.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    users = result.scalars().all()
    
    return users


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdateAdmin,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Update user (Admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return user


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Get audit logs (Admin only)."""
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    
    if action:
        query = query.where(AuditLog.action == action)
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "items": [
            {
                "id": log.id,
                "action": log.action.value,
                "user_id": log.user_id,
                "user_email": log.user_email,
                "ip_address": log.ip_address,
                "success": log.success,
                "created_at": log.created_at,
                "details": log.details
            }
            for log in logs
        ],
        "total": total or 0,
        "page": page,
        "page_size": page_size,
        "pages": ceil(total / page_size) if total and total > 0 else 0
    }
