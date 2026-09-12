"""Audit middleware that persists explicit security and mutation events."""

import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from sqlalchemy.exc import IntegrityError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.audit_log import AuditAction, AuditLog
from app.models.user import User
from app.utils.logging import audit_logger
from app.utils.security import decode_access_token


logger = logging.getLogger(__name__)

AUDIT_EMAIL_MAX_LENGTH = 255
AUDIT_IP_MAX_LENGTH = 45
AUDIT_METHOD_MAX_LENGTH = 10
AUDIT_PATH_MAX_LENGTH = 500
# The database column is TEXT, but a cap prevents untrusted headers from
# turning one request into an unbounded audit record.
AUDIT_USER_AGENT_MAX_LENGTH = 1000


class AuditMiddleware(BaseHTTPMiddleware):
    """Persist auditable API actions without affecting request outcomes."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.enabled = settings.MONITOR_AUDIT

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process a request and persist its audit event when applicable."""
        if not self.enabled:
            return await call_next(request)

        action = self._determine_action(request.url.path, request.method)
        if action is None:
            return await call_next(request)

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            await self._record_event_safely(
                request=request,
                action=action,
                status_code=500,
                duration_ms=self._elapsed_ms(start_time),
            )
            raise

        await self._record_event_safely(
            request=request,
            action=action,
            status_code=response.status_code,
            duration_ms=self._elapsed_ms(start_time),
        )
        return response

    async def _record_event_safely(self, **event: object) -> None:
        """Contain every audit failure so observability cannot alter the API."""
        try:
            await self._record_event(**event)
        except Exception:
            logger.exception("Failed to record audit event")

    async def _record_event(
        self,
        *,
        request: Request,
        action: AuditAction,
        status_code: int,
        duration_ms: float,
    ) -> None:
        """Write one event through an isolated database session."""
        claimed_user_id, claimed_email = self._token_identity(request)
        claimed_email = self._truncate(claimed_email, AUDIT_EMAIL_MAX_LENGTH)
        client_ip = self._truncate(self._client_ip(request), AUDIT_IP_MAX_LENGTH)
        user_agent = self._truncate(
            request.headers.get("User-Agent"),
            AUDIT_USER_AGENT_MAX_LENGTH,
        )
        request_method = self._truncate(request.method.upper(), AUDIT_METHOD_MAX_LENGTH)
        request_path = self._truncate(request.url.path, AUDIT_PATH_MAX_LENGTH)
        success = status_code < 400
        audit_data = {
            "action": action.value,
            "user_id": claimed_user_id,
            "user_email": claimed_email,
            "ip": client_ip,
            "user_agent": user_agent,
            "method": request_method,
            "path": request_path,
            "success": success,
            "status_code": status_code,
            "duration_ms": duration_ms,
        }

        try:
            audit_logger.info(
                "%s %s",
                request_method,
                request_path,
                extra=audit_data,
            )
        except Exception:
            logger.exception("Failed to emit audit log")

        async with AsyncSessionLocal() as session:
            user_id, user_email = await self._validated_identity(
                session,
                claimed_user_id,
                claimed_email,
            )
            event_values = {
                "action": action,
                "user_email": user_email,
                "resource_type": self._resource_type(action),
                "ip_address": client_ip,
                "user_agent": user_agent,
                "request_method": request_method,
                "request_path": request_path,
                "success": success,
                "error_message": None if success else f"HTTP {status_code}",
                "details": {
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            }
            session.add(AuditLog(user_id=user_id, **event_values))
            try:
                await session.commit()
            except IntegrityError:
                if user_id is None:
                    raise
                # The user can be deleted between validation and commit. Retry
                # without the optional foreign key so the event is retained.
                await session.rollback()
                session.add(AuditLog(user_id=None, **event_values))
                await session.commit()

    @staticmethod
    async def _validated_identity(
        session,
        claimed_user_id: int | None,
        claimed_email: str | None,
    ) -> tuple[int | None, str | None]:
        """Resolve a token claim without allowing a stale ID to violate its FK."""
        if claimed_user_id is None:
            return None, claimed_email

        user = await session.get(User, claimed_user_id)
        if user is None:
            return None, claimed_email
        return user.id, AuditMiddleware._truncate(user.email, AUDIT_EMAIL_MAX_LENGTH)

    @staticmethod
    def _elapsed_ms(start_time: float) -> float:
        return round((time.perf_counter() - start_time) * 1000, 2)

    @staticmethod
    def _truncate(value: str | None, max_length: int) -> str | None:
        if value is None:
            return None
        return value[:max_length]

    @staticmethod
    def _client_ip(request: Request) -> str | None:
        # Proxy headers must be validated by the ASGI server's trusted-proxy
        # configuration. Reading X-Forwarded-For here would let any direct
        # client forge the security audit trail.
        return request.client.host if request.client else None

    @staticmethod
    def _token_identity(request: Request) -> tuple[int | None, str | None]:
        authorization = request.headers.get("Authorization", "")
        parts = authorization.split(maxsplit=1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None, None

        payload = decode_access_token(parts[1])
        if payload is None:
            return None, None

        subject = payload.get("sub")
        try:
            user_id = (
                int(subject)
                if subject is not None and not isinstance(subject, bool)
                else None
            )
        except (TypeError, ValueError):
            user_id = None

        email = payload.get("email")
        user_email = email if isinstance(email, str) else None
        return user_id, user_email

    @staticmethod
    def _resource_type(action: AuditAction) -> str | None:
        if action.name.startswith("RESOURCE_"):
            return "resource"
        if action.name.startswith("CATEGORY_"):
            return "category"
        if action.name.startswith("USER_"):
            return "user"
        if action.name.startswith("CONTACT_"):
            return "contact"
        return None

    @staticmethod
    def _determine_action(path: str, method: str) -> AuditAction | None:
        """Map only explicit auditable endpoints, excluding ordinary reads."""
        normalized_path = path.rstrip("/") or "/"
        method = method.upper()

        if method == "POST":
            if normalized_path.endswith(
                ("/auth/login", "/auth/user/login", "/auth/admin/login")
            ):
                return AuditAction.LOGIN
            if normalized_path.endswith(("/auth/register", "/auth/user/register")):
                return AuditAction.REGISTER
            if normalized_path.endswith("/auth/logout"):
                return AuditAction.LOGOUT
            if normalized_path.endswith("/auth/reset-password"):
                return AuditAction.PASSWORD_RESET
            if normalized_path.endswith("/bulk-import/resources"):
                return AuditAction.BULK_IMPORT
            if "/seo/" in normalized_path:
                return AuditAction.SEO_GENERATE

        if method == "GET" and normalized_path.endswith("/auth/verify-email"):
            return AuditAction.EMAIL_VERIFY

        path_parts = normalized_path.split("/")
        if "resources" in path_parts:
            if method == "POST" and normalized_path.endswith("/resources"):
                return AuditAction.RESOURCE_CREATE
            if method in {"PUT", "PATCH"}:
                return AuditAction.RESOURCE_UPDATE
            if method == "DELETE":
                return AuditAction.RESOURCE_DELETE
            if method == "POST" and normalized_path.endswith("/download"):
                return AuditAction.RESOURCE_DOWNLOAD

        if "categories" in path_parts:
            if method == "POST":
                return AuditAction.CATEGORY_CREATE
            if method in {"PUT", "PATCH"}:
                return AuditAction.CATEGORY_UPDATE
            if method == "DELETE":
                return AuditAction.CATEGORY_DELETE

        if "users" in path_parts:
            if method == "POST":
                return AuditAction.USER_CREATE
            if method in {"PUT", "PATCH"}:
                return AuditAction.USER_UPDATE
            if method == "DELETE":
                return AuditAction.USER_DELETE

        if "contacts" in path_parts:
            if method == "POST":
                return AuditAction.CONTACT_CREATE
            if method in {"PUT", "PATCH"}:
                return AuditAction.CONTACT_UPDATE
            if method == "DELETE":
                return AuditAction.CONTACT_DELETE

        if method in {"POST", "PUT", "PATCH"} and "settings" in path_parts:
            return AuditAction.CONFIG_UPDATE

        # These endpoints mutate security- or business-relevant state but do
        # not have a dedicated value in the existing database enum.
        other_write_segments = {
            "auth",
            "crawler",
            "faqs",
            "orders",
            "recharge",
            "recharge-packages",
            "signin",
            "wallets",
        }
        if method in {"POST", "PUT", "PATCH", "DELETE"} and not other_write_segments.isdisjoint(path_parts):
            return AuditAction.OTHER

        return None
