from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ActivityEvent(BaseModel):
    event_type: str
    title: str
    description: str
    task_id: Optional[int] = None
    agent_id: Optional[int] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    related_entity_code: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    created_at: Optional[str] = None


class TransactionItem(BaseModel):
    id: int
    entry_code: Optional[str] = None
    entry_type: str
    direction: str  # credit, debit, lock, other
    amount: float
    balance_type: str
    description: str
    status: str
    wallet_id: Optional[int] = None
    settlement_id: Optional[int] = None
    settlement_code: Optional[str] = None
    escrow_id: Optional[int] = None
    escrow_code: Optional[str] = None
    task_id: Optional[int] = None
    task_title: Optional[str] = None
    created_at: Optional[str] = None
