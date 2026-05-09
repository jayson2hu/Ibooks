"""
Tests for daily sign-in rewards.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.main import app
from app.models.signin import DailySignin
from app.models.site_settings import SiteSetting
from app.models.user import User, UserRole
from app.models.wallet import CoinLedger, CoinLedgerType, Wallet
from app.services.wallet import get_or_create_wallet
from app.utils.security import create_access_token, get_password_hash


async def create_user_and_token(
    email: str = "signin@example.com",
    role: UserRole = UserRole.USER,
) -> tuple[User, str]:
    """Create a user with wallet and token."""
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


async def set_signin_settings(enabled: bool = True, reward_coins: int = 5) -> None:
    """Set sign-in settings for a test."""
    async with AsyncSessionLocal() as session:
        session.add_all([
            SiteSetting(
                key="signin_enabled",
                value="true" if enabled else "false",
                category="signin",
                description="是否开启每日签到奖励",
            ),
            SiteSetting(
                key="signin_reward_coins",
                value=str(reward_coins),
                category="signin",
                description="每日签到奖励书币数量",
            ),
        ])
        await session.commit()


@pytest.mark.asyncio
async def test_signin_status_defaults_to_disabled():
    """Sign-in status defaults to disabled when no setting exists."""
    _, token = await create_user_and_token()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/signin/status",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is False
    assert data["reward_coins"] == 5
    assert data["signed_in_today"] is False


@pytest.mark.asyncio
async def test_signin_disabled_rejects_without_balance_change():
    """Disabled sign-in cannot be claimed."""
    user, token = await create_user_and_token("disabled-signin@example.com")
    await set_signin_settings(enabled=False, reward_coins=8)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/signin",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "签到功能未开启"

    async with AsyncSessionLocal() as session:
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalar_one()
        ledgers = (await session.execute(
            select(CoinLedger).where(CoinLedger.user_id == user.id)
        )).scalars().all()
        assert wallet.balance == 0
        assert ledgers == []


@pytest.mark.asyncio
async def test_first_signin_adds_reward_and_ledger():
    """First daily sign-in adds configured reward coins."""
    user, token = await create_user_and_token("first-signin@example.com")
    await set_signin_settings(enabled=True, reward_coins=7)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/signin",
            headers={"Authorization": f"Bearer {token}"},
        )
        status_response = await client.get(
            "/api/v1/signin/status",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["reward_coins"] == 7
    assert data["balance"] == 7
    assert status_response.json()["signed_in_today"] is True

    async with AsyncSessionLocal() as session:
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalar_one()
        ledger = (await session.execute(
            select(CoinLedger).where(
                CoinLedger.user_id == user.id,
                CoinLedger.type == CoinLedgerType.SIGNIN,
            )
        )).scalar_one()
        signin = (await session.execute(
            select(DailySignin).where(DailySignin.user_id == user.id)
        )).scalar_one()
        assert wallet.balance == 7
        assert wallet.total_rewarded == 7
        assert ledger.amount == 7
        assert ledger.balance_after == 7
        assert signin.reward_coins == 7


@pytest.mark.asyncio
async def test_duplicate_signin_returns_409_without_second_reward():
    """Users can sign in only once per day."""
    user, token = await create_user_and_token("duplicate-signin@example.com")
    await set_signin_settings(enabled=True, reward_coins=5)

    async with AsyncClient(app=app, base_url="http://test") as client:
        first = await client.post(
            "/api/v1/signin",
            headers={"Authorization": f"Bearer {token}"},
        )
        second = await client.post(
            "/api/v1/signin",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert first.status_code == 201
    assert second.status_code == 409

    async with AsyncSessionLocal() as session:
        wallet = (await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )).scalar_one()
        signins = (await session.execute(
            select(DailySignin).where(DailySignin.user_id == user.id)
        )).scalars().all()
        ledgers = (await session.execute(
            select(CoinLedger).where(
                CoinLedger.user_id == user.id,
                CoinLedger.type == CoinLedgerType.SIGNIN,
            )
        )).scalars().all()
        assert wallet.balance == 5
        assert len(signins) == 1
        assert len(ledgers) == 1


@pytest.mark.asyncio
async def test_different_users_can_sign_in_same_day():
    """Different users can each sign in on the same day."""
    user_a, token_a = await create_user_and_token("signin-a@example.com")
    user_b, token_b = await create_user_and_token("signin-b@example.com")
    await set_signin_settings(enabled=True, reward_coins=6)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response_a = await client.post(
            "/api/v1/signin",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        response_b = await client.post(
            "/api/v1/signin",
            headers={"Authorization": f"Bearer {token_b}"},
        )

    assert response_a.status_code == 201
    assert response_b.status_code == 201

    async with AsyncSessionLocal() as session:
        count_a = len((await session.execute(
            select(DailySignin).where(DailySignin.user_id == user_a.id)
        )).scalars().all())
        count_b = len((await session.execute(
            select(DailySignin).where(DailySignin.user_id == user_b.id)
        )).scalars().all())
        assert count_a == 1
        assert count_b == 1


@pytest.mark.asyncio
async def test_signin_requires_login():
    """Sign-in endpoints require authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/signin")

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_invalid_signin_reward_setting_is_rejected():
    """Admin cannot save a non-positive sign-in reward."""
    _, admin_token = await create_user_and_token("signin-admin@example.com", UserRole.ADMIN)
    await set_signin_settings(enabled=True, reward_coins=5)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(
            "/api/v1/settings/signin_reward_coins",
            json={"value": "0"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "签到奖励币数必须为正整数"
