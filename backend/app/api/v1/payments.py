"""
Payment endpoints.
"""
from datetime import datetime
import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.order import Order, OrderStatus, PaymentMethod
from app.models.user import User
from app.utils.alipay_client import get_alipay_client, get_alipay_gateway


router = APIRouter(prefix="/payments", tags=["Payments"])


class AlipayCreateRequest(BaseModel):
    """Request body for creating an Alipay payment."""
    order_no: str


@router.post("/alipay/create")
async def create_alipay_payment(
    request: AlipayCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create an Alipay page-pay URL for a pending order."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.resource))
        .where(Order.order_no == request.order_no)
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be paid"
        )

    alipay = get_alipay_client()
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=order.order_no,
        total_amount=str(order.amount),
        subject=order.resource.title if order.resource else order.order_no,
        return_url=f"{settings.SITE_URL}/orders?payment_return=alipay&order_no={order.order_no}",
        notify_url=f"{settings.SITE_URL}/api/v1/payments/alipay/notify",
    )

    order.payment_method = PaymentMethod.ALIPAY
    await db.commit()

    return {
        "payment_url": f"{get_alipay_gateway()}?{order_string}",
        "order_no": order.order_no,
    }


@router.post("/alipay/notify", response_class=PlainTextResponse)
async def alipay_notify(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Handle Alipay asynchronous payment notification."""
    form = await request.form()
    payload = dict(form)
    signature = payload.pop("sign", None)

    if not signature:
        return "failure"

    alipay = get_alipay_client()
    if not alipay.verify(payload, signature):
        return "failure"

    order_no = payload.get("out_trade_no")
    trade_no = payload.get("trade_no")
    trade_status = payload.get("trade_status")

    if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        return "success"

    result = await db.execute(select(Order).where(Order.order_no == order_no))
    order = result.scalar_one_or_none()
    if not order:
        return "failure"

    order.status = OrderStatus.PAID
    order.payment_method = PaymentMethod.ALIPAY
    order.trade_no = trade_no
    order.payment_raw = json.dumps(dict(form), ensure_ascii=False)
    order.paid_at = datetime.utcnow()
    await db.commit()

    return "success"


@router.get("/alipay/return")
async def alipay_return():
    """Alipay synchronous return endpoint."""
    return {"message": "支付结果已提交，请返回订单页面查看状态"}
