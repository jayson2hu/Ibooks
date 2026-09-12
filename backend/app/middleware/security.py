"""
Security middleware for rate limiting and CSRF protection.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
import secrets
from app.schemas.responses import error_response
from app.utils.datetime_utils import utc_now
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse.

    Implements token bucket algorithm with per-IP rate limiting.
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.buckets: Dict[str, list] = defaultdict(list)
        # Different limits for different endpoints
        self.endpoint_limits = {
            "/api/v1/auth/user/login": 5,  # 5 attempts per minute
            "/api/v1/auth/admin/login": 3,  # 3 attempts per minute
            "/api/v1/auth/user/register": 10,  # 10 registrations per minute
            "/api/v1/search": 30,  # 30 searches per minute
        }

    async def dispatch(self, request: Request, call_next):
        """Check rate limit and process request."""
        # Don't rate limit health checks and metrics
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Determine rate limit for this endpoint
        limit = self.requests_per_minute
        for endpoint_pattern, endpoint_limit in self.endpoint_limits.items():
            if request.url.path.startswith(endpoint_pattern):
                limit = endpoint_limit
                break

        # Check rate limit
        now = utc_now()
        bucket = self.buckets[client_ip]

        # Remove old entries (older than 1 minute)
        bucket[:] = [ts for ts in bucket if now - ts < timedelta(minutes=1)]

        if len(bucket) >= limit:
            logger.warning(
                f"Rate limit exceeded for IP {client_ip} on {request.url.path}"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_response(
                    message="Rate limit exceeded. Too many requests.",
                    code=429,
                ).dict()
            )

        # Add current request to bucket
        bucket.append(now)

        # Continue processing
        response = await call_next(request)

        # Add rate limit headers
        remaining = limit - len(bucket)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(
            int((now + timedelta(minutes=1)).timestamp())
        )

        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware.

    Validates CSRF tokens for state-changing requests (POST, PUT, PATCH, DELETE).
    """

    def __init__(self, app):
        super().__init__(app)
        self.csrf_tokens: Dict[str, Tuple[str, datetime]] = {}
        self.token_expiry_minutes = 1440  # 24 hours

    def _generate_token(self) -> str:
        """Generate a new CSRF token."""
        return secrets.token_urlsafe(32)

    def _is_token_expired(self, token: str) -> bool:
        """Check if CSRF token is expired."""
        if token not in self.csrf_tokens:
            return True

        _, created_at = self.csrf_tokens[token]
        expiry_time = created_at + timedelta(minutes=self.token_expiry_minutes)
        return utc_now() > expiry_time

    async def dispatch(self, request: Request, call_next):
        """Check CSRF token for state-changing requests."""
        # Skip CSRF check for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            response = await call_next(request)

            # Generate and include CSRF token in response headers
            token = self._generate_token()
            self.csrf_tokens[token] = (token, utc_now())

            response.headers["X-CSRF-Token"] = token
            return response

        # For state-changing requests, verify CSRF token
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            # Get CSRF token from request
            csrf_token = request.headers.get("X-CSRF-Token") or await request.form().get(
                "csrf_token"
            )

            if not csrf_token:
                logger.warning(f"Missing CSRF token for {request.method} {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content=error_response(
                        message="CSRF token missing or invalid",
                        code=403,
                    ).dict()
                )

            # Verify token
            if self._is_token_expired(csrf_token):
                logger.warning(f"Invalid or expired CSRF token for {request.url.path}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content=error_response(
                        message="CSRF token expired",
                        code=403,
                    ).dict()
                )

            # Remove used token (one-time use)
            del self.csrf_tokens[csrf_token]

        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        """Add security headers."""
        response = await call_next(request)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        response.headers[
            "Content-Security-Policy"
        ] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Feature Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response
