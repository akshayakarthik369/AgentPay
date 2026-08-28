from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db

from app.schemas.arbitration import (
    ArbitrationTriggerPayload,
    ArbitrationAuditLogResponse,
    ArbitrationResponse,
)
from app.services import arbitration_service

router = APIRouter(tags=["arbitrations"])

@router.post(
    "/api/disputes/{id}/arbitrate",
    response_model=ArbitrationResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger and execute AI arbitration on a dispute",
)
def trigger_arbitration(
    id: int,
    payload: Optional[ArbitrationTriggerPayload] = None,
    db: Session = Depends(get_db),
):
    force_dec = payload.force_decision if payload else None
    notes = payload.notes if payload else None
    return arbitration_service.run_arbitration(
        db=db,
        dispute_id=id,
        force_decision=force_dec,
        notes=notes,
    )

@router.get(
    "/api/arbitrations",
    response_model=List[ArbitrationResponse],
    summary="List all arbitrations with optional status filter",
)
def list_arbitrations(
    status: Optional[str] = Query(None, description="Filter by status: pending, running, resolved, failed"),
    db: Session = Depends(get_db),
):
    return arbitration_service.list_arbitrations(db, status_filter=status)

@router.get(
    "/api/arbitrations/{id}",
    response_model=ArbitrationResponse,
    summary="Get arbitration by ID",
)
def get_arbitration(
    id: int,
    db: Session = Depends(get_db),
):
    arbitration = arbitration_service.get_arbitration(db, arbitration_id=id)
    if not arbitration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arbitration with id {id} not found."
        )
    return arbitration

@router.get(
    "/api/disputes/{id}/arbitration",
    response_model=ArbitrationResponse,
    summary="Get arbitration for a specific dispute",
)
def get_arbitration_by_dispute(
    id: int,
    db: Session = Depends(get_db),
):
    arbitration = arbitration_service.get_arbitration_by_dispute(db, dispute_id=id)
    if not arbitration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No arbitration record found for dispute {id}."
        )
    return arbitration

@router.get(
    "/api/arbitrations/{id}/audit",
    response_model=List[ArbitrationAuditLogResponse],
    summary="Get arbitration audit timeline",
)
def get_arbitration_audit(
    id: int,
    db: Session = Depends(get_db),
):
    arbitration = arbitration_service.get_arbitration(db, arbitration_id=id)
    if not arbitration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arbitration with id {id} not found."
        )
    return arbitration_service.get_arbitration_audit_logs(db, arbitration_id=id)
