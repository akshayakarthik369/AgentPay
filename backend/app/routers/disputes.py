from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db

from app.schemas.dispute import (
    DisputeCreatePayload,
    DisputeEvidenceCreatePayload,
    DisputeEvidenceResponse,
    DisputeAuditLogResponse,
    DisputeResponse,
)
from app.services import dispute_service

router = APIRouter(tags=["disputes"])

@router.post(
    "/api/disputes",
    response_model=DisputeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Raise a new dispute for a failed outcome",
)
def create_dispute(
    payload: DisputeCreatePayload,
    db: Session = Depends(get_db),
):
    return dispute_service.create_dispute(
        db=db,
        task_id=payload.task_id,
        reason=payload.reason,
        description=payload.description,
        raised_by_type=payload.raised_by_type,
        raised_by_id=payload.raised_by_id,
        initial_evidence_title=payload.initial_evidence_title,
        initial_evidence_description=payload.initial_evidence_description,
        initial_evidence_data=payload.initial_evidence_data,
    )

@router.get(
    "/api/disputes",
    response_model=List[DisputeResponse],
    summary="List disputes with optional status and task filters",
)
def list_disputes(
    status: Optional[str] = Query(None, description="Filter by status: open, evidence_pending, ready_for_arbitration, under_arbitration, resolved, rejected, cancelled"),
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    db: Session = Depends(get_db),
):
    return dispute_service.list_disputes(db, status_filter=status, task_id=task_id)

@router.get(
    "/api/disputes/{id}",
    response_model=DisputeResponse,
    summary="Get dispute by ID",
)
def get_dispute(
    id: int,
    db: Session = Depends(get_db),
):
    dispute = dispute_service.get_dispute(db, dispute_id=id)
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute with id {id} not found."
        )
    return dispute

@router.get(
    "/api/tasks/{task_id}/dispute",
    response_model=DisputeResponse,
    summary="Get dispute for a specific task",
)
def get_dispute_by_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    dispute = dispute_service.get_dispute_by_task(db, task_id=task_id)
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No dispute found for task {task_id}."
        )
    return dispute

@router.post(
    "/api/disputes/{id}/evidence",
    response_model=DisputeEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Append immutable evidence to an active dispute",
)
def add_evidence(
    id: int,
    payload: DisputeEvidenceCreatePayload,
    db: Session = Depends(get_db),
):
    return dispute_service.add_evidence(
        db=db,
        dispute_id=id,
        title=payload.title,
        description=payload.description,
        evidence_data=payload.evidence_data,
        submitted_by_type=payload.submitted_by_type,
        submitted_by_id=payload.submitted_by_id,
    )

@router.post(
    "/api/disputes/{id}/ready",
    response_model=DisputeResponse,
    summary="Mark dispute as ready for arbitration",
)
def mark_ready_for_arbitration(
    id: int,
    db: Session = Depends(get_db),
):
    return dispute_service.mark_ready_for_arbitration(db, dispute_id=id)

@router.post(
    "/api/disputes/{id}/cancel",
    response_model=DisputeResponse,
    summary="Cancel an active dispute",
)
def cancel_dispute(
    id: int,
    db: Session = Depends(get_db),
):
    return dispute_service.cancel_dispute(db, dispute_id=id)

@router.get(
    "/api/disputes/{id}/evidence",
    response_model=List[DisputeEvidenceResponse],
    summary="Get all submitted evidence for a dispute",
)
def get_dispute_evidence(
    id: int,
    db: Session = Depends(get_db),
):
    dispute = dispute_service.get_dispute(db, dispute_id=id)
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute with id {id} not found."
        )
    return dispute_service.get_dispute_evidence_list(db, dispute_id=id)

@router.get(
    "/api/disputes/{id}/audit",
    response_model=List[DisputeAuditLogResponse],
    summary="Get dispute audit history",
)
def get_dispute_audit(
    id: int,
    db: Session = Depends(get_db),
):
    dispute = dispute_service.get_dispute(db, dispute_id=id)
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute with id {id} not found."
        )
    return dispute_service.get_dispute_audit_logs(db, dispute_id=id)
