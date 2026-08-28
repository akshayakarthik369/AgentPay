from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ArbitrationAuditLogResponse(BaseModel):
    id: int
    arbitration_id: int
    action: str
    actor_type: str
    actor_id: Optional[str]
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class ArbitrationTriggerPayload(BaseModel):
    force_decision: Optional[str] = None # worker_wins | requester_wins | inconclusive (optional testing override)
    notes: Optional[str] = None

class ArbitrationResponse(BaseModel):
    id: int
    arbitration_code: Optional[str]
    dispute_id: int
    task_id: int
    arbitrator_agent_id: int
    worker_agent_id: int
    verification_id: Optional[int]
    review_id: Optional[int]
    escrow_id: int
    status: str
    decision: Optional[str]
    confidence_score: float
    reasoning_summary: Optional[str]
    analysis_details: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    resolved_at: Optional[datetime]
    audit_logs: Optional[List[ArbitrationAuditLogResponse]] = []

    class Config:
        from_attributes = True
