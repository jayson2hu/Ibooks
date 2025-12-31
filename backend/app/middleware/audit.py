"""
Audit logging middleware for tracking user actions and security events.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
import time
from app.config import settings
from app.utils.logging import audit_logger
from app.models.audit_log import AuditAction


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware for audit logging."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.enabled = settings.MONITOR_AUDIT
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log audit trail."""
        if not self.enabled:
            return await call_next(request)
        
        # Get client IP (handle proxy headers)
        client_ip = request.client.host if request.client else None
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        # Get user agent
        user_agent = request.headers.get("User-Agent", "")
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log audit information
        audit_data = {
            "path": request.url.path,
            "method": request.method,
            "ip": client_ip,
            "user_agent": user_agent,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        }
        
        # Get user from request state if authenticated
        if hasattr(request.state, "user"):
            audit_data["user_id"] = request.state.user.id
            audit_data["user_email"] = request.state.user.email
        
        # Determine action type based on path and method
        action = self._determine_action(request.url.path, request.method)
        if action:
            audit_data["action"] = action
        
        # Log to audit logger
        audit_logger.info(
            f"{request.method} {request.url.path}",
            extra=audit_data
        )
        
        return response
    
    def _determine_action(self, path: str, method: str) -> str:
        """Determine audit action from request path and method."""
        # Authentication endpoints
        if "/auth/login" in path:
            return AuditAction.LOGIN.value
        elif "/auth/logout" in path:
            return AuditAction.LOGOUT.value
        elif "/auth/register" in path:
            return AuditAction.REGISTER.value
        
        # Resource endpoints
        if "/resources" in path:
            if method == "POST":
                return AuditAction.RESOURCE_CREATE.value
            elif method == "PUT" or method == "PATCH":
                return AuditAction.RESOURCE_UPDATE.value
            elif method == "DELETE":
                return AuditAction.RESOURCE_DELETE.value
            elif method == "GET":
                return AuditAction.RESOURCE_VIEW.value
        
        # Category endpoints
        if "/categories" in path:
            if method == "POST":
                return AuditAction.CATEGORY_CREATE.value
            elif method == "PUT" or method == "PATCH":
                return AuditAction.CATEGORY_UPDATE.value
            elif method == "DELETE":
                return AuditAction.CATEGORY_DELETE.value
        
        # User management endpoints
        if "/users" in path:
            if method == "POST":
                return AuditAction.USER_CREATE.value
            elif method == "PUT" or method == "PATCH":
                return AuditAction.USER_UPDATE.value
            elif method == "DELETE":
                return AuditAction.USER_DELETE.value
        
        return None
