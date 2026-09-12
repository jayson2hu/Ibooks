"""
FAQ (Frequently Asked Questions) model.
"""
from sqlalchemy import String, Text, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base
from app.utils.datetime_utils import utc_now


class FAQ(Base):
    """FAQ model for storing frequently asked questions and answers."""
    
    __tablename__ = "faqs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Content
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Display Control
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<FAQ(id={self.id}, category={self.category}, question={self.question[:30]}...)>"
