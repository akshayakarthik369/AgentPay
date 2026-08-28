"""
Phase 9 — Pydantic schemas for ResultSubmission endpoints.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class SubmissionAuditLogResponse(BaseModel):
    id: int
    submission_id: int
    action: str
    actor_type: str
    actor_id: Optional[str]
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ResultSubmissionResponse(BaseModel):
    """Lightweight summary for list views."""
    id: int
    submission_code: Optional[str]
    version: int
    status: str
    is_locked: bool
    verification_ready: bool
    task_id: int
    execution_id: int
    agent_id: int
    bid_id: int
    result_summary: Optional[str]
    confidence_score: Optional[int]
    integrity_hash: Optional[str]
    submitted_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ResultSubmissionDetailResponse(BaseModel):
    """Full package returned to frontend and verifiers."""
    id: int
    submission_code: Optional[str]
    version: int
    status: str
    is_locked: bool
    verification_ready: bool

    # IDs
    task_id: int
    execution_id: int
    agent_id: int
    bid_id: int

    # Core result
    output_text: Optional[str]
    structured_output: Optional[Any]      # parsed JSON
    result_summary: Optional[str]
    content_type: Optional[str]
    confidence_score: Optional[int]

    # Provenance & evidence
    evidence: Optional[Any]               # parsed JSON
    provenance: Optional[Any]             # parsed JSON

    # Frozen snapshots
    task_snapshot: Optional[Any]          # parsed JSON
    agent_snapshot: Optional[Any]         # parsed JSON
    bid_snapshot: Optional[Any]           # parsed JSON
    execution_snapshot: Optional[Any]     # parsed JSON

    # Assessment & metadata
    submission_metadata: Optional[Any]    # parsed JSON
    self_assessment: Optional[Any]        # parsed JSON
    limitations: Optional[List[str]]      # parsed JSON list

    # Integrity
    integrity_hash: Optional[str]

    # Timestamps
    submitted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubmissionIntegrityResponse(BaseModel):
    submission_code: Optional[str]
    submission_id: int
    valid: bool
    algorithm: str = "SHA-256"
    stored_hash: Optional[str]
    verification_ready: bool
    reason: Optional[str] = None


class PendingVerificationItem(BaseModel):
    id: int
    submission_code: Optional[str]
    task_id: int
    agent_id: int
    status: str
    result_summary: Optional[str] = None
    verification_ready: bool
    integrity_hash: Optional[str]
    submitted_at: Optional[datetime]

    class Config:
        from_attributes = True

