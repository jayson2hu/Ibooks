"""
Pydantic schemas for daily sign-in.
"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class SigninStatusResponse(BaseModel):
    """Current user's sign-in status."""
    enabled: bool
    reward_coins: int
    signed_in_today: bool
    signin_date: date


class SigninResponse(BaseModel):
    """Successful sign-in response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    signin_date: date
    reward_coins: int
    created_at: datetime
    balance: int
