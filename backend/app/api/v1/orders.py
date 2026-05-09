"""
Order endpoints.
"""
from datetime import datetime
from math import ceil
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.resource import Resource
from app.models.user import User, UserRole
from app.schemas.common import Message
from app.schemas.order import OrderCreate, OrderListResponse, OrderResponse
from app.models.wallet import CoinLedgerType
from app.services.wallet import debit_wallet


router = APIRouter(prefix="/orders", tags=["Orders"])


def generate_order_no() -> str:
    """Generate a unique order number."""
    return f"ORD{datetime.utcnow():%Y%m%d%H%M%S}{secrets.token_hex(4).upper()}"


async def get_order_by_no(
    db: AsyncSession,
    order_no: str,
    include_user: bool = False
) -> Order | None:
    """Get an order by order number."""
    options = [selectinload(Order.resource)]
    if include_user:
        options.append(selectinload(Order.user))

    result = await db.execute(
        select(Order)
        .options(*options)
        .where(Order.order_no == order_no)
    )
    return result.scalar_one_or_none()


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create an order for the current user."""
    result = await db.execute(
        select(Resource).where(
            Resource.id == order_data.resource_id,
            Resource.is_published == True
        )
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )

    existing_paid = await db.execute(
        select(Order).where(
            Order.user_id == current_user.id,
            Order.resource_id == resource.id,
            Order.status == OrderStatus.PAID
        )
    )
    if existing_paid.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resource already purchased"
        )

    is_free = resource.is_free or resource.coin_price == 0
    coin_amount = 0 if is_free else resource.coin_price
    new_order = Order(
        order_no=generate_order_no(),
        user_id=current_user.id,
        resource_id=resource.id,
        amount=resource.price,
        coin_amount=coin_amount,
        payment_method=PaymentMethod.FREE if is_free else PaymentMethod.COIN,
        status=OrderStatus.PAID,
        paid_at=datetime.utcnow(),
    )

    db.add(new_order)
    await db.flush()

    if not is_free:
        await debit_wallet(
            db,
            current_user.id,
            coin_amount,
            CoinLedgerType.PURCHASE,
            related_order_no=new_order.order_no,
            description=f"购买资源：{resource.title}",
        )

    await db.commit()

    order = await get_order_by_no(db, new_order.order_no)
    return order


@router.get("/my", response_model=OrderListResponse)
async def list_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List orders for the current user."""
    base_query = select(Order).where(Order.user_id == current_user.id)
    total = await db.scalar(select(func.count()).select_from(base_query.subquery()))

    query = (
        base_query
        .options(selectinload(Order.resource))
        .order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    orders = result.scalars().all()

    return {
        "items": orders,
        "total": total or 0,
        "page": page,
        "page_size": page_size,
        "pages": ceil((total or 0) / page_size) if total else 0,
    }


@router.get("", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: OrderStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all orders. Admin only."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    base_query = select(Order)
    if status_filter:
        base_query = base_query.where(Order.status == status_filter)

    total = await db.scalar(select(func.count()).select_from(base_query.subquery()))
    query = (
        base_query
        .options(selectinload(Order.resource), selectinload(Order.user))
        .order_by(Order.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    orders = result.scalars().all()

    return {
        "items": orders,
        "total": total or 0,
        "page": page,
        "page_size": page_size,
        "pages": ceil((total or 0) / page_size) if total else 0,
    }


@router.get("/{order_no}", response_model=OrderResponse)
async def get_order(
    order_no: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get order detail by order number."""
    order = await get_order_by_no(db, order_no, include_user=current_user.role == UserRole.ADMIN)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    return order


@router.patch("/{order_no}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_no: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a pending order."""
    order = await get_order_by_no(db, order_no)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be cancelled"
        )

    order.status = OrderStatus.CANCELLED
    await db.commit()

    updated_order = await get_order_by_no(db, order_no)
    return updated_order
