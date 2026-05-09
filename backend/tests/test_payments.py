"""
Tests for legacy resource payment routes.
"""
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_legacy_resource_alipay_create_route_is_disabled():
    """Resource-order Alipay payment is no longer exposed."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/payments/alipay/create",
            json={"order_no": "ORDLEGACY"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_legacy_resource_alipay_notify_route_is_disabled():
    """Resource-order Alipay notify is no longer exposed."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/payments/alipay/notify",
            data={
                "out_trade_no": "ORDLEGACY",
                "trade_no": "TRADE-LEGACY",
                "trade_status": "TRADE_SUCCESS",
                "sign": "legacy-sign",
            },
        )

    assert response.status_code == 404
