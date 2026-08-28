from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.escrow import Escrow, EscrowAuditLog
from app.models.task import Task
from app.models.agent import Agent
from app.models.verification import Verification
from app.services import wallet_service


def _generate_escrow_code(db: Session) -> str:
    """Generate next sequential escrow code like ES-1001."""
    last_escrow = db.query(Escrow).order_by(Escrow.id.desc()).first()
    next_id = (last_escrow.id + 1) if last_escrow else 1
    return f"ES-{1000 + next_id}"


def _log_escrow_audit(
    db: Session,
    escrow_id: int,
    action: str,
    actor_type: str,
    message: str,
    actor_id: Optional[str] = None,
    amount: Optional[float] = None,
) -> EscrowAuditLog:
    """Helper to record immutable audit log entries for escrow events."""
    log_entry = EscrowAuditLog(
        escrow_id=escrow_id,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        message=message,
        amount=amount,
        created_at=datetime.utcnow(),
    )
    db.add(log_entry)
    return log_entry


def create_escrow_for_task(
    db: Session,
    task: Task,
    worker_agent_id: int,
    reward_amount: float,
) -> Escrow:
    """
    Atomically creates an Escrow account and reserves the task reward amount
    from the Requester Wallet.
    Participates in the parent DB transaction.
    """
    # 1. Check for duplicate escrow on this task
    existing_escrow = db.query(Escrow).filter(Escrow.task_id == task.id).first()
    if existing_escrow:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Escrow account {existing_escrow.escrow_code} already exists for task {task.task_code}.",
        )

    # 2. Get or create requester and worker wallets
    requester_wallet = wallet_service.get_or_create_requester_wallet(db)
    worker_wallet = wallet_service.get_or_create_agent_wallet(db, worker_agent_id)

    # 3. Validate reward
    if reward_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task reward amount must be strictly greater than 0 AP Credits.",
        )

    # 4. Lock balance from requester wallet (raises 400 if insufficient)
    wallet_service.lock_balance(db, requester_wallet.id, reward_amount)

    # 5. Create Escrow record
    now = datetime.utcnow()
    escrow_code = _generate_escrow_code(db)
    escrow = Escrow(
        escrow_code=escrow_code,
        task_id=task.id,
        requester_wallet_id=requester_wallet.id,
        worker_agent_id=worker_agent_id,
        worker_wallet_id=worker_wallet.id,
        reward_amount=reward_amount,
        status="locked",
        locked_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(escrow)
    db.flush()

    # 6. Record Audit Trails
    _log_escrow_audit(
        db,
        escrow.id,
        action="escrow_created",
        actor_type="system",
        actor_id="AgentPay-Trust-Layer",
        message=f"Escrow account {escrow_code} established for task {task.task_code}.",
        amount=reward_amount,
    )

    _log_escrow_audit(
        db,
        escrow.id,
        action="reward_locked",
        actor_type="requester",
        actor_id=requester_wallet.wallet_code,
        message=f"{reward_amount} AP Credits locked in escrow from Requester Wallet {requester_wallet.wallet_code}.",
        amount=reward_amount,
    )

    return escrow


def get_task_escrow(db: Session, task_id: int) -> Optional[Escrow]:
    """Retrieve escrow associated with a task."""
    return db.query(Escrow).filter(Escrow.task_id == task_id).first()


def get_escrow(db: Session, escrow_id: int) -> Optional[Escrow]:
    """Retrieve escrow by primary ID."""
    return db.query(Escrow).filter(Escrow.id == escrow_id).first()


def get_escrow_by_code(db: Session, escrow_code: str) -> Optional[Escrow]:
    """Retrieve escrow by unique code."""
    return db.query(Escrow).filter(Escrow.escrow_code == escrow_code).first()


def list_escrows(
    db: Session,
    status_filter: Optional[str] = None,
    task_id: Optional[int] = None,
) -> List[Escrow]:
    """List escrows with optional filtering."""
    query = db.query(Escrow)
    if status_filter and status_filter.lower() != "all":
        query = query.filter(Escrow.status == status_filter.lower())
    if task_id:
        query = query.filter(Escrow.task_id == task_id)
    return query.order_by(Escrow.id.desc()).all()


def get_escrow_summary(db: Session) -> Dict[str, Any]:
    """Calculate aggregate stats across all escrows."""
    escrows = db.query(Escrow).all()
    
    total_locked = 0.0
    total_releasable = 0.0
    total_blocked = 0.0
    total_released = 0.0

    count_locked = 0
    count_releasable = 0
    count_blocked = 0
    count_released = 0

    for esc in escrows:
        if esc.status in ("locked", "awaiting_verification"):
            total_locked += esc.reward_amount
            count_locked += 1
        elif esc.status == "releasable":
            total_releasable += esc.reward_amount
            count_releasable += 1
        elif esc.status in ("blocked", "awaiting_review"):
            total_blocked += esc.reward_amount
            count_blocked += 1
        elif esc.status == "released":
            total_released += esc.reward_amount
            count_released += 1

    return {
        "total_locked": total_locked,
        "total_releasable": total_releasable,
        "total_blocked": total_blocked,
        "total_released": total_released,
        "count_locked": count_locked,
        "count_releasable": count_releasable,
        "count_blocked": count_blocked,
        "count_released": count_released,
        "count_total": len(escrows),
    }


def update_escrow_from_verification(
    db: Session,
    verification_id: int,
    decision: str,
) -> Optional[Escrow]:
    """
    Updates linked Escrow status based on Phase 10 verification decision:
      - PASS   -> releasable (releasable_at timestamped)
      - FAIL   -> blocked
      - REVIEW -> blocked (reason: human review required)
    
    CRITICAL PHASE 11 BOUNDARY:
      Does NOT transfer AP Credits.
      Does NOT credit worker wallet.
      Settlement release is Phase 12.
    """
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        return None

    escrow = db.query(Escrow).filter(Escrow.task_id == verification.task_id).first()
    if not escrow:
        return None

    now = datetime.utcnow()
    escrow.verification_id = verification_id
    escrow.updated_at = now

    decision_upper = decision.upper() if decision else "UNKNOWN"

    if decision_upper == "PASS":
        escrow.status = "releasable"
        escrow.releasable_at = now
        _log_escrow_audit(
            db,
            escrow.id,
            action="verification_passed",
            actor_type="verifier",
            actor_id=str(verification.verifier_agent_id),
            message=f"Verification {verification.verification_code or verification.id} passed with score {verification.overall_score:.1f}/100.",
            amount=escrow.reward_amount,
        )
        _log_escrow_audit(
            db,
            escrow.id,
            action="marked_releasable",
            actor_type="system",
            actor_id="AgentPay-Trust-Layer",
            message="Escrow marked as Releasable. Payout ready for Phase 12 automated settlement.",
            amount=escrow.reward_amount,
        )

    elif decision_upper == "FAIL":
        escrow.status = "blocked"
        _log_escrow_audit(
            db,
            escrow.id,
            action="verification_failed",
            actor_type="verifier",
            actor_id=str(verification.verifier_agent_id),
            message=f"Verification {verification.verification_code or verification.id} failed with score {verification.overall_score:.1f}/100.",
            amount=escrow.reward_amount,
        )
        _log_escrow_audit(
            db,
            escrow.id,
            action="blocked",
            actor_type="system",
            actor_id="AgentPay-Trust-Layer",
            message="Escrow payout blocked. Deliverable did not satisfy verification criteria.",
            amount=escrow.reward_amount,
        )

    else:  # REVIEW
        escrow.status = "blocked"
        _log_escrow_audit(
            db,
            escrow.id,
            action="review_required",
            actor_type="verifier",
            actor_id=str(verification.verifier_agent_id),
            message="Verification flagged outcome as borderline. Human arbitrator review required.",
            amount=escrow.reward_amount,
        )
        _log_escrow_audit(
            db,
            escrow.id,
            action="blocked",
            actor_type="system",
            actor_id="AgentPay-Trust-Layer",
            message="Escrow locked and blocked pending human dispute resolution.",
            amount=escrow.reward_amount,
        )

    db.flush()
    return escrow


def get_escrow_audit_logs(db: Session, escrow_id: int) -> List[EscrowAuditLog]:
    """Retrieve chronological audit logs for an escrow account."""
    return (
        db.query(EscrowAuditLog)
        .filter(EscrowAuditLog.escrow_id == escrow_id)
        .order_by(EscrowAuditLog.id.asc())
        .all()
    )


def initialize_escrow_for_assigned_task(db: Session, task_id: int) -> Escrow:
    """
    Backfill helper to initialize an escrow for an already-assigned task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found.",
        )

    if not task.assigned_agent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot initialize escrow: task is not assigned to any agent.",
        )

    existing = db.query(Escrow).filter(Escrow.task_id == task_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Escrow {existing.escrow_code} already exists for task {task.task_code}.",
        )

    escrow = create_escrow_for_task(
        db,
        task=task,
        worker_agent_id=task.assigned_agent_id,
        reward_amount=task.reward,
    )
    db.commit()
    db.refresh(escrow)
    return escrow
