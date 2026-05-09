"""
Wallet endpoints.
"""
from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.wallet import CoinLedger
from app.schemas.wallet import CoinLedgerListResponse, WalletResponse
from app.services.wallet import get_or_create_wallet


router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.get("/me", response_model=WalletResponse)
async def get_my_wallet(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's wallet summary."""
    wallet = await get_or_create_wallet(db, current_user.id)
    return wallet


@router.get("/ledger", response_model=CoinLedgerListResponse)
async def list_my_coin_ledger(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List coin ledger entries for the current user."""
    wallet = await get_or_create_wallet(db, current_user.id)
    base_query = select(CoinLedger).where(CoinLedger.wallet_id == wallet.id)
    total = await db.scalar(select(func.count()).select_from(base_query.subquery()))

    query = (
        base_query
        .order_by(CoinLedger.created_at.desc(), CoinLedger.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    entries = result.scalars().all()

    return {
        "items": entries,
        "total": total or 0,
        "page": page,
        "page_size": page_size,
        "pages": ceil((total or 0) / page_size) if total else 0,
    }
