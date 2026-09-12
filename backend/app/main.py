"""
Main FastAPI application.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from contextlib import asynccontextmanager
from pathlib import Path

from app.config import settings
from app.database import init_db, close_db
from app.database import engine
from sqlalchemy import text
import redis.asyncio as redis
from app.services.crawler_service import crawler_scheduler
from app.utils.logging import setup_logging
from app.utils.metrics import metrics_endpoint
from app.middleware import AuditMiddleware, PerformanceMiddleware, SecurityHeadersMiddleware, setup_cors
from app.api import router as api_router
from app.static_generator.html_generator import get_resource_html_path
from app.static_generator.startup import generate_startup_seo_files


GENERATED_RESOURCE_NOT_FOUND_DETAIL = "Generated resource page not found"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events - startup and shutdown.
    """
    # Startup
    setup_logging()
    await init_db(bootstrap_schema=settings.SCHEMA_BOOTSTRAP_ENABLED)
    await generate_startup_seo_files()
    if settings.CRAWLER_SCHEDULER_ENABLED:
        crawler_scheduler.start()
    print(f"[START] {settings.APP_NAME} v{settings.APP_VERSION} started")

    yield

    # Shutdown
    if settings.CRAWLER_SCHEDULER_ENABLED:
        await crawler_scheduler.stop()
    await close_db()
    print(f"[STOP] {settings.APP_NAME} shut down")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Digital Resource Marketplace API",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Setup CORS
setup_cors(app)

# Add middleware
app.add_middleware(SecurityHeadersMiddleware)

if settings.MONITOR_PERFORMANCE:
    app.add_middleware(PerformanceMiddleware)

if settings.MONITOR_AUDIT:
    app.add_middleware(AuditMiddleware)


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

def get_static_pages_dir() -> Path:
    """Return the same configured directory used by the SEO generators."""
    static_dir = Path(settings.STATIC_PAGES_DIR).expanduser()
    static_dir.mkdir(parents=True, exist_ok=True)
    return static_dir


def static_page_response(filename: str, media_type: str, missing_detail: str) -> FileResponse:
    """Build a response for a generated SEO file or report a real 404."""
    file_path = get_static_pages_dir() / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=missing_detail)
    return FileResponse(file_path, media_type=media_type)


def generated_resource_page_response(slug: str) -> FileResponse:
    """Serve one generated resource page while keeping reads inside its directory."""
    try:
        file_path = get_resource_html_path(slug, get_static_pages_dir())
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=GENERATED_RESOURCE_NOT_FOUND_DETAIL,
        ) from exc

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=GENERATED_RESOURCE_NOT_FOUND_DETAIL,
        )
    return FileResponse(file_path, media_type="text/html")

# Serve individual SEO files
@app.get("/sitemap.xml")
async def serve_sitemap():
    """Serve sitemap.xml file."""
    return static_page_response(
        "sitemap.xml",
        "application/xml",
        "Sitemap not found. Please generate it first.",
    )

@app.get("/rss.xml")
async def serve_rss():
    """Serve RSS feed file."""
    return static_page_response(
        "rss.xml",
        "application/xml",
        "RSS feed not found. Please generate it first.",
    )

@app.get("/robots.txt")
async def serve_robots():
    """Serve robots.txt file."""
    return static_page_response(
        "robots.txt",
        "text/plain",
        "Robots.txt not found. Please generate it first.",
    )


@app.get("/generated/resources/{slug}.html")
async def serve_generated_resource_page(slug: str):
    """Serve a generated resource HTML page by its canonical resource slug."""
    return generated_resource_page_response(slug)

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API information."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{settings.APP_NAME}</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #333; }}
            .status {{ color: #28a745; }}
            a {{ color: #007bff; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 {settings.APP_NAME}</h1>
            <p class="status">Status: <strong>Running</strong></p>
            <p>Version: {settings.APP_VERSION}</p>
            <h2>API Documentation</h2>
            <ul>
                <li><a href="/api/docs">Swagger UI</a></li>
                <li><a href="/api/redoc">ReDoc</a></li>
                <li><a href="/metrics">Prometheus Metrics</a></li>
            </ul>
            <h2>Endpoints</h2>
            <ul>
                <li><strong>Authentication:</strong> {settings.API_V1_PREFIX}/auth</li>
                <li><strong>Resources:</strong> {settings.API_V1_PREFIX}/resources</li>
                <li><strong>Categories:</strong> {settings.API_V1_PREFIX}/categories</li>
                <li><strong>Search:</strong> {settings.API_V1_PREFIX}/search</li>
                <li><strong>Admin:</strong> {settings.API_V1_PREFIX}/admin</li>
            </ul>
        </div>
    </body>
    </html>
    """


# Health check endpoint
@app.get("/live")
async def liveness_check():
    """Liveness probe that only confirms the API process can respond."""
    return {"status": "alive", "version": settings.APP_VERSION}


@app.get("/health")
async def health_check():
    """Readiness check used by orchestration and load balancers."""
    checks = {"database": "ok", "redis": "ok"}
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        checks["database"] = "unavailable"

    client = None
    try:
        client = redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        await client.ping()
    except Exception:
        checks["redis"] = "unavailable"
    finally:
        if client is not None:
            try:
                await client.aclose()
            except Exception:
                checks["redis"] = "unavailable"

    status_value = (
        "healthy"
        if all(check == "ok" for check in checks.values())
        else "unhealthy"
    )
    payload = {"status": status_value, "version": settings.APP_VERSION, "checks": checks}
    if status_value == "unhealthy":
        raise HTTPException(status_code=503, detail=payload)
    return payload


# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return metrics_endpoint()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
