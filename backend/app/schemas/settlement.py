from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class SettlementAuditLogResponse(BaseModel):
    id: int
    settlement_id: int
    action: str
    actor_type: str
    actor_id: Optional[str] = None
    amount: Optional[float] = None
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    message: str
    created_at: datetime

    class Config:
        from_attributes = True


class LedgerEntryResponse(BaseModel):
    id: int
    entry_code: str
    settlement_id: Optional[int] = None
    escrow_id: Optional[int] = None
    task_id: Optional[int] = None
    wallet_id: int
    entry_type: str
    amount: float
    balance_type: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


class SettlementResponse(BaseModel):
    id: int
    settlement_code: str
    task_id: int
    task_code: Optional[str] = None
    task_title: Optional[str] = None
    escrow_id: int
    escrow_code: Optional[str] = None
    verification_id: Optional[int] = None
    verification_code: Optional[str] = None
    requester_wallet_id: int
    requester_wallet_code: Optional[str] = None
    worker_wallet_id: int
    worker_wallet_code: Optional[str] = None
    worker_agent_id: int
    worker_agent_name: Optional[str] = None
    worker_agent_code: Optional[str] = None
    amount: float
    currency: str
    status: str
    trigger_type: str
    verification_decision: Optional[str] = None
    integrity_verified: bool
    failure_reason: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class SettlementSummaryResponse(BaseModel):
    total_settlements: int
    completed_settlements: int
    blocked_settlements: int
    failed_settlements: int
    pending_settlements: int
    total_ap_settled: float
    ap_currently_locked: float
    ap_awaiting_resolution: float
