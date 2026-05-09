"""
Tests for recharge payment endpoints.
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.api.v1 import recharge
from app.database import AsyncSessionLocal
from app.main import app
from app.models.recharge import (
    RechargeOrder,
    RechargeOrderStatus,
    RechargePackage,
    RechargePaymentMethod,
)
from app.models.user import User
from app.models.wallet import CoinLedger, CoinLedgerType, Wallet
from app.services.wallet import get_or_create_wallet
from app.utils.security import create_access_token, get_password_hash


class FakeAlipay:
    """Fake Alipay SDK client."""

    def __init__(self, verify_result: bool = True):
        self.verify_result = verify_result

    def api_alipay_trade_page_pay(self, **kwargs):
        return f"out_trade_no={kwargs['out_trade_no']}&total_amount={kwargs['total_amount']}"

    def verify(self, data, signature):
        return self.verify_result


async def create_user_and_token(email: str = "recharge-pay@example.com") -> tuple[User, str]:
    """Create a user with wallet and token."""
    async with AsyncSessionLocal() as session:
        user = User(
            email=email,
            username=email.split("@")[0],
            password_hash=get_password_hash("Test1234"),
        )
        session.add(user)
        await session.flush()
        await get_or_create_wallet(session, user.id)
        await session.commit()
        await session.refresh(user)
        token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )
        return user, token


async def create_package_and_order(
    user_id: int,
    *,
    status: RechargeOrderStatus = RechargeOrderStatus.PENDING,
    recharge_no: str = "RCHPAYPENDING",
) -> RechargeOrder:
    """Create a recharge package and order."""
    async with AsyncSessionLocal() as session:
        package = RechargePackage(
            name="支付测试套餐",
            coins=100,
            bonus_coins=20,
            amount=Decimal("12.00"),
            is_active=True,
            sort_order=0,
        )
        session.add(package)
        await session.flush()

        order = RechargeOrder(
            recharge_no=recharge_no,
            user_id=user_id,
            package_id=package.id,
            coins=100,
            bonus_coins=20,
            amount=Decimal("12.00"),
            payment_method=RechargePaymentMethod.ALIPAY,
            status=status,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order


@pytest.mark.asyncio
async def test_alipay_recharge_create_returns_payment_url(monkeypatch):
    """Pending recharge orders can create an Alipay payment URL."""
    user, token = await create_user_and_token()
    order = await create_package_and_order(user.id)
    monkeypatch.setattr(recharge, "get_alipay_client", lambda: FakeAlipay())

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recharge/alipay/create",
            json={"recharge_no": order.recharge_no},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["recharge_no"] == order.recharge_no
    assert "openapi.alipaydev.com" in data["payment_url"]
    assert order.recharge_no in data["payment_url"]


@pytest.mark.asyncio
async def test_alipay_recharge_create_rejects_non_owner(monkeypatch):
    """Users cannot pay another user's recharge order."""
    owner, _ = await create_user_and_token("recharge-owner@example.com")
    _, other_token = await create_user_and_token("recharge-other@example.com")
    order = await create_package_and_order(owner.id, recharge_no="RCHPAYOWNER")
    monkeypatch.setattr(recharge, "get_alipay_client", lambda: FakeAlipay())

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recharge/alipay/create",
            json={"recharge_no": order.recharge_no},
            headers={"Authorization": f"Bearer {other_token}"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_alipay_recharge_create_rejects_non_pending(monkeypatch):
    """Only pending recharge orders can create payment URLs."""
    user, token = await create_user_and_token("recharge-paid@example.com")
    order = await create_package_and_order(
        user.id,
        status=RechargeOrderStatus.PAID,
        recharge_no="RCHPAYPAID",
    )
    monkeypatch.setattr(recharge, "get_alipay_client", lambda: FakeAlipay())

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recharge/alipay/create",
            json={"recharge_no": order.recharge_no},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_alipay_recharge_notify_success_marks_paid_and_adds_coins(monkeypatch):
    """Verified Alipay notification marks recharge paid and credits wallet."""
    user, _ = await create_user_and_token("notify-success@example.com")
    order = await create_package_and_order(user.id, recharge_no="RCHNOTIFYSUCCESS")
    monkeypatch.setattr(recharge, "get_alipay_client", lambda: FakeAlipay(verify_result=True))

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recharge/alipay/notify",
            data={
                "out_trade_no": order.recharge_no,
                "trade_no": "TRADE-RCH-1",
                "trade_status": "TRADE_SUCCESS",
                "sign": "valid-sign",
            },
        )

    assert response.status_code == 200
    assert response.text == "success"

    async with AsyncSessionLocal() as session:
        updated = (await session.execute(
            select(RechargeOrder).where(RechargeOrder.recharge_no == order.recharge_no)
        )).scalar_one()
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalar_one()
        ledger = (await session.execute(
            select(CoinLedger).where(
                CoinLedger.user_id == user.id,
                CoinLedger.related_order_no == order.recharge_no,
            )
        )).scalar_one()

        assert updated.status == RechargeOrderStatus.PAID
        assert updated.trade_no == "TRADE-RCH-1"
        assert updated.paid_at is not None
        assert wallet.balance == 120
        assert wallet.total_recharged == 120
        assert ledger.amount == 120
        assert ledger.type == CoinLedgerType.RECHARGE


@pytest.mark.asyncio
async def test_alipay_recharge_notify_is_idempotent(monkeypatch):
    """Duplicate successful notifications do not credit twice."""
    user, _ = await create_user_and_token("notify-idempotent@example.com")
    order = await create_package_and_order(user.id, recharge_no="RCHNOTIFYIDEMP")
    monkeypatch.setattr(recharge, "get_alipay_client", lambda: FakeAlipay(verify_result=True))

    async with AsyncClient(app=app, base_url="http://test") as client:
        for _ in range(2):
            response = await client.post(
                "/api/v1/recharge/alipay/notify",
                data={
                    "out_trade_no": order.recharge_no,
                    "trade_no": "TRADE-RCH-2",
                    "trade_status": "TRADE_SUCCESS",
                    "sign": "valid-sign",
                },
            )
            assert response.status_code == 200
            assert response.text == "success"

    async with AsyncSessionLocal() as session:
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalar_one()
        ledgers = (await session.execute(
            select(CoinLedger).where(
                CoinLedger.user_id == user.id,
                CoinLedger.related_order_no == order.recharge_no,
            )
        )).scalars().all()

        assert wallet.balance == 120
        assert wallet.total_recharged == 120
        assert len(ledgers) == 1


@pytest.mark.asyncio
async def test_alipay_recharge_notify_verify_failure_does_not_update(monkeypatch):
    """Failed signature verification leaves recharge order and wallet unchanged."""
    user, _ = await create_user_and_token("notify-failure@example.com")
    order = await create_package_and_order(user.id, recharge_no="RCHNOTIFYFAIL")
    monkeypatch.setattr(recharge, "get_alipay_client", lambda: FakeAlipay(verify_result=False))

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recharge/alipay/notify",
            data={
                "out_trade_no": order.recharge_no,
                "trade_no": "TRADE-RCH-FAIL",
                "trade_status": "TRADE_SUCCESS",
                "sign": "invalid-sign",
            },
        )

    assert response.status_code == 200
    assert response.text == "failure"

    async with AsyncSessionLocal() as session:
        updated = (await session.execute(
            select(RechargeOrder).where(RechargeOrder.recharge_no == order.recharge_no)
        )).scalar_one()
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalar_one()
        ledgers = (await session.execute(
            select(CoinLedger).where(CoinLedger.user_id == user.id)
        )).scalars().all()

        assert updated.status == RechargeOrderStatus.PENDING
        assert updated.trade_no is None
        assert wallet.balance == 0
        assert ledgers == []
