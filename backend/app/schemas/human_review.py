from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class HumanReviewAuditLogResponse(BaseModel):
    id: int
    review_id: int
    action: str
    actor_type: str
    actor_id: Optional[str]
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class HumanReviewResponse(BaseModel):
    id: int
    review_code: Optional[str]
    task_id: int
    submission_id: int
    verification_id: int
    worker_agent_id: int
    status: str
    decision: Optional[str]
    reviewer_note: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True

class HumanReviewResolvePayload(BaseModel):
    decision: str  # APPROVE or REJECT
    reviewer_note: str
