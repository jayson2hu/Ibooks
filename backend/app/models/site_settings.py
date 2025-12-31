"""
Site settings model for storing system-wide configuration.
"""
from datetime import datetime
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class SiteSetting(Base):
    """Site-wide configuration settings."""
    
    __tablename__ = "site_settings"
    
    # Primary Key
    key: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    
    # Setting Details
    value: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True, default="general")
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Metadata
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        nullable=False
    )
    updated_by: Mapped[str] = mapped_column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<SiteSetting(key={self.key}, category={self.category})>"
