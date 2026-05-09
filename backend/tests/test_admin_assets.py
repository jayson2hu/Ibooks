"""
Tests for admin wallet, recharge, and sign-in management APIs.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.database import AsyncSessionLocal
from app.main import app
from app.models.recharge import RechargePackage
from app.models.user import User, UserRole
from app.models.wallet import CoinLedger, CoinLedgerType, Wallet
from app.services.wallet import credit_wallet, get_or_create_wallet
from app.utils.security import create_access_token, get_password_hash


async def create_user(email: str, role: UserRole = UserRole.USER) -> tuple[User, str]:
    """Create a user with a wallet and JWT token."""
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


@pytest.mark.asyncio
async def test_regular_user_cannot_access_admin_wallets():
    """Admin wallet list rejects non-admin users."""
    _, token = await create_user("regular-wallet-admin@example.com")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/admin/wallets",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_adjust_wallet_adds_coins_and_ledger():
    """Admin can add coins and writes an admin_adjust ledger entry."""
    _, admin_token = await create_user("asset-admin@example.com", UserRole.ADMIN)
    user, _ = await create_user("adjust-target@example.com")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/admin/wallets/{user.id}/adjust",
            json={"amount": 25, "description": "manual bonus"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert response.status_code == 200
    assert response.json()["balance"] == 25

    async with AsyncSessionLocal() as session:
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalar_one()
        ledger = (await session.execute(
            select(CoinLedger).where(CoinLedger.user_id == user.id)
        )).scalar_one()

    assert wallet.balance == 25
    assert wallet.total_rewarded == 25
    assert ledger.amount == 25
    assert ledger.type == CoinLedgerType.ADMIN_ADJUST
    assert ledger.description == "manual bonus"


@pytest.mark.asyncio
async def test_admin_adjust_wallet_rejects_insufficient_balance():
    """Admin deduction cannot drive wallet below zero."""
    _, admin_token = await create_user("deduct-admin@example.com", UserRole.ADMIN)
    user, _ = await create_user("deduct-target@example.com")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/admin/wallets/{user.id}/adjust",
            json={"amount": -10, "description": "manual deduction"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert response.status_code == 402

    async with AsyncSessionLocal() as session:
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalar_one()
        ledger_count = await session.scalar(
            select(func.count()).select_from(CoinLedger).where(CoinLedger.user_id == user.id)
        )

    assert wallet.balance == 0
    assert ledger_count == 0


@pytest.mark.asyncio
async def test_admin_can_create_and_update_recharge_package():
    """Admin can manage recharge packages and validation rejects invalid values."""
    _, admin_token = await create_user("package-admin@example.com", UserRole.ADMIN)

    async with AsyncClient(app=app, base_url="http://test") as client:
        invalid_response = await client.post(
            "/api/v1/admin/recharge-packages",
            json={"name": "bad", "coins": 0, "bonus_coins": 0, "amount": "9.90"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        create_response = await client.post(
            "/api/v1/admin/recharge-packages",
            json={"name": "30 书币", "coins": 30, "bonus_coins": 5, "amount": "9.90"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        package_id = create_response.json()["id"]
        update_response = await client.patch(
            f"/api/v1/admin/recharge-packages/{package_id}",
            json={"is_active": False, "sort_order": 10},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert invalid_response.status_code == 422
    assert create_response.status_code == 201
    assert update_response.status_code == 200
    assert update_response.json()["is_active"] is False
    assert update_response.json()["sort_order"] == 10


@pytest.mark.asyncio
async def test_admin_can_list_recharge_orders():
    """Admin can list recharge orders across users."""
    _, admin_token = await create_user("recharge-list-admin@example.com", UserRole.ADMIN)
    user, user_token = await create_user("recharge-list-user@example.com")

    async with AsyncSessionLocal() as session:
        package = RechargePackage(name="10 书币", coins=10, bonus_coins=0, amount=5)
        session.add(package)
        await session.commit()
        await session.refresh(package)

    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post(
            "/api/v1/recharge/orders",
            json={"package_id": package.id, "payment_method": "alipay"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        response = await client.get(
            "/api/v1/admin/recharge-orders",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["user_id"] == user.id


@pytest.mark.asyncio
async def test_admin_signin_settings_control_reward():
    """Admin sign-in settings are used by the user sign-in flow."""
    _, admin_token = await create_user("signin-admin@example.com", UserRole.ADMIN)
    user, user_token = await create_user("signin-user@example.com")

    async with AsyncClient(app=app, base_url="http://test") as client:
        settings_response = await client.put(
            "/api/v1/admin/settings/signin",
            json={"enabled": True, "reward_coins": 12},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        signin_response = await client.post(
            "/api/v1/signin",
            headers={"Authorization": f"Bearer {user_token}"},
        )

    assert settings_response.status_code == 200
    assert signin_response.status_code == 201
    assert signin_response.json()["reward_coins"] == 12

    async with AsyncSessionLocal() as session:
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalar_one()

    assert wallet.balance == 12
