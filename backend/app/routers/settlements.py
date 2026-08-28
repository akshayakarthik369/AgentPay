"""
Phase 12 — Settlement API Router.
Endpoints for managing conditional automatic settlement, audit logs, and double-entry ledger.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from app.models.settlement import Settlement, SettlementAuditLog, LedgerEntry
from app.models.task import Task
from app.models.agent import Agent
from app.models.wallet import Wallet
from app.models.escrow import Escrow
from app.models.verification import Verification
from app.schemas.settlement import (
    SettlementResponse,
    SettlementAuditLogResponse,
    LedgerEntryResponse,
    SettlementSummaryResponse,
)
from app.services import settlement_service

router = APIRouter(prefix="/api", tags=["Settlements"])


def _enrich_settlement(s: Settlement, db: Session) -> dict:
    """Enrich a Settlement model with human-readable cross-references."""
    task = db.query(Task).filter(Task.id == s.task_id).first()
    escrow = db.query(Escrow).filter(Escrow.id == s.escrow_id).first()
    verification = (
        db.query(Verification).filter(Verification.id == s.verification_id).first()
        if s.verification_id
        else None
    )
    req_wallet = db.query(Wallet).filter(Wallet.id == s.requester_wallet_id).first()
    wrk_wallet = db.query(Wallet).filter(Wallet.id == s.worker_wallet_id).first()
    worker = db.query(Agent).filter(Agent.id == s.worker_agent_id).first()

    return {
        "id": s.id,
        "settlement_code": s.settlement_code,
        "task_id": s.task_id,
        "task_code": task.task_code if task else None,
        "task_title": task.title if task else None,
        "escrow_id": s.escrow_id,
        "escrow_code": escrow.escrow_code if escrow else None,
        "verification_id": s.verification_id,
        "verification_code": verification.verification_code if verification else None,
        "requester_wallet_id": s.requester_wallet_id,
        "requester_wallet_code": req_wallet.wallet_code if req_wallet else None,
        "worker_wallet_id": s.worker_wallet_id,
        "worker_wallet_code": wrk_wallet.wallet_code if wrk_wallet else None,
        "worker_agent_id": s.worker_agent_id,
        "worker_agent_name": worker.name if worker else None,
        "worker_agent_code": worker.agent_code if worker else None,
        "amount": s.amount,
        "currency": s.currency,
        "status": s.status,
        "trigger_type": s.trigger_type,
        "verification_decision": s.verification_decision,
        "integrity_verified": s.integrity_verified,
        "failure_reason": s.failure_reason,
        "created_at": s.created_at,
        "started_at": s.started_at,
        "completed_at": s.completed_at,
        "failed_at": s.failed_at,
        "updated_at": s.updated_at,
    }


@router.get("/settlements/summary", response_model=SettlementSummaryResponse)
def get_settlement_summary(db: Session = Depends(get_db)):
    """Aggregate financial and settlement statistics."""
    return settlement_service.get_settlement_summary(db)


@router.get("/settlements")
def list_settlements(
    status: Optional[str] = Query(None, description="Filter by status"),
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    db: Session = Depends(get_db),
):
    """List all settlements with optional filtering."""
    items = settlement_service.list_settlements(db, status_filter=status, task_id=task_id)
    return [_enrich_settlement(s, db) for s in items]


@router.get("/settlements/{settlement_id}")
def get_settlement(settlement_id: int, db: Session = Depends(get_db)):
    """Retrieve detailed settlement by ID."""
    s = settlement_service.get_settlement(db, settlement_id)
    if not s:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settlement with id {settlement_id} not found.",
        )
    return _enrich_settlement(s, db)


@router.get("/tasks/{task_id}/settlement")
def get_task_settlement(task_id: int, db: Session = Depends(get_db)):
    """Get the settlement associated with a task."""
    s = settlement_service.get_task_settlement(db, task_id)
    if not s:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No settlement found for task {task_id}.",
        )
    return _enrich_settlement(s, db)


@router.get("/escrows/{escrow_id}/settlement")
def get_escrow_settlement(escrow_id: int, db: Session = Depends(get_db)):
    """Get the settlement associated with an escrow account."""
    s = settlement_service.get_escrow_settlement(db, escrow_id)
    if not s:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No settlement found for escrow {escrow_id}.",
        )
    return _enrich_settlement(s, db)


@router.get("/settlements/{settlement_id}/audit", response_model=List[SettlementAuditLogResponse])
def get_settlement_audit(settlement_id: int, db: Session = Depends(get_db)):
    """Get chronological audit log for a settlement."""
    s = settlement_service.get_settlement(db, settlement_id)
    if not s:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settlement with id {settlement_id} not found.",
        )
    return settlement_service.get_settlement_audit_logs(db, settlement_id)


@router.get("/settlements/{settlement_id}/ledger", response_model=List[LedgerEntryResponse])
def get_settlement_ledger(settlement_id: int, db: Session = Depends(get_db)):
    """Get double-entry ledger entries for a settlement."""
    s = settlement_service.get_settlement(db, settlement_id)
    if not s:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settlement with id {settlement_id} not found.",
        )
    return settlement_service.get_settlement_ledger_entries(db, settlement_id)


@router.post("/escrows/{escrow_id}/settle")
def settle_escrow_manual_trigger(escrow_id: int, db: Session = Depends(get_db)):
    """
    Demo/Manual trigger for escrow settlement:
      - Validates all conditional eligibility rules
      - Executes atomic settlement if escrow is releasable
      - Idempotent: returns existing completed settlement if already completed
    """
    escrow = db.query(Escrow).filter(Escrow.id == escrow_id).first()
    if not escrow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escrow with id {escrow_id} not found.",
        )

    settlement = settlement_service.create_settlement(db, escrow_id, trigger_type="manual")
    settlement = settlement_service.execute_settlement(db, settlement.id)
    return _enrich_settlement(settlement, db)


@router.post("/settlements/{settlement_id}/retry")
def retry_settlement(settlement_id: int, db: Session = Depends(get_db)):
    """Retry a failed settlement transaction."""
    settlement = settlement_service.retry_failed_settlement(db, settlement_id)
    return _enrich_settlement(settlement, db)
