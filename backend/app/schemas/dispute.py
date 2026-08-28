from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class DisputeEvidenceCreatePayload(BaseModel):
    title: str
    description: str
    evidence_data: Optional[str] = None
    submitted_by_type: str = "worker"
    submitted_by_id: Optional[str] = None

class DisputeEvidenceResponse(BaseModel):
    id: int
    dispute_id: int
    submitted_by_type: str
    submitted_by_id: Optional[str]
    title: str
    description: str
    evidence_data: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class DisputeAuditLogResponse(BaseModel):
    id: int
    dispute_id: int
    action: str
    actor_type: str
    actor_id: Optional[str]
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class DisputeCreatePayload(BaseModel):
    task_id: int
    reason: str
    description: str
    raised_by_type: str = "worker"
    raised_by_id: Optional[str] = None
    initial_evidence_title: Optional[str] = None
    initial_evidence_description: Optional[str] = None
    initial_evidence_data: Optional[str] = None

class DisputeResponse(BaseModel):
    id: int
    dispute_code: Optional[str]
    task_id: int
    submission_id: int
    verification_id: int
    escrow_id: int
    settlement_id: Optional[int]
    raised_by_type: str
    raised_by_id: Optional[str]
    worker_agent_id: int
    reason: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    evidence_items: Optional[List[DisputeEvidenceResponse]] = []
    audit_logs: Optional[List[DisputeAuditLogResponse]] = []

    class Config:
        from_attributes = True
