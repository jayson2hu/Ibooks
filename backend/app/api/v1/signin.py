"""
Daily sign-in endpoints.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.signin import DailySignin
from app.models.user import User
from app.models.wallet import CoinLedgerType
from app.schemas.signin import SigninResponse, SigninStatusResponse
from app.services.site_settings import get_signin_enabled, get_signin_reward_coins
from app.services.wallet import credit_wallet


router = APIRouter(prefix="/signin", tags=["Signin"])


async def get_today_signin(
    db: AsyncSession,
    user_id: int,
    signin_date: date,
) -> DailySignin | None:
    """Return today's sign-in record for a user."""
    result = await db.execute(
        select(DailySignin).where(
            DailySignin.user_id == user_id,
            DailySignin.signin_date == signin_date,
        )
    )
    return result.scalar_one_or_none()


@router.get("/status", response_model=SigninStatusResponse)
async def get_signin_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current daily sign-in status."""
    today = date.today()
    signed_in = await get_today_signin(db, current_user.id, today)
    enabled = await get_signin_enabled(db)
    reward_coins = await get_signin_reward_coins(db)

    return {
        "enabled": enabled,
        "reward_coins": reward_coins,
        "signed_in_today": signed_in is not None,
        "signin_date": today,
    }


@router.post("", response_model=SigninResponse, status_code=status.HTTP_201_CREATED)
async def signin(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Claim today's daily sign-in coin reward."""
    today = date.today()
    if not await get_signin_enabled(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="签到功能未开启",
        )

    existing = await get_today_signin(db, current_user.id, today)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="今日已签到",
        )

    reward_coins = await get_signin_reward_coins(db)
    signin_record = DailySignin(
        user_id=current_user.id,
        signin_date=today,
        reward_coins=reward_coins,
    )
    db.add(signin_record)
    await db.flush()

    wallet, _ = await credit_wallet(
        db,
        current_user.id,
        reward_coins,
        CoinLedgerType.SIGNIN,
        related_order_no=f"SIGNIN-{today.isoformat()}",
        description="每日签到奖励",
    )
    await db.commit()
    await db.refresh(signin_record)

    return {
        "id": signin_record.id,
        "user_id": signin_record.user_id,
        "signin_date": signin_record.signin_date,
        "reward_coins": signin_record.reward_coins,
        "created_at": signin_record.created_at,
        "balance": wallet.balance,
    }
