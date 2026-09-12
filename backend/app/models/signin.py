"""
Daily sign-in model.
"""
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class DailySignin(Base):
    """One daily coin reward claim per user."""

    __tablename__ = "daily_signins"
    __table_args__ = (
        UniqueConstraint("user_id", "signin_date", name="uq_daily_signins_user_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    signin_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reward_coins: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)

    user: Mapped["User"] = relationship("User")
