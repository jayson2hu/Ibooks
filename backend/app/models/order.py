"""
Order model for resource purchases.
"""
from datetime import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from app.models.resource import Resource
    from app.models.user import User


class OrderStatus(str, enum.Enum):
    """Order status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration."""
    ALIPAY = "alipay"
    WECHAT = "wechat"
    FREE = "free"
    COIN = "coin"


class Order(Base):
    """Order model for tracking resource purchases."""

    __tablename__ = "orders"
    __table_args__ = (
        Index(
            "uq_orders_paid_user_resource",
            "user_id",
            "resource_id",
            unique=True,
            postgresql_where=text("status = 'PAID'"),
            sqlite_where=text("status = 'PAID'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    resource_id: Mapped[int] = mapped_column(ForeignKey("resources.id"), nullable=False, index=True)

    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    coin_amount: Mapped[int] = mapped_column(default=0, nullable=False)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(SQLEnum(PaymentMethod))
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True
    )

    trade_no: Mapped[str | None] = mapped_column(String(128))
    payment_raw: Mapped[str | None] = mapped_column(Text)

    paid_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )

    user: Mapped["User"] = relationship("User")
    resource: Mapped["Resource"] = relationship("Resource")
