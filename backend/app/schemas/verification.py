"""
Phase 10 — Pydantic Schemas for Verification.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, field_validator


class VerificationAuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    verification_id: int
    action: str
    actor_type: str
    actor_id: Optional[str]
    message: Optional[str]
    created_at: datetime


class VerificationStartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
    verification_id: int
    verification_code: Optional[str]
    status: str
    submission_id: int
    task_id: int
    worker_agent_id: int
    verifier_agent_id: int
    verifier_name: Optional[str] = None
    verifier_code: Optional[str] = None
    started_at: Optional[datetime] = None


class VerificationCriteriaScores(BaseModel):
    accuracy: float
    completeness: float
    format_compliance: float
    quality: float
    evidence_provenance: float
    overall: float
    required: float


class VerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    verification_code: Optional[str]
    submission_id: int
    task_id: int
    worker_agent_id: int
    verifier_agent_id: int
    status: str
    decision: Optional[str]
    integrity_valid: bool
    accuracy_score: float
    completeness_score: float
    format_compliance_score: float
    quality_score: float
    evidence_score: float
    overall_score: float
    required_score: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime


class VerificationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    verification_code: Optional[str]
    submission_id: int
    task_id: int
    worker_agent_id: int
    verifier_agent_id: int
    status: str
    decision: Optional[str]
    integrity_valid: bool

    # Criteria Scores
    accuracy_score: float
    completeness_score: float
    format_compliance_score: float
    quality_score: float
    evidence_score: float
    overall_score: float
    required_score: float

    # Parsed JSON structures
    reasons: Optional[Dict[str, List[str]]] = None
    warnings: Optional[List[str]] = None
    verification_details: Optional[Dict[str, Any]] = None
    verifier_snapshot: Optional[Dict[str, Any]] = None
    submission_hash_snapshot: Optional[str] = None

    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @field_validator("reasons", "warnings", "verification_details", "verifier_snapshot", mode="before")
    @classmethod
    def parse_json_fields(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return v
        return v
