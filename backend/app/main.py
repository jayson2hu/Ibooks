"""
Main FastAPI application.
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db, close_db
from app.utils.logging import setup_logging
from app.utils.metrics import metrics_endpoint
from app.middleware import AuditMiddleware, PerformanceMiddleware, setup_cors
from app.api.v1 import auth, resources, categories, contacts, search, admin
from app.api import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events - startup and shutdown.
    """
    # Startup
    setup_logging()
    await init_db()
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} started")
    
    yield
    
    # Shutdown
    await close_db()
    print(f"👋 {settings.APP_NAME} shut down")


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
if settings.MONITOR_PERFORMANCE:
    app.add_middleware(PerformanceMiddleware)

if settings.MONITOR_AUDIT:
    app.add_middleware(AuditMiddleware)


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


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
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "version": settings.APP_VERSION}


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
