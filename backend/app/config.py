"""
Application configuration management.
Loads settings from environment variables with validation.
"""
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


_INSECURE_JWT_VALUES = {
    "changeme",
    "secret",
    "test-secret",
    "your-jwt-secret-key-change-this-in-production",
    "your-secret-key-change-in-production",
    "your-super-secret-jwt-key-change-this-in-production",
}
_INSECURE_JWT_MARKERS = ("change-this", "change-in-production", "your-secret")
_LOCAL_SITE_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
_EXAMPLE_SITE_HOSTS = {
    "example.com",
    "www.example.com",
    "example.net",
    "www.example.net",
    "example.org",
    "www.example.org",
}


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # Database
    DATABASE_URL: str
    DB_ECHO: bool = False
    # Compatibility fallback for disposable local/test databases only.
    # Production startup must rely on Alembic and leave this disabled.
    SCHEMA_BOOTSTRAP_ENABLED: bool = False

    # Redis
    REDIS_URL: str

    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1, le=90)
    PASSWORD_MIN_LENGTH: int = 8

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://0.0.0.0:3000,http://0.0.0.0:3001,http://127.0.0.1:3000,http://127.0.0.1:3001"
    CORS_ALLOW_CREDENTIALS: bool = True

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Application
    APP_NAME: str = "Resource Marketplace"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # Monitoring Flags
    MONITOR_PERFORMANCE: bool = True
    MONITOR_AUDIT: bool = True
    MONITOR_API_LOG: bool = True
    MONITOR_SYSTEM_METRICS: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_ACCESS: bool = True
    LOG_ERROR: bool = True
    LOG_PERFORMANCE: bool = True
    LOG_AUDIT: bool = True
    # Relative defaults work for local development and resolve to /app/* in Docker.
    LOG_DIR: str = "logs"
    LOG_FORMAT: str = "json"

    # SEO
    SEO_AUTO_GENERATE: bool = True
    SEO_SUBMIT_BAIDU: bool = False
    SEO_SUBMIT_GOOGLE: bool = False
    SEO_SUBMIT_360: bool = False
    BAIDU_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    SITE_URL: str = "https://www.example.com"
    API_PUBLIC_URL: str = ""
    STATIC_PAGES_DIR: str = "static_pages"

    # Email
    EMAIL_SMTP_HOST: str = "smtp.gmail.com"
    EMAIL_SMTP_PORT: int = 587
    EMAIL_FROM: str = ""
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_USE_TLS: bool = True

    # Alipay
    ALIPAY_APP_ID: str = ""
    ALIPAY_PRIVATE_KEY: str = ""
    ALIPAY_PUBLIC_KEY: str = ""
    ALIPAY_SANDBOX: bool = True

    # File Upload
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024, gt=0)  # bytes (10 MiB)
    UPLOAD_DIR: str = "uploads"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Performance
    SLOW_QUERY_THRESHOLD_MS: int = 500

    # Crawler
    CRAWLER_SCHEDULER_ENABLED: bool = True

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        """Fail fast when a non-debug process uses development credentials."""
        if self.DEBUG:
            return self

        errors: list[str] = []
        secret = self.JWT_SECRET_KEY.strip()
        normalized_secret = secret.lower()
        if (
            len(secret) < 32
            or normalized_secret in _INSECURE_JWT_VALUES
            or any(marker in normalized_secret for marker in _INSECURE_JWT_MARKERS)
        ):
            errors.append(
                "JWT_SECRET_KEY must be at least 32 characters and not use a placeholder"
            )

        site = urlparse(self.SITE_URL)
        hostname = (site.hostname or "").lower()
        if site.scheme not in {"http", "https"} or not hostname:
            errors.append("SITE_URL must be an absolute HTTP(S) URL")
        elif (
            hostname in _LOCAL_SITE_HOSTS
            or hostname.endswith(".localhost")
            or hostname in _EXAMPLE_SITE_HOSTS
        ):
            errors.append("SITE_URL must not use a local or example hostname")

        if self.SCHEMA_BOOTSTRAP_ENABLED:
            errors.append("SCHEMA_BOOTSTRAP_ENABLED must be false when DEBUG=false")

        if errors:
            raise ValueError("Unsafe production configuration: " + "; ".join(errors))

        return self


# Global settings instance
settings = Settings()
