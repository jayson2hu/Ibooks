"""
Admin endpoints for user management and statistics.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from math import ceil
from app.database import get_db
from app.dependencies import get_current_admin, get_current_staff
from app.models.recharge import RechargeOrder, RechargeOrderStatus, RechargePackage
from app.schemas.user import UserResponse, UserUpdateAdmin
from app.schemas.common import PaginatedResponse
from app.schemas.resource import AdminResourceResponse, ResourceListResponse
from app.schemas.recharge import (
    RechargeOrderListResponse,
    RechargePackageCreate,
    RechargePackageResponse,
    RechargePackageUpdate,
)
from app.schemas.wallet import (
    AdminCoinLedgerListResponse,
    AdminWalletListResponse,
    WalletAdjustRequest,
    WalletResponse,
)
from app.models.user import User
from app.models.resource import Resource
from app.models.category import Category
from app.models.audit_log import AuditAction, AuditLog
from app.models.site_settings import SiteSetting
from app.models.wallet import CoinLedger, CoinLedgerType, Wallet
from app.services.site_settings import (
    SIGNIN_CATEGORY,
    SIGNIN_ENABLED_KEY,
    SIGNIN_REWARD_COINS_KEY,
)
from app.services.wallet import credit_wallet, debit_wallet


router = APIRouter(prefix="/admin", tags=["Admin"])


def paginated_response(items, total: int, page: int, page_size: int) -> dict:
    """Build the project's common paginated response shape."""
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": ceil(total / page_size) if total > 0 else 0,
    }


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_staff)
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
        select(func.count()).select_from(Resource).where(Resource.is_published)
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


@router.get("/resources", response_model=ResourceListResponse)
async def list_resources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, max_length=500),
    category_id: Optional[int] = Query(None, ge=1),
    is_published: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_staff),
):
    """List published and draft resources for content administration."""
    query = select(Resource)

    if category_id is not None:
        query = query.where(Resource.category_id == category_id)
    if is_published is not None:
        query = query.where(Resource.is_published == is_published)
    if search and (search_term := search.strip()):
        keyword = f"%{search_term}%"
        query = query.where(
            or_(
                Resource.title.ilike(keyword),
                Resource.description.ilike(keyword),
                Resource.excerpt.ilike(keyword),
            )
        )

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(
        query
        .order_by(
            Resource.sort_order.desc(),
            Resource.created_at.desc(),
            Resource.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return paginated_response(result.scalars().all(), total or 0, page, page_size)


@router.get("/resources/{resource_id}", response_model=AdminResourceResponse)
async def get_resource(
    resource_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_staff),
):
    """Get a resource by ID for administration, including delivery fields."""
    resource = await db.get(Resource, resource_id)
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found",
        )
    return resource


@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """Return the only user-list contract: a paginated response object."""
    query = select(User).order_by(User.created_at.desc(), User.id.desc())
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(
        query.offset((page - 1) * page_size).limit(page_size)
    )

    return paginated_response(
        result.scalars().all(),
        total or 0,
        page,
        page_size,
    )


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
    action: Optional[AuditAction] = Query(None),
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


@router.get("/wallets", response_model=AdminWalletListResponse)
async def list_wallets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """List user wallets with optional email/username search."""
    query = select(Wallet).options(selectinload(Wallet.user)).join(User)

    if search:
        keyword = f"%{search.strip()}%"
        query = query.where(or_(User.email.ilike(keyword), User.username.ilike(keyword)))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(
        query
        .order_by(Wallet.updated_at.desc(), Wallet.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return paginated_response(result.scalars().all(), total or 0, page, page_size)


@router.get("/coin-ledger", response_model=AdminCoinLedgerListResponse)
async def list_coin_ledger(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[CoinLedgerType] = None,
    user_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """List all coin ledger entries with filters."""
    query = select(CoinLedger).options(selectinload(CoinLedger.user))

    if type:
        query = query.where(CoinLedger.type == type)
    if user_id:
        query = query.where(CoinLedger.user_id == user_id)
    if start_date:
        query = query.where(CoinLedger.created_at >= start_date)
    if end_date:
        query = query.where(CoinLedger.created_at <= end_date)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(
        query
        .order_by(CoinLedger.created_at.desc(), CoinLedger.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return paginated_response(result.scalars().all(), total or 0, page, page_size)


@router.post("/wallets/{user_id}/adjust", response_model=WalletResponse)
async def adjust_wallet(
    user_id: int,
    request: WalletAdjustRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """Manually add or deduct coins from a user wallet."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if request.amount == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="调整金额不能为 0",
        )

    description = request.description or f"后台调整：{current_user.username}"
    if request.amount > 0:
        wallet, _ = await credit_wallet(
            db,
            user_id,
            request.amount,
            CoinLedgerType.ADMIN_ADJUST,
            description=description,
        )
    else:
        wallet, _ = await debit_wallet(
            db,
            user_id,
            abs(request.amount),
            CoinLedgerType.ADMIN_ADJUST,
            description=description,
        )

    await db.commit()
    await db.refresh(wallet)
    return wallet


@router.get("/recharge-orders", response_model=RechargeOrderListResponse)
async def list_recharge_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[RechargeOrderStatus] = Query(None, alias="status"),
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """List all recharge orders."""
    query = select(RechargeOrder).options(
        selectinload(RechargeOrder.package),
        selectinload(RechargeOrder.user),
    )
    if status_filter:
        query = query.where(RechargeOrder.status == status_filter)
    if user_id:
        query = query.where(RechargeOrder.user_id == user_id)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(
        query
        .order_by(RechargeOrder.created_at.desc(), RechargeOrder.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return paginated_response(result.scalars().all(), total or 0, page, page_size)


@router.get("/recharge-packages", response_model=List[RechargePackageResponse])
async def list_recharge_packages(
    include_inactive: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """List recharge packages for admin management."""
    query = select(RechargePackage)
    if not include_inactive:
        query = query.where(RechargePackage.is_active)
    result = await db.execute(
        query.order_by(RechargePackage.sort_order.desc(), RechargePackage.amount.asc(), RechargePackage.id.asc())
    )
    return result.scalars().all()


@router.post("/recharge-packages", response_model=RechargePackageResponse, status_code=status.HTTP_201_CREATED)
async def create_recharge_package(
    package_data: RechargePackageCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """Create a recharge package."""
    package = RechargePackage(**package_data.model_dump())
    db.add(package)
    await db.commit()
    await db.refresh(package)
    return package


@router.patch("/recharge-packages/{package_id}", response_model=RechargePackageResponse)
async def update_recharge_package(
    package_id: int,
    package_data: RechargePackageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """Update a recharge package."""
    package = await db.get(RechargePackage, package_id)
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recharge package not found",
        )

    for field, value in package_data.model_dump(exclude_unset=True).items():
        setattr(package, field, value)

    await db.commit()
    await db.refresh(package)
    return package


@router.get("/settings/signin")
async def get_signin_settings(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """Get sign-in feature settings."""
    result = await db.execute(
        select(SiteSetting).where(
            SiteSetting.key.in_([SIGNIN_ENABLED_KEY, SIGNIN_REWARD_COINS_KEY])
        )
    )
    settings = {setting.key: setting for setting in result.scalars().all()}
    return {
        "enabled": settings.get(SIGNIN_ENABLED_KEY).value.lower() == "true"
        if settings.get(SIGNIN_ENABLED_KEY) else False,
        "reward_coins": int(settings.get(SIGNIN_REWARD_COINS_KEY).value)
        if settings.get(SIGNIN_REWARD_COINS_KEY) else 5,
    }


@router.put("/settings/signin")
async def update_signin_settings(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_admin),
):
    """Update sign-in feature settings."""
    enabled = bool(payload.get("enabled", False))
    try:
        reward_coins = int(payload.get("reward_coins", 5))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="签到奖励币数必须为正整数",
        )
    if reward_coins <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="签到奖励币数必须为正整数",
        )

    values = {
        SIGNIN_ENABLED_KEY: "true" if enabled else "false",
        SIGNIN_REWARD_COINS_KEY: str(reward_coins),
    }
    for key, value in values.items():
        result = await db.execute(select(SiteSetting).where(SiteSetting.key == key))
        setting = result.scalar_one_or_none()
        if setting:
            setting.value = value
            setting.updated_by = current_user.username
        else:
            db.add(SiteSetting(
                key=key,
                value=value,
                category=SIGNIN_CATEGORY,
                updated_by=current_user.username,
            ))

    await db.commit()
    return {"enabled": enabled, "reward_coins": reward_coins}
