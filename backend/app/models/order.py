"""
Order model for resource purchases.
"""
from datetime import datetime
import enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    user: Mapped["User"] = relationship("User")
    resource: Mapped["Resource"] = relationship("Resource")
