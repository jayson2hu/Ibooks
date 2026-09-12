"""
Recharge package and order endpoints.
"""
from decimal import Decimal, InvalidOperation
import json
from math import ceil
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.recharge import (
    RechargeOrder,
    RechargeOrderStatus,
    RechargePackage,
    RechargePaymentMethod,
)
from app.models.user import User
from app.models.wallet import CoinLedgerType
from app.schemas.recharge import (
    RechargeOrderCreate,
    RechargeOrderListResponse,
    RechargeOrderResponse,
    RechargePackageResponse,
)
from app.services.wallet import credit_wallet
from app.utils.alipay_client import get_alipay_client, get_alipay_gateway
from app.utils.datetime_utils import utc_now


router = APIRouter(prefix="/recharge", tags=["Recharge"])


class AlipayRechargeCreateRequest(BaseModel):
    """Request body for creating an Alipay recharge payment."""
    recharge_no: str


def generate_recharge_no() -> str:
    """Generate a unique recharge order number."""
    return f"RCH{utc_now():%Y%m%d%H%M%S}{secrets.token_hex(4).upper()}"


async def get_recharge_order_by_no(
    db: AsyncSession,
    recharge_no: str,
    *,
    for_update: bool = False,
) -> RechargeOrder | None:
    """Get recharge order by number with package loaded."""
    query = (
        select(RechargeOrder)
        .options(selectinload(RechargeOrder.package))
        .where(RechargeOrder.recharge_no == recharge_no)
    )
    if for_update:
        query = query.with_for_update()
    result = await db.execute(query)
    return result.scalar_one_or_none()


@router.get("/packages", response_model=list[RechargePackageResponse])
async def list_recharge_packages(db: AsyncSession = Depends(get_db)):
    """List active recharge packages for users."""
    result = await db.execute(
        select(RechargePackage)
        .where(RechargePackage.is_active)
        .order_by(RechargePackage.sort_order.desc(), RechargePackage.amount.asc(), RechargePackage.id.asc())
    )
    return result.scalars().all()


@router.post("/orders", response_model=RechargeOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_recharge_order(
    order_data: RechargeOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a pending recharge order from an active package."""
    if order_data.payment_method != RechargePaymentMethod.ALIPAY:
        raise HTTPException(
            status_code=422,
            detail="微信支付暂未开放，请使用支付宝",
        )

    result = await db.execute(
        select(RechargePackage).where(
            RechargePackage.id == order_data.package_id,
            RechargePackage.is_active,
        )
    )
    package = result.scalar_one_or_none()
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="充值套餐不存在或未启用",
        )

    if package.coins <= 0 or package.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="充值套餐配置无效",
        )

    recharge_order = RechargeOrder(
        recharge_no=generate_recharge_no(),
        user_id=current_user.id,
        package_id=package.id,
        coins=package.coins,
        bonus_coins=package.bonus_coins,
        amount=package.amount,
        payment_method=order_data.payment_method,
        status=RechargeOrderStatus.PENDING,
    )
    db.add(recharge_order)
    await db.commit()

    order = await get_recharge_order_by_no(db, recharge_order.recharge_no)
    return order


@router.get("/orders/my", response_model=RechargeOrderListResponse)
async def list_my_recharge_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List current user's recharge orders."""
    base_query = select(RechargeOrder).where(RechargeOrder.user_id == current_user.id)
    total = await db.scalar(select(func.count()).select_from(base_query.subquery()))
    query = (
        base_query
        .options(selectinload(RechargeOrder.package))
        .order_by(RechargeOrder.created_at.desc(), RechargeOrder.id.desc())
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


@router.get("/orders/{recharge_no}", response_model=RechargeOrderResponse)
async def get_recharge_order(
    recharge_no: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's recharge order detail."""
    order = await get_recharge_order_by_no(db, recharge_no)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="充值订单不存在",
        )
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看该充值订单",
        )
    return order


@router.patch("/orders/{recharge_no}/cancel", response_model=RechargeOrderResponse)
async def cancel_recharge_order(
    recharge_no: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel a pending recharge order."""
    order = await get_recharge_order_by_no(db, recharge_no, for_update=True)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="充值订单不存在",
        )
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权取消该充值订单",
        )
    if order.status != RechargeOrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅待支付充值订单可取消",
        )

    order.status = RechargeOrderStatus.CANCELLED
    await db.commit()
    await db.refresh(order)
    return await get_recharge_order_by_no(db, recharge_no)


@router.post("/alipay/create")
async def create_alipay_recharge_payment(
    request: AlipayRechargeCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an Alipay page-pay URL for a pending recharge order."""
    order = await get_recharge_order_by_no(db, request.recharge_no)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="充值订单不存在",
        )
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权支付该充值订单",
        )
    if order.payment_method != RechargePaymentMethod.ALIPAY:
        raise HTTPException(
            status_code=422,
            detail="充值订单支付渠道与支付宝不匹配",
        )
    if order.status != RechargeOrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅待支付充值订单可发起支付",
        )

    alipay = get_alipay_client()
    subject = order.package.name if order.package else "书币充值"
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=order.recharge_no,
        total_amount=str(order.amount),
        subject=subject,
        return_url=f"{settings.SITE_URL}/wallet?payment_return=alipay&recharge_no={order.recharge_no}",
        notify_url=f"{settings.API_PUBLIC_URL or settings.SITE_URL}/api/v1/recharge/alipay/notify",
    )

    return {
        "payment_url": f"{get_alipay_gateway()}?{order_string}",
        "recharge_no": order.recharge_no,
    }


@router.post("/alipay/notify", response_class=PlainTextResponse)
async def alipay_recharge_notify(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Alipay asynchronous notification for recharge orders."""
    form = await request.form()
    raw_payload = dict(form)
    payload = dict(raw_payload)
    signature = payload.pop("sign", None)

    if not signature:
        return "failure"

    alipay = get_alipay_client()
    if not alipay.verify(payload, signature):
        return "failure"

    recharge_no = payload.get("out_trade_no")
    trade_no = payload.get("trade_no")
    trade_status = payload.get("trade_status")

    if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        return "success"

    if not recharge_no or not trade_no:
        return "failure"

    if settings.ALIPAY_APP_ID and payload.get("app_id") != settings.ALIPAY_APP_ID:
        return "failure"

    try:
        paid_amount = Decimal(str(payload.get("total_amount"))).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return "failure"

    result = await db.execute(
        select(RechargeOrder)
        .where(RechargeOrder.recharge_no == recharge_no)
        .with_for_update()
    )
    order = result.scalar_one_or_none()
    if not order:
        return "failure"

    expected_amount = Decimal(str(order.amount)).quantize(Decimal("0.01"))
    if order.payment_method != RechargePaymentMethod.ALIPAY or paid_amount != expected_amount:
        return "failure"

    if order.status == RechargeOrderStatus.PAID:
        return "success" if order.trade_no == trade_no else "failure"

    order.status = RechargeOrderStatus.PAID
    order.trade_no = trade_no
    order.payment_raw = json.dumps(raw_payload, ensure_ascii=False)
    order.paid_at = utc_now()

    await credit_wallet(
        db,
        order.user_id,
        order.coins + order.bonus_coins,
        CoinLedgerType.RECHARGE,
        related_order_no=order.recharge_no,
        description="书币充值",
    )
    await db.commit()

    return "success"
