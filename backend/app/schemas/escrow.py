from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class EscrowAuditLogResponse(BaseModel):
    id: int
    escrow_id: int
    action: str
    actor_type: str
    actor_id: Optional[str]
    message: str
    amount: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class EscrowResponse(BaseModel):
    id: int
    escrow_code: str
    task_id: int
    task_code: Optional[str] = None
    task_title: Optional[str] = None
    requester_wallet_id: int
    requester_wallet_code: Optional[str] = None
    worker_agent_id: int
    worker_agent_name: Optional[str] = None
    worker_agent_code: Optional[str] = None
    worker_wallet_id: int
    worker_wallet_code: Optional[str] = None
    verification_id: Optional[int] = None
    verification_decision: Optional[str] = None
    reward_amount: float
    status: str
    locked_at: datetime
    releasable_at: Optional[datetime] = None
    released_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EscrowSummaryResponse(BaseModel):
    total_locked: float
    total_releasable: float
    total_blocked: float
    total_released: float
    count_locked: int
    count_releasable: int
    count_blocked: int
    count_released: int
    count_total: int
