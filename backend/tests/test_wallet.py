"""
Tests for wallet and coin ledger functionality.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.main import app
from app.models.user import User
from app.models.wallet import CoinLedger, CoinLedgerType, Wallet
from app.services.wallet import credit_wallet, debit_wallet, get_or_create_wallet
from app.utils.security import create_access_token, get_password_hash


async def create_user_and_token(email: str = "wallet@example.com") -> tuple[User, str]:
    """Create a test user and auth token."""
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


@pytest.mark.asyncio
async def test_register_creates_zero_balance_wallet():
    """User registration creates a wallet with zero balance."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "new-wallet@example.com",
                "username": "newwallet",
                "password": "Test1234",
            },
        )

    assert response.status_code == 201

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.email == "new-wallet@example.com")
        )).scalar_one()
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalar_one()
        assert wallet.balance == 0
        assert wallet.total_recharged == 0
        assert wallet.total_spent == 0
        assert wallet.total_rewarded == 0


@pytest.mark.asyncio
async def test_wallet_me_requires_login():
    """Wallet endpoint requires authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/wallet/me")

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_wallet_me_returns_current_user_wallet():
    """Authenticated users can fetch their wallet summary."""
    user, token = await create_user_and_token()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/wallet/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user.id
    assert data["balance"] == 0


@pytest.mark.asyncio
async def test_get_or_create_wallet_is_idempotent():
    """Repeated wallet creation returns the same wallet."""
    user, _ = await create_user_and_token("idempotent@example.com")

    async with AsyncSessionLocal() as session:
        first = await get_or_create_wallet(session, user.id)
        second = await get_or_create_wallet(session, user.id)
        await session.commit()

        wallets = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalars().all()

    assert first.id == second.id
    assert len(wallets) == 1


@pytest.mark.asyncio
async def test_credit_wallet_adds_balance_and_ledger():
    """Crediting a wallet increases balance and writes a positive ledger entry."""
    user, _ = await create_user_and_token("credit@example.com")

    async with AsyncSessionLocal() as session:
        wallet, ledger = await credit_wallet(
            session,
            user.id,
            30,
            CoinLedgerType.RECHARGE,
            related_order_no="RCH001",
            description="充值",
        )
        await session.commit()
        wallet_id = wallet.id
        ledger_id = ledger.id

    async with AsyncSessionLocal() as session:
        wallet = await session.get(Wallet, wallet_id)
        ledger = await session.get(CoinLedger, ledger_id)
        assert wallet.balance == 30
        assert wallet.total_recharged == 30
        assert ledger.amount == 30
        assert ledger.balance_after == 30
        assert ledger.type == CoinLedgerType.RECHARGE


@pytest.mark.asyncio
async def test_debit_wallet_subtracts_balance_and_ledger():
    """Debiting a wallet decreases balance and writes a negative ledger entry."""
    user, _ = await create_user_and_token("debit@example.com")

    async with AsyncSessionLocal() as session:
        await credit_wallet(session, user.id, 50, CoinLedgerType.RECHARGE)
        wallet, ledger = await debit_wallet(
            session,
            user.id,
            20,
            CoinLedgerType.PURCHASE,
            related_order_no="ORD001",
            description="购买资源",
        )
        await session.commit()
        wallet_id = wallet.id
        ledger_id = ledger.id

    async with AsyncSessionLocal() as session:
        wallet = await session.get(Wallet, wallet_id)
        ledger = await session.get(CoinLedger, ledger_id)
        assert wallet.balance == 30
        assert wallet.total_spent == 20
        assert ledger.amount == -20
        assert ledger.balance_after == 30
        assert ledger.type == CoinLedgerType.PURCHASE


@pytest.mark.asyncio
async def test_debit_wallet_rejects_insufficient_balance_without_ledger():
    """Insufficient balance leaves wallet and ledger untouched."""
    user, _ = await create_user_and_token("insufficient@example.com")

    async with AsyncSessionLocal() as session:
        await credit_wallet(session, user.id, 10, CoinLedgerType.RECHARGE)
        await session.commit()

    async with AsyncSessionLocal() as session:
        with pytest.raises(Exception):
            await debit_wallet(session, user.id, 20, CoinLedgerType.PURCHASE)
        await session.rollback()

    async with AsyncSessionLocal() as session:
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalar_one()
        ledger_entries = (await session.execute(
            select(CoinLedger).where(CoinLedger.user_id == user.id)
        )).scalars().all()
        assert wallet.balance == 10
        assert len(ledger_entries) == 1


@pytest.mark.asyncio
async def test_wallet_ledger_returns_paginated_entries():
    """Users can list their own wallet ledger entries."""
    user, token = await create_user_and_token("ledger@example.com")

    async with AsyncSessionLocal() as session:
        await credit_wallet(session, user.id, 10, CoinLedgerType.RECHARGE, related_order_no="RCH001")
        await credit_wallet(session, user.id, 5, CoinLedgerType.SIGNIN, description="签到")
        await debit_wallet(session, user.id, 3, CoinLedgerType.PURCHASE, related_order_no="ORD001")
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/wallet/ledger?page=1&page_size=2",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["pages"] == 2
    assert len(data["items"]) == 2
