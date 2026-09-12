"""
Async audit logging system using background tasks.
Decouples audit logging from request processing for better performance.
"""
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog, AuditAction
from app.utils.datetime_utils import utc_now
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Thread pool for background tasks
_executor = ThreadPoolExecutor(max_workers=5)


async def log_audit_event(
    db: AsyncSession,
    action: AuditAction,
    user_id: Optional[int] = None,
    user_email: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_method: Optional[str] = None,
    request_path: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """
    Log an audit event asynchronously.

    This function creates an audit log entry for tracking user actions.
    Called from request handlers without blocking the response.

    Args:
        db: Database session
        action: Action being audited (e.g., LOGIN, CREATE_RESOURCE)
        user_id: ID of user performing action
        user_email: Email of user performing action
        resource_type: Type of resource being acted upon
        resource_id: ID of resource being acted upon
        ip_address: Client IP address
        user_agent: Client user agent
        request_method: HTTP method
        request_path: Request path
        success: Whether action succeeded
        error_message: Error message if failed
        details: Additional details as dict

    Returns:
        Created AuditLog object
    """
    try:
        audit_log = AuditLog(
            action=action,
            user_id=user_id,
            user_email=user_email,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            success=success,
            error_message=error_message,
            details=details or {},
            created_at=utc_now(),
        )

        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)

        logger.debug(f"Audit logged: {action} for user {user_id}")
        return audit_log

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to log audit event: {str(e)}", exc_info=True)
        # Don't raise - audit logging should not break the application
        return None


async def log_user_action(
    db: AsyncSession,
    action: AuditAction,
    user_id: int,
    user_email: str,
    ip_address: str,
    user_agent: str,
    request_method: str,
    request_path: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[int] = None,
    success: bool = True,
    error_message: Optional[str] = None,
) -> None:
    """Log a user action asynchronously without blocking request."""
    # Schedule audit logging as background task
    asyncio.create_task(
        log_audit_event(
            db=db,
            action=action,
            user_id=user_id,
            user_email=user_email,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_path=request_path,
            success=success,
            error_message=error_message,
        )
    )


async def bulk_log_audit_events(
    db: AsyncSession,
    events: list[Dict[str, Any]],
) -> int:
    """
    Log multiple audit events in a single batch.

    Useful for bulk operations that need to log multiple actions.

    Args:
        db: Database session
        events: List of event dicts with parameters for log_audit_event

    Returns:
        Number of events logged successfully
    """
    logged_count = 0

    for event_data in events:
        try:
            await log_audit_event(db, **event_data)
            logged_count += 1
        except Exception as e:
            logger.error(f"Failed to log event: {str(e)}")
            continue

    return logged_count


async def get_audit_logs(
    db: AsyncSession,
    user_id: Optional[int] = None,
    action: Optional[AuditAction] = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    """
    Retrieve audit logs with filtering.

    Args:
        db: Database session
        user_id: Filter by user ID
        action: Filter by action type
        limit: Maximum number of logs to return
        offset: Number of logs to skip

    Returns:
        Tuple of (logs list, total count)
    """
    from sqlalchemy import select, func

    query = select(AuditLog)

    if user_id:
        query = query.where(AuditLog.user_id == user_id)

    if action:
        query = query.where(AuditLog.action == action)

    # Get total count
    count_query = select(func.count()).select_from(AuditLog)
    if user_id:
        count_query = count_query.where(AuditLog.user_id == user_id)
    if action:
        count_query = count_query.where(AuditLog.action == action)

    total = await db.scalar(count_query)

    # Get paginated results
    query = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    logs = result.scalars().all()

    return logs, total


# Convenience functions for common audit events

async def audit_login(
    db: AsyncSession,
    user_id: int,
    user_email: str,
    ip_address: str,
    user_agent: str,
    success: bool = True,
    error_message: Optional[str] = None,
) -> None:
    """Log user login event."""
    await log_user_action(
        db=db,
        action=AuditAction.LOGIN,
        user_id=user_id,
        user_email=user_email,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method="POST",
        request_path="/api/v1/auth/login",
        success=success,
        error_message=error_message,
    )


async def audit_resource_action(
    db: AsyncSession,
    action: AuditAction,
    user_id: int,
    user_email: str,
    resource_id: int,
    ip_address: str,
    user_agent: str,
    success: bool = True,
    error_message: Optional[str] = None,
) -> None:
    """Log resource-related action."""
    await log_user_action(
        db=db,
        action=action,
        user_id=user_id,
        user_email=user_email,
        resource_type="resource",
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        request_method="POST",
        request_path="/api/v1/resources",
        success=success,
        error_message=error_message,
    )
