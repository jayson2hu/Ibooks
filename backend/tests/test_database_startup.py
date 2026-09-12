"""Tests for safe database startup behavior."""

import sqlite3

import pytest

from app import database
from app.config import Settings


def test_sqlite_foreign_key_hook_supports_sync_dbapi_connections():
    """The connect hook also works with the standard synchronous driver."""
    connection = sqlite3.connect(":memory:")
    try:
        database._enable_sqlite_foreign_keys(connection, None)
        assert connection.execute("PRAGMA foreign_keys").fetchone() == (1,)
    finally:
        connection.close()


class StubConnection:
    """Record synchronous operations submitted through an async connection."""

    def __init__(self) -> None:
        self.operations: list[str] = []

    async def run_sync(self, operation) -> None:
        self.operations.append(operation.__name__)


class StubTransaction:
    """Minimal async context manager returned by ``engine.begin``."""

    def __init__(self, connection: StubConnection) -> None:
        self.connection = connection

    async def __aenter__(self) -> StubConnection:
        return self.connection

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        return None


class StubEngine:
    """Minimal engine that exposes a recorded begin transaction."""

    def __init__(self) -> None:
        self.connection = StubConnection()
        self.begin_calls = 0

    def begin(self) -> StubTransaction:
        self.begin_calls += 1
        return StubTransaction(self.connection)


def test_schema_bootstrap_is_disabled_by_default():
    """A production-style environment cannot mutate schemas by omission."""
    assert Settings.model_fields["SCHEMA_BOOTSTRAP_ENABLED"].default is False


@pytest.mark.asyncio
async def test_init_db_skips_all_schema_mutation_when_disabled(monkeypatch):
    """Disabled bootstrap must not even open a schema transaction."""
    stub_engine = StubEngine()
    monkeypatch.setattr(database, "engine", stub_engine)

    bootstrapped = await database.init_db(bootstrap_schema=False)

    assert bootstrapped is False
    assert stub_engine.begin_calls == 0
    assert stub_engine.connection.operations == []


@pytest.mark.asyncio
async def test_init_db_runs_local_compatibility_bootstrap_when_explicit(monkeypatch):
    """Local/test callers can explicitly request the compatibility bootstrap."""
    stub_engine = StubEngine()
    monkeypatch.setattr(database, "engine", stub_engine)

    bootstrapped = await database.init_db(bootstrap_schema=True)

    assert bootstrapped is True
    assert stub_engine.begin_calls == 1
    assert stub_engine.connection.operations == [
        "create_all",
        "_run_startup_migrations",
    ]


@pytest.mark.asyncio
async def test_init_db_uses_configured_bootstrap_flag(monkeypatch):
    """Legacy helper callers inherit the explicit environment configuration."""
    stub_engine = StubEngine()
    monkeypatch.setattr(database, "engine", stub_engine)
    monkeypatch.setattr(database.settings, "SCHEMA_BOOTSTRAP_ENABLED", True)

    bootstrapped = await database.init_db()

    assert bootstrapped is True
    assert stub_engine.begin_calls == 1
