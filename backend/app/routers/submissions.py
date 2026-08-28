"""
Phase 9 — Submissions router.

Endpoints:
  GET  /api/submissions/pending-verification
  GET  /api/submissions/code/{submission_code}
  GET  /api/submissions/{submission_id}
  GET  /api/submissions/{submission_id}/integrity
  GET  /api/submissions/{submission_id}/audit
  GET  /api/tasks/{task_id}/submission
  GET  /api/agents/{agent_id}/submissions
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from app.schemas.submission import (
    ResultSubmissionDetailResponse,
    ResultSubmissionResponse,
    SubmissionAuditLogResponse,
    SubmissionIntegrityResponse,
    PendingVerificationItem,
)
from app.services import submission_service as svc
from app.models.result_submission import ResultSubmission, SubmissionAuditLog

router = APIRouter(prefix="/api", tags=["submissions"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse(field: Any) -> Any:
    """Parse a JSON string field into a Python object."""
    if field is None:
        return None
    if isinstance(field, str):
        try:
            return json.loads(field)
        except Exception:
            return field
    return field


def _to_detail(s: ResultSubmission) -> Dict:
    """Convert ORM object to dict with all parsed JSON fields."""
    return {
        "id": s.id,
        "submission_code": s.submission_code,
        "version": s.version,
        "status": s.status,
        "is_locked": s.is_locked,
        "verification_ready": s.verification_ready,
        "task_id": s.task_id,
        "execution_id": s.execution_id,
        "agent_id": s.agent_id,
        "bid_id": s.bid_id,
        "output_text": s.output_text,
        "structured_output": _parse(s.structured_output),
        "result_summary": s.result_summary,
        "content_type": s.content_type,
        "confidence_score": s.confidence_score,
        "evidence": _parse(s.evidence),
        "provenance": _parse(s.provenance),
        "task_snapshot": _parse(s.task_snapshot),
        "agent_snapshot": _parse(s.agent_snapshot),
        "bid_snapshot": _parse(s.bid_snapshot),
        "execution_snapshot": _parse(s.execution_snapshot),
        "submission_metadata": _parse(s.submission_metadata),
        "self_assessment": _parse(s.self_assessment),
        "limitations": _parse(s.limitations),
        "integrity_hash": s.integrity_hash,
        "submitted_at": s.submitted_at,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }


# ── Routes (order matters — specific paths before parametric) ─────────────────

@router.get("/submissions/pending-verification", response_model=List[PendingVerificationItem])
def pending_verification(db: Session = Depends(get_db)):
    """
    Return all locked, verifier-ready submissions.
    Phase 10 can extend this to exclude already-verified ones.
    """
    subs = svc.get_pending_verification(db)
    return [
        PendingVerificationItem(
            id=s.id,
            submission_code=s.submission_code,
            task_id=s.task_id,
            agent_id=s.agent_id,
            status=s.status,
            verification_ready=s.verification_ready,
            integrity_hash=s.integrity_hash,
            submitted_at=s.submitted_at,
        )
        for s in subs
    ]


@router.get("/submissions/code/{submission_code}", response_model=ResultSubmissionDetailResponse)
def get_by_code(submission_code: str, db: Session = Depends(get_db)):
    """Lookup a submission by its human-readable RS-NNNN code."""
    s = svc.get_submission_by_code(db, submission_code)
    if not s:
        raise HTTPException(status_code=404, detail=f"Submission '{submission_code}' not found.")
    return _to_detail(s)


@router.get("/submissions/{submission_id}", response_model=ResultSubmissionDetailResponse)
def get_submission(submission_id: int, db: Session = Depends(get_db)):
    """Full submission detail including all snapshots and parsed JSON fields."""
    s = svc.get_submission(db, submission_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found.")
    return _to_detail(s)


@router.get("/submissions/{submission_id}/integrity", response_model=SubmissionIntegrityResponse)
def check_integrity(submission_id: int, db: Session = Depends(get_db)):
    """Re-compute SHA-256 hash and verify it matches the stored fingerprint."""
    s = svc.get_submission(db, submission_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found.")
    result = svc.verify_submission_integrity(s)
    return SubmissionIntegrityResponse(
        submission_code=s.submission_code,
        submission_id=s.id,
        valid=result["valid"],
        algorithm="SHA-256",
        stored_hash=s.integrity_hash,
        verification_ready=s.verification_ready,
        reason=result.get("reason"),
    )


@router.get("/submissions/{submission_id}/audit", response_model=List[SubmissionAuditLogResponse])
def get_audit(submission_id: int, db: Session = Depends(get_db)):
    """Return the chronological audit trail for a submission."""
    s = svc.get_submission(db, submission_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Submission {submission_id} not found.")
    logs = svc.get_submission_audit(db, submission_id)
    return logs


@router.get("/tasks/{task_id}/submission", response_model=ResultSubmissionDetailResponse)
def get_task_submission(task_id: int, db: Session = Depends(get_db)):
    """Return the current result submission for a given task."""
    s = svc.get_task_submission(db, task_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"No submission found for task {task_id}.")
    return _to_detail(s)


@router.get("/agents/{agent_id}/submissions", response_model=List[ResultSubmissionResponse])
def get_agent_submissions(agent_id: int, db: Session = Depends(get_db)):
    """Return all submissions by a specific agent (newest first)."""
    subs = svc.get_agent_submissions(db, agent_id)
    return [
        ResultSubmissionResponse(
            id=s.id,
            submission_code=s.submission_code,
            version=s.version,
            status=s.status,
            is_locked=s.is_locked,
            verification_ready=s.verification_ready,
            task_id=s.task_id,
            execution_id=s.execution_id,
            agent_id=s.agent_id,
            bid_id=s.bid_id,
            result_summary=s.result_summary,
            confidence_score=s.confidence_score,
            integrity_hash=s.integrity_hash,
            submitted_at=s.submitted_at,
            created_at=s.created_at,
        )
        for s in subs
    ]
