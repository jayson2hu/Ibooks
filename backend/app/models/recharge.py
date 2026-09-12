"""
Recharge package and order models.
"""
from datetime import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class RechargePaymentMethod(str, enum.Enum):
    """Recharge payment method."""
    ALIPAY = "alipay"
    WECHAT = "wechat"


class RechargeOrderStatus(str, enum.Enum):
    """Recharge order status."""
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    FAILED = "failed"


class RechargePackage(Base):
    """Configurable coin recharge package."""

    __tablename__ = "recharge_packages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    coins: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus_coins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class RechargeOrder(Base):
    """Recharge order paid by a third-party payment channel."""

    __tablename__ = "recharge_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recharge_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    package_id: Mapped[int | None] = mapped_column(ForeignKey("recharge_packages.id"), nullable=True, index=True)
    coins: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus_coins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[RechargePaymentMethod] = mapped_column(SQLEnum(RechargePaymentMethod), nullable=False)
    status: Mapped[RechargeOrderStatus] = mapped_column(
        SQLEnum(RechargeOrderStatus),
        default=RechargeOrderStatus.PENDING,
        nullable=False,
        index=True,
    )
    trade_no: Mapped[str | None] = mapped_column(String(128))
    payment_raw: Mapped[str | None] = mapped_column(Text)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    user: Mapped["User"] = relationship("User")
    package: Mapped[RechargePackage | None] = relationship("RechargePackage")
