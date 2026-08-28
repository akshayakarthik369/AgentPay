from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class WalletBase(BaseModel):
    owner_type: str = Field(..., description="requester | agent | system")
    owner_id: Optional[int] = Field(None, description="Linked ID")
    currency: str = Field("AP", description="Currency identifier")


class WalletResponse(BaseModel):
    id: int
    wallet_code: str
    owner_type: str
    owner_id: Optional[int]
    available_balance: float
    locked_balance: float
    total_earned: float
    total_spent: float
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WalletSummaryResponse(BaseModel):
    wallet_code: str
    owner_type: str
    owner_id: Optional[int]
    available_balance: float
    locked_balance: float
    total_balance: float
    total_earned: float
    total_spent: float
    currency: str
    is_active: bool
