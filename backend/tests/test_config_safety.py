"""Tests for environment-sensitive configuration safeguards."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def make_settings(**overrides) -> Settings:
    """Build isolated settings without reading the developer's local .env file."""
    values = {
        "DATABASE_URL": "sqlite+aiosqlite:///./config-test.db",
        "REDIS_URL": "redis://localhost:6379/0",
        "JWT_SECRET_KEY": "9f79a78c3c5f4b80b5936b625b6d872a",
        "SITE_URL": "https://books.example.cn",
        "DEBUG": False,
        "SCHEMA_BOOTSTRAP_ENABLED": False,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_debug_mode_allows_explicit_local_bootstrap():
    """Developers can opt into the compatibility bootstrap locally."""
    settings = make_settings(
        DEBUG=True,
        JWT_SECRET_KEY="test-secret",
        SITE_URL="http://localhost:3000",
        SCHEMA_BOOTSTRAP_ENABLED=True,
    )

    assert settings.SCHEMA_BOOTSTRAP_ENABLED is True


@pytest.mark.parametrize(
    "secret",
    [
        "too-short",
        "your-secret-key-change-in-production",
        "your-super-secret-jwt-key-change-this-in-production",
    ],
)
def test_non_debug_mode_rejects_weak_or_placeholder_jwt_secret(secret):
    """Production-like processes reject predictable signing keys."""
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        make_settings(JWT_SECRET_KEY=secret)


@pytest.mark.parametrize(
    "site_url",
    [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://www.example.com",
        "not-a-url",
    ],
)
def test_non_debug_mode_rejects_local_placeholder_or_invalid_site_url(site_url):
    """Public production URLs must identify a deployable site."""
    with pytest.raises(ValidationError, match="SITE_URL"):
        make_settings(SITE_URL=site_url)


def test_non_debug_mode_rejects_schema_bootstrap():
    """Alembic remains the only production schema mutation path."""
    with pytest.raises(ValidationError, match="SCHEMA_BOOTSTRAP_ENABLED"):
        make_settings(SCHEMA_BOOTSTRAP_ENABLED=True)


def test_non_debug_mode_accepts_hardened_configuration():
    """A valid production-style configuration remains compatible."""
    settings = make_settings()

    assert settings.DEBUG is False
    assert settings.SCHEMA_BOOTSTRAP_ENABLED is False
