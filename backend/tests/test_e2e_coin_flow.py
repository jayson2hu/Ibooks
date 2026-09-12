"""
End-to-end tests for the coin-based purchase flow.
"""
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.main import app
from app.models.order import Order, OrderStatus
from app.models.resource import Resource
from app.models.user import User, UserRole
from app.models.wallet import Wallet
from app.services.wallet import get_or_create_wallet
from app.utils.security import create_access_token, get_password_hash


async def create_user(email: str, role: UserRole = UserRole.USER) -> tuple[User, str]:
    """Create a user and return it with a JWT token."""
    async with AsyncSessionLocal() as session:
        user = User(
            email=email,
            username=email.split("@")[0],
            role=role,
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


async def create_paid_resource(slug: str, coin_price: int) -> Resource:
    """Create a published paid resource with cloud delivery fields."""
    async with AsyncSessionLocal() as session:
        resource = Resource(
            title=f"Resource {slug}",
            slug=slug,
            description="E2E resource",
            tags=[],
            price=Decimal("99.00"),
            coin_price=coin_price,
            is_free=False,
            cloud_link=f"https://pan.example.com/{slug}",
            backup_links=[],
            access_code="abcd",
            preview_images=[],
            is_published=True,
        )
        session.add(resource)
        await session.commit()
        await session.refresh(resource)
        return resource


@pytest.mark.asyncio
async def test_signin_reward_purchase_flow_grants_access():
    """Scenario A: sign in for coins, buy a resource, then access delivery."""
    _, admin_token = await create_user("e2e-admin-a@example.com", UserRole.ADMIN)
    user, user_token = await create_user("e2e-user-a@example.com")
    resource = await create_paid_resource("e2e-signin-buy", coin_price=6)

    async with AsyncClient(app=app, base_url="http://test") as client:
        settings_response = await client.put(
            "/api/v1/admin/settings/signin",
            json={"enabled": True, "reward_coins": 10},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        signin_response = await client.post(
            "/api/v1/signin",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        order_response = await client.post(
            "/api/v1/orders",
            json={"resource_id": resource.id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        wallet_response = await client.get(
            "/api/v1/wallet/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        access_response = await client.get(
            f"/api/v1/resources/{resource.slug}/access",
            headers={"Authorization": f"Bearer {user_token}"},
        )

    assert settings_response.status_code == 200
    assert signin_response.status_code == 201
    assert signin_response.json()["balance"] == 10
    assert order_response.status_code == 201
    assert order_response.json()["status"] == "paid"
    assert order_response.json()["payment_method"] == "coin"
    assert order_response.json()["coin_amount"] == 6
    assert wallet_response.json()["balance"] == 4
    assert access_response.status_code == 200
    assert access_response.json() == {"has_access": True}

    async with AsyncSessionLocal() as session:
        order = (await session.execute(
            select(Order).where(Order.user_id == user.id, Order.resource_id == resource.id)
        )).scalar_one()
    assert order.status == OrderStatus.PAID


@pytest.mark.asyncio
async def test_insufficient_balance_does_not_create_paid_order():
    """Scenario C: insufficient balance rejects purchase without granting access."""
    user, user_token = await create_user("e2e-user-c@example.com")
    resource = await create_paid_resource("e2e-insufficient", coin_price=50)

    async with AsyncClient(app=app, base_url="http://test") as client:
        order_response = await client.post(
            "/api/v1/orders",
            json={"resource_id": resource.id},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        wallet_response = await client.get(
            "/api/v1/wallet/me",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        access_response = await client.get(
            f"/api/v1/resources/{resource.slug}/access",
            headers={"Authorization": f"Bearer {user_token}"},
        )

    assert order_response.status_code == 402
    assert order_response.json()["detail"]["message"] == "Insufficient coin balance"
    assert wallet_response.json()["balance"] == 0
    assert access_response.status_code == 402

    async with AsyncSessionLocal() as session:
        paid_order = (await session.execute(
            select(Order).where(
                Order.user_id == user.id,
                Order.resource_id == resource.id,
                Order.status == OrderStatus.PAID,
            )
        )).scalar_one_or_none()
        wallet = (await session.execute(select(Wallet).where(Wallet.user_id == user.id))).scalar_one()
    assert paid_order is None
    assert wallet.balance == 0


@pytest.mark.asyncio
async def test_admin_adjusts_balance_lists_ledger_and_disables_signin():
    """Scenario D: admin adjusts balance, sees ledger, and disables sign-in."""
    _, admin_token = await create_user("e2e-admin-d@example.com", UserRole.ADMIN)
    user, user_token = await create_user("e2e-user-d@example.com")

    async with AsyncClient(app=app, base_url="http://test") as client:
        adjust_response = await client.post(
            f"/api/v1/admin/wallets/{user.id}/adjust",
            json={"amount": 15, "description": "E2E admin adjustment"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        ledger_response = await client.get(
            "/api/v1/admin/coin-ledger",
            params={"user_id": user.id, "type": "admin_adjust"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        settings_response = await client.put(
            "/api/v1/admin/settings/signin",
            json={"enabled": False, "reward_coins": 5},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        signin_response = await client.post(
            "/api/v1/signin",
            headers={"Authorization": f"Bearer {user_token}"},
        )

    assert adjust_response.status_code == 200
    assert adjust_response.json()["balance"] == 15
    assert ledger_response.status_code == 200
    assert ledger_response.json()["total"] == 1
    assert ledger_response.json()["items"][0]["amount"] == 15
    assert ledger_response.json()["items"][0]["description"] == "E2E admin adjustment"
    assert settings_response.status_code == 200
    assert settings_response.json()["enabled"] is False
    assert signin_response.status_code == 403
    assert signin_response.json()["detail"] == "签到功能未开启"
