"""
Wallet balance mutation service.
"""
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import CoinLedger, CoinLedgerType, Wallet


async def get_or_create_wallet(db: AsyncSession, user_id: int) -> Wallet:
    """Return a user's wallet, creating it if missing."""
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    wallet = result.scalar_one_or_none()
    if wallet:
        return wallet

    wallet = Wallet(user_id=user_id)
    db.add(wallet)
    await db.flush()
    return wallet


async def get_wallet_for_update(db: AsyncSession, user_id: int) -> Wallet:
    """Return a wallet row with a database lock when supported."""
    result = await db.execute(
        select(Wallet)
        .where(Wallet.user_id == user_id)
        .with_for_update()
    )
    wallet = result.scalar_one_or_none()
    if wallet:
        return wallet
    return await get_or_create_wallet(db, user_id)


def validate_coin_amount(amount: int) -> None:
    """Validate a positive integer coin amount."""
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coin amount must be greater than zero",
        )


async def credit_wallet(
    db: AsyncSession,
    user_id: int,
    amount: int,
    ledger_type: CoinLedgerType,
    related_order_no: str | None = None,
    description: str | None = None,
) -> tuple[Wallet, CoinLedger]:
    """Add coins to a wallet and write an immutable ledger entry."""
    validate_coin_amount(amount)
    wallet = await get_wallet_for_update(db, user_id)

    wallet.balance += amount
    if ledger_type == CoinLedgerType.RECHARGE:
        wallet.total_recharged += amount
    elif ledger_type in (CoinLedgerType.SIGNIN, CoinLedgerType.ADMIN_ADJUST):
        wallet.total_rewarded += amount

    ledger = CoinLedger(
        user_id=user_id,
        wallet_id=wallet.id,
        amount=amount,
        balance_after=wallet.balance,
        type=ledger_type,
        related_order_no=related_order_no,
        description=description,
    )
    db.add(ledger)
    await db.flush()
    return wallet, ledger


async def debit_wallet(
    db: AsyncSession,
    user_id: int,
    amount: int,
    ledger_type: CoinLedgerType,
    related_order_no: str | None = None,
    description: str | None = None,
) -> tuple[Wallet, CoinLedger]:
    """Remove coins from a wallet and write an immutable ledger entry."""
    validate_coin_amount(amount)
    wallet = await get_wallet_for_update(db, user_id)

    if wallet.balance < amount:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": "Insufficient coin balance",
                "required_coins": amount,
                "balance": wallet.balance,
            },
        )

    wallet.balance -= amount
    if ledger_type == CoinLedgerType.PURCHASE:
        wallet.total_spent += amount

    ledger = CoinLedger(
        user_id=user_id,
        wallet_id=wallet.id,
        amount=-amount,
        balance_after=wallet.balance,
        type=ledger_type,
        related_order_no=related_order_no,
        description=description,
    )
    db.add(ledger)
    await db.flush()
    return wallet, ledger
