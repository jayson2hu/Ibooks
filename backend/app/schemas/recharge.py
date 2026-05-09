"""
Pydantic schemas for recharge packages and orders.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.recharge import RechargeOrderStatus, RechargePaymentMethod
from app.schemas.user import UserResponse


class RechargePackageResponse(BaseModel):
    """Recharge package response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    coins: int
    bonus_coins: int
    amount: Decimal
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


class RechargeOrderCreate(BaseModel):
    """Create recharge order request."""
    package_id: int
    payment_method: RechargePaymentMethod = RechargePaymentMethod.ALIPAY


class RechargeOrderResponse(BaseModel):
    """Recharge order response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    recharge_no: str
    user_id: int
    package_id: Optional[int] = None
    coins: int
    bonus_coins: int
    amount: Decimal
    payment_method: RechargePaymentMethod
    status: RechargeOrderStatus
    trade_no: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    package: Optional[RechargePackageResponse] = None
    user: Optional[UserResponse] = None


class RechargeOrderListResponse(BaseModel):
    """Paginated recharge order response."""
    items: List[RechargeOrderResponse]
    total: int
    page: int
    page_size: int
    pages: int


class RechargePackageCreate(BaseModel):
    """Internal/admin recharge package create schema for later reuse."""
    name: str = Field(..., min_length=1, max_length=100)
    coins: int = Field(..., gt=0)
    bonus_coins: int = Field(default=0, ge=0)
    amount: Decimal = Field(..., gt=0)
    is_active: bool = True
    sort_order: int = 0


class RechargePackageUpdate(BaseModel):
    """Admin recharge package update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    coins: Optional[int] = Field(None, gt=0)
    bonus_coins: Optional[int] = Field(None, ge=0)
    amount: Optional[Decimal] = Field(None, gt=0)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
