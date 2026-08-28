"""
Phase 10 — Verification REST API Router.

Endpoints:
  POST /api/submissions/{id}/verification/start  - Start verification pipeline
  POST /api/verifications/{id}/run               - Run evaluation and compute score
  GET  /api/verifications/{id}                   - Full verification detail
  GET  /api/verifications/{id}/audit             - Verification audit log
  GET  /api/tasks/{task_id}/verification         - Latest verification for task
  GET  /api/submissions/{sub_id}/verification     - Verification for submission
  GET  /api/verifications                        - List completed verifications
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from app.models.agent import Agent
from app.schemas.verification import (
    VerificationStartResponse,
    VerificationResponse,
    VerificationDetailResponse,
    VerificationAuditLogResponse,
)
from app.services import verification_service

router = APIRouter(prefix="/api", tags=["Verification"])


@router.post(
    "/submissions/{submission_id}/verification/start",
    response_model=VerificationStartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start independent verification pipeline for a submission",
)
def start_verification(submission_id: int, db: Session = Depends(get_db)):
    """
    Selects an independent eligible verifier agent and initiates verification.
    Guards against self-verification and duplicate verification (409 Conflict).
    """
    try:
        verification = verification_service.create_verification_for_submission(
            db, submission_id
        )
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("DUPLICATE_VERIFICATION:"):
            parts = msg.split(":")
            existing_id = int(parts[1]) if len(parts) > 1 else None
            existing_code = parts[2] if len(parts) > 2 else None
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Verification already exists and is finalized",
                    "verification_id": existing_id,
                    "verification_code": existing_code,
                },
            )
        elif msg.startswith("NO_VERIFIER_AVAILABLE:"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No eligible independent verifier agent is currently active.",
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    verifier = db.query(Agent).filter(Agent.id == verification.verifier_agent_id).first()

    return VerificationStartResponse(
        message=f"Independent verifier {verifier.name if verifier else 'assigned'} selected. Verification initiated.",
        verification_id=verification.id,
        verification_code=verification.verification_code,
        status=verification.status,
        submission_id=verification.submission_id,
        task_id=verification.task_id,
        worker_agent_id=verification.worker_agent_id,
        verifier_agent_id=verification.verifier_agent_id,
        verifier_name=verifier.name if verifier else None,
        verifier_code=verifier.agent_code if verifier else None,
        started_at=verification.started_at,
    )


@router.post(
    "/verifications/{verification_id}/run",
    response_model=VerificationDetailResponse,
    summary="Execute the verification evaluation pipeline",
)
def run_verification_endpoint(
    verification_id: int, db: Session = Depends(get_db)
):
    """
    Runs SHA-256 integrity check, executes category-specific scoring strategy,
    calculates 5 criteria, derives explainable reasons & warnings, and applies decision.
    """
    try:
        verification = verification_service.run_verification(db, verification_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return verification


@router.get(
    "/verifications/{verification_id}",
    response_model=VerificationDetailResponse,
    summary="Get full verification details and decision breakdown",
)
def get_verification(verification_id: int, db: Session = Depends(get_db)):
    verification = verification_service.get_verification_by_id(db, verification_id)
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification with ID {verification_id} not found.",
        )
    return verification


@router.get(
    "/verifications/{verification_id}/audit",
    response_model=List[VerificationAuditLogResponse],
    summary="Get chronological audit trail for a verification",
)
def get_verification_audit(
    verification_id: int, db: Session = Depends(get_db)
):
    verification = verification_service.get_verification_by_id(db, verification_id)
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification with ID {verification_id} not found.",
        )
    return verification_service.get_verification_audit_logs(db, verification_id)


@router.get(
    "/tasks/{task_id}/verification",
    response_model=VerificationDetailResponse,
    summary="Get the latest verification record for a task",
)
def get_task_verification_endpoint(
    task_id: int, db: Session = Depends(get_db)
):
    verification = verification_service.get_task_verification(db, task_id)
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No verification found for task #{task_id}.",
        )
    return verification


@router.get(
    "/submissions/{submission_id}/verification",
    response_model=VerificationDetailResponse,
    summary="Get verification record for a result submission",
)
def get_submission_verification_endpoint(
    submission_id: int, db: Session = Depends(get_db)
):
    verification = verification_service.get_submission_verification(
        db, submission_id
    )
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No verification found for submission #{submission_id}.",
        )
    return verification


@router.get(
    "/verifications",
    response_model=List[VerificationResponse],
    summary="List verification history records",
)
def list_verifications_endpoint(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return verification_service.list_verifications(db, limit=limit, offset=offset)
