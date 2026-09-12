"""
Contact information model for displaying company/service contact details.
"""
from sqlalchemy import String, Text, Integer, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import enum
from app.database import Base
from app.utils.datetime_utils import utc_now


class ContactType(str, enum.Enum):
    """Contact information type."""
    WECHAT = "wechat"
    WECHAT_QR = "wechat_qr"
    QQ = "qq"
    QQ_GROUP = "qq_group"
    EMAIL = "email"
    PHONE = "phone"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    ADDRESS = "address"
    BUSINESS_HOURS = "business_hours"
    OTHER = "other"


class Contact(Base):
    """Contact information model."""
    
    __tablename__ = "contacts"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Contact Type
    type: Mapped[ContactType] = mapped_column(
        SQLEnum(ContactType),
        nullable=False,
        index=True
    )
    
    # Basic Information
    label: Mapped[str] = mapped_column(String(200), nullable=False)  # Display label
    value: Mapped[str] = mapped_column(Text, nullable=False)  # Contact value (ID, number, email, etc.)
    
    # For QR Codes
    qr_code_url: Mapped[str | None] = mapped_column(String(500))  # QR code image URL
    qr_code_path: Mapped[str | None] = mapped_column(String(500))  # Local path to QR code
    
    # Display Options
    icon: Mapped[str | None] = mapped_column(String(100))  # Icon class or URL
    color: Mapped[str | None] = mapped_column(String(50))  # Hex color code
    description: Mapped[str | None] = mapped_column(Text)  # Additional description
    
    # Behavior
    is_copyable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # Can copy value
    is_clickable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Is a link
    link_url: Mapped[str | None] = mapped_column(String(500))  # Click destination URL
    
    # Display Control
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Display Location (where to show this contact)
    show_in_header: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    show_in_footer: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_in_contact_page: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_in_sidebar: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, type={self.type}, label={self.label})>"
