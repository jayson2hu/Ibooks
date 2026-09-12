"""Tests for monitoring feature flags that affect runtime behavior."""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.middleware import performance as performance_module
from app.middleware.performance import PerformanceMiddleware, UNMATCHED_ROUTE_LABEL
from app.utils import metrics as metrics_module


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [True, False])
async def test_api_log_flag_controls_access_log_emission(monkeypatch, enabled):
    """MONITOR_API_LOG controls structured access-log records."""
    monkeypatch.setattr(performance_module.settings, "MONITOR_PERFORMANCE", True)
    monkeypatch.setattr(performance_module.settings, "MONITOR_API_LOG", enabled)
    records: list[tuple[str, dict]] = []

    def capture_access(message: str, *, extra: dict) -> None:
        records.append((message, extra))

    monkeypatch.setattr(performance_module.access_logger, "info", capture_access)

    app = FastAPI()
    app.add_middleware(PerformanceMiddleware)

    @app.get("/probe")
    async def probe():
        return {"ok": True}

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/probe")

    assert response.status_code == 200
    assert "X-Response-Time" in response.headers
    if enabled:
        assert len(records) == 1
        assert records[0][0] == "GET /probe"
        assert records[0][1]["endpoint"] == "/probe"
        assert records[0][1]["status_code"] == 200
    else:
        assert records == []


@pytest.mark.parametrize("enabled", [True, False])
def test_system_metrics_flag_controls_host_sampling(monkeypatch, enabled):
    """MONITOR_SYSTEM_METRICS can disable host CPU and memory sampling."""
    monkeypatch.setattr(metrics_module.settings, "MONITOR_SYSTEM_METRICS", enabled)
    calls = 0

    def record_update() -> None:
        nonlocal calls
        calls += 1

    monkeypatch.setattr(metrics_module, "update_system_metrics", record_update)

    response = metrics_module.metrics_endpoint()

    assert response.status_code == 200
    assert calls == int(enabled)


@pytest.mark.asyncio
async def test_request_metrics_use_route_templates(monkeypatch):
    """Dynamic route values must not create unbounded Prometheus series."""
    monkeypatch.setattr(performance_module.settings, "MONITOR_PERFORMANCE", True)
    monkeypatch.setattr(performance_module.settings, "MONITOR_API_LOG", False)

    app = FastAPI()
    app.add_middleware(PerformanceMiddleware)

    @app.get("/metric-cardinality/{item_id}")
    async def metric_cardinality(item_id: str):
        return {"item_id": item_id}

    route_label = "/metric-cardinality/{item_id}"
    counter = metrics_module.request_count.labels(
        method="GET",
        endpoint=route_label,
        status="200",
    )
    before = counter._value.get()

    async with AsyncClient(app=app, base_url="http://test") as client:
        assert (await client.get("/metric-cardinality/alpha")).status_code == 200
        assert (await client.get("/metric-cardinality/beta")).status_code == 200

    assert counter._value.get() == before + 2
    endpoint_labels = {
        sample.labels["endpoint"]
        for metric in metrics_module.request_count.collect()
        for sample in metric.samples
        if sample.name == "http_requests_total"
    }
    assert "/metric-cardinality/alpha" not in endpoint_labels
    assert "/metric-cardinality/beta" not in endpoint_labels


@pytest.mark.asyncio
async def test_request_metrics_collapse_unmatched_paths(monkeypatch):
    """Arbitrary 404 paths share one fixed label instead of one series each."""
    monkeypatch.setattr(performance_module.settings, "MONITOR_PERFORMANCE", True)
    monkeypatch.setattr(performance_module.settings, "MONITOR_API_LOG", False)

    app = FastAPI()
    app.add_middleware(PerformanceMiddleware)

    counter = metrics_module.request_count.labels(
        method="GET",
        endpoint=UNMATCHED_ROUTE_LABEL,
        status="404",
    )
    before = counter._value.get()
    missing_paths = (
        "/metric-cardinality-missing-alpha",
        "/metric-cardinality-missing-beta",
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        for path in missing_paths:
            assert (await client.get(path)).status_code == 404

    assert counter._value.get() == before + len(missing_paths)
    endpoint_labels = {
        sample.labels["endpoint"]
        for metric in metrics_module.request_count.collect()
        for sample in metric.samples
        if sample.name == "http_requests_total"
    }
    assert all(path not in endpoint_labels for path in missing_paths)
