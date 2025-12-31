"""
Category model for organizing resources.
"""
from sqlalchemy import String, Text, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List, Optional
from app.database import Base


class Category(Base):
    """Category model for resource organization."""
    
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic Information
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(250), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    
    # Hierarchy (for nested categories)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), index=True)
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children"
    )
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    
    # Display
    icon: Mapped[str | None] = mapped_column(String(100))  # Icon class or URL
    color: Mapped[str | None] = mapped_column(String(50))  # Hex color code
    cover_image_url: Mapped[str | None] = mapped_column(String(500))
    
    # SEO
    meta_title: Mapped[str | None] = mapped_column(String(200))
    meta_description: Mapped[str | None] = mapped_column(String(500))
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Sorting
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Statistics
    resource_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    resources: Mapped[List["Resource"]] = relationship(
        "Resource",
        back_populates="category",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name}, slug={self.slug})>"
