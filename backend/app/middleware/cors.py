"""
CORS middleware configuration.
"""
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings


def setup_cors(app):
    """Configure CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Response-Time"],
    )
