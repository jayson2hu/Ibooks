"""
Application configuration management.
Loads settings from environment variables with validation.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


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

    # Redis
    REDIS_URL: str

    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
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
    LOG_DIR: str = "/app/logs"
    LOG_FORMAT: str = "json"

    # SEO
    SEO_AUTO_GENERATE: bool = True
    SEO_SUBMIT_BAIDU: bool = False
    SEO_SUBMIT_GOOGLE: bool = False
    SEO_SUBMIT_360: bool = False
    BAIDU_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    SITE_URL: str = "https://www.example.com"
    STATIC_PAGES_DIR: str = "/app/static_pages"

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
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "/app/uploads"

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Performance
    SLOW_QUERY_THRESHOLD_MS: int = 500

    # Crawler
    CRAWLER_SCHEDULER_ENABLED: bool = True


# Global settings instance
settings = Settings()
