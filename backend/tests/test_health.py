"""Tests for liveness and dependency-aware readiness probes."""

import pytest
from httpx import AsyncClient

from app import main as main_module
from app.main import app


class StubDatabaseConnection:
    """Database connection that can simulate an unavailable dependency."""

    def __init__(self, unavailable: bool) -> None:
        self.unavailable = unavailable

    async def execute(self, statement) -> None:
        if self.unavailable:
            raise RuntimeError("database unavailable")


class StubDatabaseContext:
    def __init__(self, unavailable: bool) -> None:
        self.connection = StubDatabaseConnection(unavailable)

    async def __aenter__(self) -> StubDatabaseConnection:
        return self.connection

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        return None


class StubEngine:
    def __init__(self, unavailable: bool) -> None:
        self.unavailable = unavailable

    def connect(self) -> StubDatabaseContext:
        return StubDatabaseContext(self.unavailable)


class StubRedisClient:
    """Redis client that records cleanup and can fail its readiness ping."""

    def __init__(self, unavailable: bool) -> None:
        self.unavailable = unavailable
        self.closed = False

    async def ping(self) -> None:
        if self.unavailable:
            raise RuntimeError("redis unavailable")

    async def aclose(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_liveness_does_not_depend_on_database_or_redis():
    """The liveness endpoint remains usable for process restarts."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "alive",
        "version": main_module.settings.APP_VERSION,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("database_unavailable", "redis_unavailable", "expected_checks"),
    [
        (True, False, {"database": "unavailable", "redis": "ok"}),
        (False, True, {"database": "ok", "redis": "unavailable"}),
        (True, True, {"database": "unavailable", "redis": "unavailable"}),
    ],
)
async def test_readiness_returns_503_when_a_required_dependency_is_unavailable(
    monkeypatch,
    database_unavailable,
    redis_unavailable,
    expected_checks,
):
    """Both the database and Redis are mandatory readiness dependencies."""
    redis_client = StubRedisClient(redis_unavailable)
    monkeypatch.setattr(main_module, "engine", StubEngine(database_unavailable))
    monkeypatch.setattr(
        main_module.redis,
        "from_url",
        lambda *args, **kwargs: redis_client,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "status": "unhealthy",
        "version": main_module.settings.APP_VERSION,
        "checks": expected_checks,
    }
    assert redis_client.closed is True


@pytest.mark.asyncio
async def test_readiness_returns_200_when_database_and_redis_are_available(monkeypatch):
    """Healthy dependencies produce a successful readiness response."""
    redis_client = StubRedisClient(unavailable=False)
    monkeypatch.setattr(main_module, "engine", StubEngine(unavailable=False))
    monkeypatch.setattr(
        main_module.redis,
        "from_url",
        lambda *args, **kwargs: redis_client,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "version": main_module.settings.APP_VERSION,
        "checks": {"database": "ok", "redis": "ok"},
    }
    assert redis_client.closed is True
