"""
Phase 11 — Escrow API Router.
Endpoints for retrieving and managing Escrow accounts and audit trails.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from app.models.escrow import Escrow, EscrowAuditLog
from app.models.task import Task
from app.models.agent import Agent
from app.models.wallet import Wallet
from app.models.verification import Verification
from app.services import escrow_service

router = APIRouter(prefix="/api", tags=["Escrows"])


def _enrich_escrow(escrow: Escrow, db: Session) -> dict:
    """Enrich an Escrow ORM object with human-readable cross-references."""
    task = db.query(Task).filter(Task.id == escrow.task_id).first()
    worker = db.query(Agent).filter(Agent.id == escrow.worker_agent_id).first()
    req_wallet = db.query(Wallet).filter(Wallet.id == escrow.requester_wallet_id).first()
    wrk_wallet = db.query(Wallet).filter(Wallet.id == escrow.worker_wallet_id).first()
    verification = None
    if escrow.verification_id:
        verification = db.query(Verification).filter(Verification.id == escrow.verification_id).first()

    return {
        "id": escrow.id,
        "escrow_code": escrow.escrow_code,
        "task_id": escrow.task_id,
        "task_code": task.task_code if task else None,
        "task_title": task.title if task else None,
        "requester_wallet_id": escrow.requester_wallet_id,
        "requester_wallet_code": req_wallet.wallet_code if req_wallet else None,
        "worker_agent_id": escrow.worker_agent_id,
        "worker_agent_name": worker.name if worker else None,
        "worker_agent_code": worker.agent_code if worker else None,
        "worker_wallet_id": escrow.worker_wallet_id,
        "worker_wallet_code": wrk_wallet.wallet_code if wrk_wallet else None,
        "verification_id": escrow.verification_id,
        "verification_decision": verification.decision if verification else None,
        "reward_amount": escrow.reward_amount,
        "status": escrow.status,
        "locked_at": escrow.locked_at,
        "releasable_at": escrow.releasable_at,
        "released_at": escrow.released_at,
        "refunded_at": escrow.refunded_at,
        "created_at": escrow.created_at,
        "updated_at": escrow.updated_at,
    }


@router.get("/escrows/summary")
def get_escrow_summary(db: Session = Depends(get_db)):
    """
    Return aggregate AP Credit escrow stats across all escrow accounts.
    """
    return escrow_service.get_escrow_summary(db)


@router.get("/escrows")
def list_escrows(
    status: Optional[str] = Query(None, description="Filter by status"),
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    db: Session = Depends(get_db),
):
    """List all escrows with optional filtering."""
    escrows = escrow_service.list_escrows(db, status_filter=status, task_id=task_id)
    return [_enrich_escrow(e, db) for e in escrows]


@router.get("/escrows/{escrow_id}/audit")
def get_escrow_audit(escrow_id: int, db: Session = Depends(get_db)):
    """Return chronological audit log for an escrow account."""
    escrow = escrow_service.get_escrow(db, escrow_id)
    if not escrow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escrow with id {escrow_id} not found.",
        )
    logs = escrow_service.get_escrow_audit_logs(db, escrow_id)
    return [
        {
            "id": log.id,
            "escrow_id": log.escrow_id,
            "action": log.action,
            "actor_type": log.actor_type,
            "actor_id": log.actor_id,
            "message": log.message,
            "amount": log.amount,
            "created_at": log.created_at,
        }
        for log in logs
    ]


@router.get("/escrows/{escrow_id}")
def get_escrow(escrow_id: int, db: Session = Depends(get_db)):
    """Retrieve escrow by ID with full enriched data."""
    escrow = escrow_service.get_escrow(db, escrow_id)
    if not escrow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escrow with id {escrow_id} not found.",
        )
    return _enrich_escrow(escrow, db)


@router.get("/tasks/{task_id}/escrow")
def get_task_escrow(task_id: int, db: Session = Depends(get_db)):
    """Get the escrow linked to a specific task."""
    escrow = escrow_service.get_task_escrow(db, task_id)
    if not escrow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No escrow found for task {task_id}.",
        )
    return _enrich_escrow(escrow, db)


@router.post("/tasks/{task_id}/escrow/initialize")
def initialize_task_escrow(task_id: int, db: Session = Depends(get_db)):
    """
    Backfill escrow for an already-assigned task that has no escrow yet.
    Only usable when task is assigned and escrow is missing.
    Idempotent — will 409 if escrow already exists.
    """
    escrow = escrow_service.initialize_escrow_for_assigned_task(db, task_id)
    return _enrich_escrow(escrow, db)
