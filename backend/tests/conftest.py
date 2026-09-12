"""
Test configuration and fixtures.
"""
import os
import tempfile
from pathlib import Path
import pytest
import pytest_asyncio
from sqlalchemy import text


# Configure test settings before importing application modules.
default_test_db = (Path(tempfile.gettempdir()) / "ibooks_test.db").as_posix()
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{default_test_db}")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-only-jwt-secret-key-at-least-32-bytes",
)
os.environ.setdefault("SCHEMA_BOOTSTRAP_ENABLED", "false")

import app.models  # noqa: E402, F401
from app import dependencies  # noqa: E402
from app.api.v1 import auth as auth_api  # noqa: E402
from app.database import AsyncSessionLocal, Base, engine  # noqa: E402


TEST_DATABASE_URL = os.environ["DATABASE_URL"]


async def reset_database_schema(*, create_tables: bool) -> None:
    """Reset SQLite test schemas while restoring runtime FK enforcement."""
    if engine.url.get_backend_name() != "sqlite":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            if create_tables:
                await conn.run_sync(Base.metadata.create_all)
        return

    async with engine.connect() as conn:
        await conn.execute(text("PRAGMA foreign_keys=OFF"))
        await conn.commit()
        try:
            await conn.run_sync(Base.metadata.drop_all)
            if create_tables:
                await conn.run_sync(Base.metadata.create_all)
            await conn.commit()
        finally:
            if conn.in_transaction():
                await conn.rollback()
            await conn.execute(text("PRAGMA foreign_keys=ON"))
            await conn.commit()


@pytest.fixture(autouse=True)
def isolate_redis_backed_auth_controls(monkeypatch):
    """Keep the unit suite deterministic and independent of a local Redis."""

    async def allow_auth_request(
        key: str,
        max_calls: int,
        window_seconds: int,
    ) -> bool:
        return True

    async def token_is_not_blacklisted(token: str) -> bool:
        return False

    async def consume_refresh_token(token: str, ttl_seconds: int) -> bool:
        return True

    monkeypatch.setattr(auth_api, "check_rate_limit", allow_auth_request)
    monkeypatch.setattr(
        dependencies,
        "is_token_blacklisted",
        token_is_not_blacklisted,
    )
    monkeypatch.setattr(
        auth_api,
        "blacklist_token_once",
        consume_refresh_token,
    )


@pytest.fixture(scope="function")
async def db_session():
    """Yield a session from the same engine managed by the autouse fixture."""
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(autouse=True)
async def reset_app_database():
    """Reset the application database around each API test."""
    await reset_database_schema(create_tables=True)

    yield

    await reset_database_schema(create_tables=False)
