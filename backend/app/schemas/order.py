"""
Pydantic schemas for orders.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.order import OrderStatus, PaymentMethod
from app.schemas.resource import ResourceResponse
from app.schemas.user import UserResponse


class OrderCreate(BaseModel):
    """Schema for creating an order."""
    resource_id: int


class OrderResponse(BaseModel):
    """Schema for order responses."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_no: str
    user_id: int
    resource_id: int
    amount: Decimal
    coin_amount: int
    payment_method: Optional[PaymentMethod] = None
    status: OrderStatus
    trade_no: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    resource: Optional[ResourceResponse] = None
    user: Optional[UserResponse] = None


class OrderListResponse(BaseModel):
    """Schema for paginated order responses."""
    items: List[OrderResponse]
    total: int
    page: int
    page_size: int
    pages: int
