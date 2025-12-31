"""
Audit log model for tracking user actions and security events.
"""
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import enum
from app.database import Base


class AuditAction(str, enum.Enum):
    """Audit action types."""
    # Authentication
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"
    PASSWORD_RESET = "password_reset"
    EMAIL_VERIFY = "email_verify"
    
    # Resource Management
    RESOURCE_CREATE = "resource_create"
    RESOURCE_UPDATE = "resource_update"
    RESOURCE_DELETE = "resource_delete"
    RESOURCE_VIEW = "resource_view"
    RESOURCE_DOWNLOAD = "resource_download"
    
    # Category Management
    CATEGORY_CREATE = "category_create"
    CATEGORY_UPDATE = "category_update"
    CATEGORY_DELETE = "category_delete"
    
    # User Management
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    USER_SUSPEND = "user_suspend"
    USER_ACTIVATE = "user_activate"
    
    # Contact Management
    CONTACT_CREATE = "contact_create"
    CONTACT_UPDATE = "contact_update"
    CONTACT_DELETE = "contact_delete"
    
    # System
    CONFIG_UPDATE = "config_update"
    BULK_IMPORT = "bulk_import"
    SEO_GENERATE = "seo_generate"
    
    # Other
    OTHER = "other"


class AuditLog(Base):
    """Audit log for tracking user actions and security events."""
    
    __tablename__ = "audit_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Action Information
    action: Mapped[AuditAction] = mapped_column(
        SQLEnum(AuditAction),
        nullable=False,
        index=True
    )
    resource_type: Mapped[str | None] = mapped_column(String(100), index=True)  # e.g., "resource", "user"
    resource_id: Mapped[int | None] = mapped_column(Integer, index=True)  # ID of affected resource
    
    # User Information
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    user_email: Mapped[str | None] = mapped_column(String(255))
    
    # Request Information
    ip_address: Mapped[str | None] = mapped_column(String(45), index=True)  # IPv4 or IPv6
    user_agent: Mapped[str | None] = mapped_column(Text)
    request_method: Mapped[str | None] = mapped_column(String(10))  # GET, POST, etc.
    request_path: Mapped[str | None] = mapped_column(String(500))
    
    # Status
    success: Mapped[bool] = mapped_column(default=True, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    
    # Additional Details (JSON)
    details: Mapped[dict] = mapped_column(JSON, default=dict)  # Additional context
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id}, ip={self.ip_address})>"
