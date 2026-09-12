"""
Prometheus metrics utilities for monitoring.
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
import psutil

from app.config import settings


# Request metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Database metrics
db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type']
)

db_connection_pool = Gauge(
    'db_connection_pool_size',
    'Database connection pool size'
)

# System metrics
cpu_usage = Gauge(
    'system_cpu_usage_percent',
    'System CPU usage percentage'
)

memory_usage = Gauge(
    'system_memory_usage_bytes',
    'System memory usage in bytes'
)

# Application metrics
active_users = Gauge(
    'active_users_total',
    'Number of active users'
)

resources_total = Gauge(
    'resources_total',
    'Total number of resources'
)


def update_system_metrics():
    """Update system metrics (CPU, memory)."""
    cpu_usage.set(psutil.cpu_percent())
    memory_usage.set(psutil.virtual_memory().used)


def metrics_endpoint() -> Response:
    """Endpoint for Prometheus to scrape metrics."""
    if settings.MONITOR_SYSTEM_METRICS:
        update_system_metrics()
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
