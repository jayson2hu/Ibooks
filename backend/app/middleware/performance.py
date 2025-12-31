"""
Performance tracking middleware for monitoring API response times.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
import time
from app.config import settings
from app.utils.logging import performance_logger


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance tracking and monitoring."""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.enabled = settings.MONITOR_PERFORMANCE
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
