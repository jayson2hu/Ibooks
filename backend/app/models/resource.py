"""
Resource model for digital products (eBooks, courses, documents).
"""
from sqlalchemy import String, Text, Numeric, Integer, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List
from app.database import Base


class Resource(Base):
    """Digital resource/product model."""
    
    __tablename__ = "resources"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Basic Information
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(600), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    excerpt: Mapped[str | None] = mapped_column(String(500))  # Short description for listing
    
    # Category and Tags
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), index=True)
    category: Mapped["Category"] = relationship("Category", back_populates="resources")
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)  # JSON array of tags
    
    # Pricing
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    coin_price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    original_price: Mapped[float | None] = mapped_column(Numeric(10, 2))  # For showing discounts
    is_free: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Cloud Storage Links
    cloud_link: Mapped[str | None] = mapped_column(Text)  # Main cloud storage link
    backup_links: Mapped[List[str]] = mapped_column(JSON, default=list)  # Backup links
    access_code: Mapped[str | None] = mapped_column(String(100))  # Cloud storage access code
    
    # Media
    cover_image_url: Mapped[str | None] = mapped_column(String(500))
    preview_images: Mapped[List[str]] = mapped_column(JSON, default=list)  # Multiple preview images
    
    # Resource Details
    file_size: Mapped[str | None] = mapped_column(String(50))  # e.g., "2.5 GB"
    file_format: Mapped[str | None] = mapped_column(String(100))  # e.g., "PDF, EPUB, MOBI"
    resource_type: Mapped[str | None] = mapped_column(String(50), index=True)  # eBook, course, document
    
    # SEO
    meta_title: Mapped[str | None] = mapped_column(String(200))
    meta_description: Mapped[str | None] = mapped_column(String(500))
    meta_keywords: Mapped[str | None] = mapped_column(String(500))
    
    # Status
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Statistics
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    download_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Sorting
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime)
    
    def __repr__(self) -> str:
        return f"<Resource(id={self.id}, title={self.title}, slug={self.slug})>"
