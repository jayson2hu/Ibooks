"""
Performance tracking middleware for monitoring API response times.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
import time
from app.config import settings
from app.utils.logging import access_logger, performance_logger
from app.utils.metrics import request_count, request_duration


UNMATCHED_ROUTE_LABEL = "__unmatched__"


def get_metric_endpoint(request: Request) -> str:
    """Return a bounded Prometheus label for the matched route template."""
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    return route_path if isinstance(route_path, str) and route_path else UNMATCHED_ROUTE_LABEL


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance tracking and monitoring."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.enabled = settings.MONITOR_PERFORMANCE
        self.api_logging_enabled = settings.MONITOR_API_LOG
        self.slow_threshold_ms = settings.SLOW_QUERY_THRESHOLD_MS
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and track performance metrics."""
        if not self.enabled:
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        duration_ms = round(duration * 1000, 2)
        metric_endpoint = get_metric_endpoint(request)
        
        # Performance data
        perf_data = {
            "endpoint": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "slow_query": duration_ms > self.slow_threshold_ms,
        }
        
        # Add to response headers (for debugging)
        response.headers["X-Response-Time"] = f"{duration_ms}ms"

        request_count.labels(
            method=request.method,
            endpoint=metric_endpoint,
            status=str(response.status_code),
        ).inc()
        request_duration.labels(
            method=request.method,
            endpoint=metric_endpoint,
        ).observe(duration)

        if self.api_logging_enabled:
            access_logger.info(
                f"{request.method} {request.url.path}",
                extra=perf_data,
            )
        
        # Log performance
        if duration_ms > self.slow_threshold_ms:
            performance_logger.warning(
                f"Slow request: {request.method} {request.url.path}",
                extra=perf_data
            )
        else:
            performance_logger.info(
                f"{request.method} {request.url.path}",
                extra=perf_data
            )
        
        return response
