"""
Tests for recharge packages and orders.
"""
from decimal import Decimal
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.main import app
from app.models.recharge import (
    RechargeOrder,
    RechargeOrderStatus,
    RechargePackage,
    RechargePaymentMethod,
)
from app.models.user import User
from app.services.wallet import get_or_create_wallet
from app.utils.security import create_access_token, get_password_hash


async def create_user_and_token(email: str = "recharge@example.com") -> tuple[User, str]:
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


async def create_package(
    *,
    name: str = "测试充值包",
    coins: int = 100,
    bonus_coins: int = 10,
    amount: Decimal = Decimal("10.00"),
    is_active: bool = True,
    sort_order: int = 0,
) -> RechargePackage:
    """Create a recharge package."""
    async with AsyncSessionLocal() as session:
        package = RechargePackage(
            name=name,
            coins=coins,
            bonus_coins=bonus_coins,
            amount=amount,
            is_active=is_active,
            sort_order=sort_order,
        )
        session.add(package)
        await session.commit()
        await session.refresh(package)
        return package


async def create_recharge_order(
    user_id: int,
    package_id: int | None,
    status: RechargeOrderStatus = RechargeOrderStatus.PENDING,
    recharge_no: str = "RCHTESTORDER",
) -> RechargeOrder:
    """Create a recharge order directly."""
    async with AsyncSessionLocal() as session:
        order = RechargeOrder(
            recharge_no=recharge_no,
            user_id=user_id,
            package_id=package_id,
            coins=100,
            bonus_coins=0,
            amount=Decimal("10.00"),
            payment_method=RechargePaymentMethod.ALIPAY,
            status=status,
            paid_at=datetime.utcnow() if status == RechargeOrderStatus.PAID else None,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        return order


@pytest.mark.asyncio
async def test_list_recharge_packages_returns_only_active_packages():
    """Public package list only includes active packages."""
    active = await create_package(name="启用套餐", is_active=True, sort_order=10)
    await create_package(name="停用套餐", is_active=False, sort_order=99)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/recharge/packages")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == active.id
    assert data[0]["name"] == "启用套餐"


@pytest.mark.asyncio
async def test_create_recharge_order_from_active_package():
    """Users can create a pending recharge order from an active package."""
    user, token = await create_user_and_token()
    package = await create_package(coins=120, bonus_coins=20, amount=Decimal("12.00"))

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recharge/orders",
            json={"package_id": package.id, "payment_method": "alipay"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["recharge_no"].startswith("RCH")
    assert data["user_id"] == user.id
    assert data["package_id"] == package.id
    assert data["coins"] == 120
    assert data["bonus_coins"] == 20
    assert data["amount"] == "12.00"
    assert data["payment_method"] == "alipay"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_create_recharge_order_rejects_inactive_package():
    """Inactive packages cannot create recharge orders."""
    _, token = await create_user_and_token("inactive-package@example.com")
    package = await create_package(is_active=False)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recharge/orders",
            json={"package_id": package.id, "payment_method": "alipay"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_recharge_order_rejects_invalid_package_config():
    """Invalid package values are rejected at order creation."""
    _, token = await create_user_and_token("invalid-package@example.com")
    package = await create_package(coins=0, amount=Decimal("10.00"), is_active=True)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recharge/orders",
            json={"package_id": package.id, "payment_method": "alipay"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "充值套餐配置无效"


@pytest.mark.asyncio
async def test_my_recharge_orders_and_detail_are_owner_scoped():
    """Users can list and view only their own recharge orders."""
    owner, owner_token = await create_user_and_token("owner-recharge@example.com")
    other, other_token = await create_user_and_token("other-recharge@example.com")
    package = await create_package()
    order = await create_recharge_order(owner.id, package.id, recharge_no="RCHOWNER")
    await create_recharge_order(other.id, package.id, recharge_no="RCHOTHER")

    async with AsyncClient(app=app, base_url="http://test") as client:
        list_response = await client.get(
            "/api/v1/recharge/orders/my",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        detail_response = await client.get(
            f"/api/v1/recharge/orders/{order.recharge_no}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        forbidden_response = await client.get(
            f"/api/v1/recharge/orders/{order.recharge_no}",
            headers={"Authorization": f"Bearer {other_token}"},
        )

    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1
    assert list_response.json()["items"][0]["recharge_no"] == "RCHOWNER"
    assert detail_response.status_code == 200
    assert detail_response.json()["recharge_no"] == "RCHOWNER"
    assert forbidden_response.status_code == 403


@pytest.mark.asyncio
async def test_cancel_pending_recharge_order_success():
    """Pending recharge orders can be cancelled."""
    user, token = await create_user_and_token("cancel-recharge@example.com")
    package = await create_package()
    order = await create_recharge_order(user.id, package.id, recharge_no="RCHCANCEL")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.patch(
            f"/api/v1/recharge/orders/{order.recharge_no}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_paid_recharge_order_cannot_be_cancelled():
    """Paid recharge orders cannot be cancelled."""
    user, token = await create_user_and_token("paid-recharge@example.com")
    package = await create_package()
    order = await create_recharge_order(
        user.id,
        package.id,
        status=RechargeOrderStatus.PAID,
        recharge_no="RCHPAID",
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.patch(
            f"/api/v1/recharge/orders/{order.recharge_no}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "仅待支付充值订单可取消"


@pytest.mark.asyncio
async def test_recharge_order_requires_login():
    """Recharge order creation requires authentication."""
    package = await create_package()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/recharge/orders",
            json={"package_id": package.id, "payment_method": "alipay"},
        )

    assert response.status_code in (401, 403)
