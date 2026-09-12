"""
Resource model for digital products (eBooks, courses, documents).
"""
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import TYPE_CHECKING, List
from app.database import Base
from app.utils.datetime_utils import utc_now

if TYPE_CHECKING:
    from app.models.category import Category


class Resource(Base):
    """Digital resource/product model."""

    __tablename__ = "resources"
    __table_args__ = (
        Index(
            "uq_resources_source_site_external_id",
            "source_site",
            "source_external_id",
            unique=True,
            postgresql_where=text(
                "source_site IS NOT NULL AND source_external_id IS NOT NULL"
            ),
            sqlite_where=text(
                "source_site IS NOT NULL AND source_external_id IS NOT NULL"
            ),
        ),
        Index(
            "uq_resources_source_url",
            "source_url",
            unique=True,
            postgresql_where=text("source_url IS NOT NULL"),
            sqlite_where=text("source_url IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Basic Information
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(600), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    excerpt: Mapped[str | None] = mapped_column(String(500))  # Short description for listing

    # Category and Tags
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "categories.id",
            name="fk_resources_category_id_categories",
            ondelete="RESTRICT",
        ),
        index=True,
    )
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

    # External Source Metadata
    source_type: Mapped[str | None] = mapped_column(String(32), index=True)
    source_site: Mapped[str | None] = mapped_column(String(100), index=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    source_external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    source_last_synced_at: Mapped[datetime | None] = mapped_column(DateTime)

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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return f"<Resource(id={self.id}, title={self.title}, slug={self.slug})>"
