"""
Wallet and coin ledger models.
"""
from datetime import datetime
import enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CoinLedgerType(str, enum.Enum):
    """Coin ledger entry type."""
    RECHARGE = "recharge"
    PURCHASE = "purchase"
    REFUND = "refund"
    SIGNIN = "signin"
    ADMIN_ADJUST = "admin_adjust"


class Wallet(Base):
    """User wallet holding current coin balance."""

    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_recharged: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_spent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_rewarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship("User")
    ledger_entries: Mapped[list["CoinLedger"]] = relationship(
        "CoinLedger",
        back_populates="wallet",
    )


class CoinLedger(Base):
    """Immutable wallet balance change record."""

    __tablename__ = "coin_ledger"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    wallet_id: Mapped[int] = mapped_column(ForeignKey("wallets.id"), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[CoinLedgerType] = mapped_column(SQLEnum(CoinLedgerType), nullable=False, index=True)
    related_order_no: Mapped[str | None] = mapped_column(String(64), index=True)
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship("User")
    wallet: Mapped[Wallet] = relationship("Wallet", back_populates="ledger_entries")
