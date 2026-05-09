"""
Pydantic schemas for wallet and coin ledger.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.wallet import CoinLedgerType
from app.schemas.user import UserResponse


class WalletResponse(BaseModel):
    """Current wallet summary."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    balance: int
    total_recharged: int
    total_spent: int
    total_rewarded: int
    created_at: datetime
    updated_at: datetime


class AdminWalletResponse(WalletResponse):
    """Admin wallet response with user profile."""
    user: UserResponse | None = None


class CoinLedgerResponse(BaseModel):
    """Coin ledger entry response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    wallet_id: int
    amount: int
    balance_after: int
    type: CoinLedgerType
    related_order_no: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime


class AdminCoinLedgerResponse(CoinLedgerResponse):
    """Admin ledger response with user profile."""
    user: UserResponse | None = None


class CoinLedgerListResponse(BaseModel):
    """Paginated coin ledger response."""
    items: List[CoinLedgerResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AdminWalletListResponse(BaseModel):
    """Paginated admin wallet response."""
    items: List[AdminWalletResponse]
    total: int
    page: int
    page_size: int
    pages: int


class AdminCoinLedgerListResponse(BaseModel):
    """Paginated admin coin ledger response."""
    items: List[AdminCoinLedgerResponse]
    total: int
    page: int
    page_size: int
    pages: int


class WalletAdjustRequest(BaseModel):
    """Admin wallet balance adjustment request."""
    amount: int = Field(..., description="Positive to add coins, negative to deduct coins")
    description: Optional[str] = Field(None, max_length=500)
