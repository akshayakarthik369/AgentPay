"""
Phase 12 — Settlement Service for AgentPay.
Manages automatic, conditional, and auditable AP Credit settlement:
  Verification PASS -> Escrow Releasable -> Atomic Settlement -> AP Credits Transferred
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.settlement import Settlement, SettlementAuditLog, LedgerEntry
from app.models.escrow import Escrow, EscrowAuditLog
from app.models.task import Task
from app.models.agent import Agent
from app.models.wallet import Wallet
from app.models.verification import Verification
from app.models.result_submission import ResultSubmission
from app.models.dispute import Dispute
from app.services import wallet_service
from app.services import reputation_service


def _generate_settlement_code(db: Session) -> str:
    """Generate sequential code like ST-1001."""
    last_item = db.query(Settlement).order_by(Settlement.id.desc()).first()
    next_id = (last_item.id + 1) if last_item else 1
    return f"ST-{1000 + next_id}"


def _generate_ledger_code(db: Session) -> str:
    """Generate sequential code like LE-1001."""
    last_item = db.query(LedgerEntry).order_by(LedgerEntry.id.desc()).first()
    next_id = (last_item.id + 1) if last_item else 1
    return f"LE-{1000 + next_id}"


def _log_settlement_audit(
    db: Session,
    settlement_id: int,
    action: str,
    actor_type: str,
    message: str,
    actor_id: Optional[str] = None,
    amount: Optional[float] = None,
    previous_status: Optional[str] = None,
    new_status: Optional[str] = None,
) -> SettlementAuditLog:
    """Helper to record audit trail entries."""
    log = SettlementAuditLog(
        settlement_id=settlement_id,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        amount=amount,
        previous_status=previous_status,
        new_status=new_status,
        message=message,
        created_at=datetime.utcnow(),
    )
    db.add(log)
    return log


def _create_ledger_entry(
    db: Session,
    settlement_id: Optional[int],
    escrow_id: Optional[int],
    task_id: Optional[int],
    wallet_id: int,
    entry_type: str,
    amount: float,
    balance_type: str,
    description: str,
) -> LedgerEntry:
    """Create an immutable double-entry style financial record."""
    entry_code = _generate_ledger_code(db)
    entry = LedgerEntry(
        entry_code=entry_code,
        settlement_id=settlement_id,
        escrow_id=escrow_id,
        task_id=task_id,
        wallet_id=wallet_id,
        entry_type=entry_type,
        amount=amount,
        balance_type=balance_type,
        description=description,
        created_at=datetime.utcnow(),
    )
    db.add(entry)
    db.flush()
    return entry


def check_settlement_eligibility(db: Session, escrow_id: int) -> Dict[str, Any]:
    """
    Evaluates ALL conditional gates before settlement can occur:
      1. Escrow exists
      2. Escrow status is 'releasable'
      3. Task exists and has assigned worker
      4. Verification exists and decision == 'PASS'
      5. Submission integrity is valid
      6. Requester & Worker wallets exist
      7. Escrow reward amount > 0
      8. Requester locked balance >= reward amount
      9. Escrow not already released
      10. No completed settlement already exists for this escrow
    """
    escrow = db.query(Escrow).filter(Escrow.id == escrow_id).first()
    if not escrow:
        return {"eligible": False, "reason": f"Escrow with id {escrow_id} not found"}

    task = db.query(Task).filter(Task.id == escrow.task_id).first()
    if not task:
        return {"eligible": False, "reason": f"Task with id {escrow.task_id} not found"}

    # Active Dispute Check — immediate priority pause
    active_dispute = (
        db.query(Dispute)
        .filter(
            Dispute.task_id == task.id,
            Dispute.status.in_(["open", "evidence_pending", "ready_for_arbitration", "under_arbitration"]),
        )
        .first()
    )
    if active_dispute:
        return {
            "eligible": False,
            "reason": f"Active dispute {active_dispute.dispute_code or active_dispute.id} is open. Settlement is paused pending arbitration.",
        }

    if escrow.status == "released":
        return {"eligible": False, "reason": "Escrow reward has already been released"}

    if escrow.status != "releasable":
        return {
            "eligible": False,
            "reason": f"Escrow status is '{escrow.status}'. Settlement requires status 'releasable'.",
        }

    if not task.assigned_agent_id:
        return {"eligible": False, "reason": "Task has no assigned worker agent"}

    verification = None
    if escrow.verification_id:
        verification = db.query(Verification).filter(Verification.id == escrow.verification_id).first()
    else:
        # Fallback query by task_id
        verification = db.query(Verification).filter(Verification.task_id == task.id).order_by(Verification.id.desc()).first()

    if not verification:
        return {"eligible": False, "reason": "No independent verification record found for task"}

    if verification.decision != "PASS":
        return {
            "eligible": False,
            "reason": f"Verification decision is '{verification.decision}'. Settlement requires PASS.",
        }

    # Verify submission integrity
    submission = None
    if verification and not getattr(verification, "integrity_valid", True):
        return {"eligible": False, "reason": "Submission package integrity validation failed"}

    if verification.submission_id:
        submission = db.query(ResultSubmission).filter(ResultSubmission.id == verification.submission_id).first()
    else:
        submission = db.query(ResultSubmission).filter(ResultSubmission.task_id == task.id).order_by(ResultSubmission.id.desc()).first()

    if submission and not submission.is_locked:
        return {"eligible": False, "reason": "Submission package is not locked"}

    # Check wallets
    req_wallet = db.query(Wallet).filter(Wallet.id == escrow.requester_wallet_id).first()
    if not req_wallet:
        return {"eligible": False, "reason": "Requester wallet not found"}

    wrk_wallet = db.query(Wallet).filter(Wallet.id == escrow.worker_wallet_id).first()
    if not wrk_wallet:
        return {"eligible": False, "reason": "Worker wallet not found"}

    if escrow.reward_amount <= 0:
        return {"eligible": False, "reason": "Escrow reward amount must be strictly greater than 0 AP"}

    if req_wallet.locked_balance < escrow.reward_amount:
        return {
            "eligible": False,
            "reason": f"Insufficient requester locked balance ({req_wallet.locked_balance} AP < {escrow.reward_amount} AP)",
        }

    return {
        "eligible": True,
        "reason": "All settlement conditions met. Escrow is eligible for release.",
        "escrow": escrow,
        "task": task,
        "verification": verification,
        "submission": submission,
        "requester_wallet": req_wallet,
        "worker_wallet": wrk_wallet,
    }


def create_settlement(
    db: Session,
    escrow_id: int,
    trigger_type: str = "automatic",
) -> Settlement:
    """
    Creates a pending Settlement record for an escrow account (idempotent).
    """
    # Check if settlement already exists for this escrow
    existing = db.query(Settlement).filter(Settlement.escrow_id == escrow_id).first()
    if existing:
        return existing

    escrow = db.query(Escrow).filter(Escrow.id == escrow_id).first()
    if not escrow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Escrow with id {escrow_id} not found.",
        )

    task = db.query(Task).filter(Task.id == escrow.task_id).first()
    verification = (
        db.query(Verification).filter(Verification.id == escrow.verification_id).first()
        if escrow.verification_id
        else db.query(Verification).filter(Verification.task_id == escrow.task_id).order_by(Verification.id.desc()).first()
    )

    submission = (
        db.query(ResultSubmission).filter(ResultSubmission.id == verification.submission_id).first()
        if verification and verification.submission_id
        else None
    )

    now = datetime.utcnow()
    settlement_code = _generate_settlement_code(db)
    
    settlement = Settlement(
        settlement_code=settlement_code,
        task_id=escrow.task_id,
        escrow_id=escrow.id,
        verification_id=verification.id if verification else None,
        requester_wallet_id=escrow.requester_wallet_id,
        worker_wallet_id=escrow.worker_wallet_id,
        worker_agent_id=escrow.worker_agent_id,
        amount=escrow.reward_amount,
        currency="AP",
        status="pending",
        trigger_type=trigger_type,
        verification_decision=verification.decision if verification else None,
        integrity_verified=getattr(verification, "integrity_valid", True) if verification else True,
        created_at=now,
        updated_at=now,
    )
    db.add(settlement)
    db.flush()

    _log_settlement_audit(
        db,
        settlement_id=settlement.id,
        action="settlement_created",
        actor_type="system",
        actor_id="AgentPay-Settlement-Engine",
        amount=settlement.amount,
        previous_status=None,
        new_status="pending",
        message=f"Settlement {settlement_code} created for task {task.task_code if task else escrow.task_id} ({settlement.amount} AP).",
    )

    db.commit()
    db.refresh(settlement)
    return settlement


def execute_settlement(db: Session, settlement_id: int) -> Settlement:
    """
    Executes the settlement as ONE atomic database transaction:
      1. Check eligibility & duplicate payment guards
      2. Debit Requester locked_balance -= amount, total_spent += amount
      3. Credit Worker available_balance += amount, total_earned += amount
      4. Set Escrow status = 'released', released_at = now
      5. Set Task status = 'completed'
      6. Record immutable double-entry Ledger entries
      7. Record audit trail events
      8. Set Settlement status = 'completed', completed_at = now
    Rolls back completely if any failure occurs.
    """
    settlement = (
        db.query(Settlement)
        .filter(Settlement.id == settlement_id)
        .with_for_update()
        .first()
    )
    if not settlement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settlement with id {settlement_id} not found.",
        )

    # Idempotency: if already completed, return as-is
    if settlement.status == "completed":
        return settlement

    # Evaluate eligibility
    eligibility = check_settlement_eligibility(db, settlement.escrow_id)
    if not eligibility["eligible"]:
        reason = eligibility["reason"]
        settlement.status = "blocked"
        settlement.failure_reason = reason
        settlement.updated_at = datetime.utcnow()
        _log_settlement_audit(
            db,
            settlement_id=settlement.id,
            action="settlement_blocked",
            actor_type="system",
            actor_id="AgentPay-Settlement-Engine",
            amount=settlement.amount,
            previous_status="pending",
            new_status="blocked",
            message=f"Settlement blocked: {reason}",
        )
        db.commit()
        db.refresh(settlement)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Settlement cannot execute: {reason}",
        )

    now = datetime.utcnow()
    settlement.status = "processing"
    settlement.started_at = now
    settlement.updated_at = now

    _log_settlement_audit(
        db,
        settlement_id=settlement.id,
        action="settlement_started",
        actor_type="system",
        actor_id="AgentPay-Settlement-Engine",
        amount=settlement.amount,
        previous_status="pending",
        new_status="processing",
        message="Conditional settlement execution started.",
    )

    try:
        # 1. Execute wallet transfer (atomic within current session)
        req_wallet, wrk_wallet = wallet_service.settle_transfer(
            db,
            requester_wallet_id=settlement.requester_wallet_id,
            worker_wallet_id=settlement.worker_wallet_id,
            amount=settlement.amount,
        )

        _log_settlement_audit(
            db,
            settlement_id=settlement.id,
            action="requester_locked_balance_debited",
            actor_type="requester",
            actor_id=req_wallet.wallet_code,
            amount=settlement.amount,
            message=f"{settlement.amount} AP debited from Requester locked balance. Total spent: {req_wallet.total_spent} AP.",
        )

        _log_settlement_audit(
            db,
            settlement_id=settlement.id,
            action="worker_wallet_credited",
            actor_type="agent",
            actor_id=wrk_wallet.wallet_code,
            amount=settlement.amount,
            message=f"{settlement.amount} AP credited to Worker available balance. Total earned: {wrk_wallet.total_earned} AP.",
        )

        # 2. Release Escrow
        escrow = db.query(Escrow).filter(Escrow.id == settlement.escrow_id).with_for_update().first()
        escrow.status = "released"
        escrow.released_at = now
        escrow.updated_at = now

        # Add escrow audit log
        escrow_log = EscrowAuditLog(
            escrow_id=escrow.id,
            action="escrow_released",
            actor_type="system",
            actor_id="AgentPay-Settlement-Engine",
            amount=settlement.amount,
            message=f"Escrow released via Settlement {settlement.settlement_code}. {settlement.amount} AP transferred to worker.",
            created_at=now,
        )
        db.add(escrow_log)

        # 3. Complete Task
        task = db.query(Task).filter(Task.id == settlement.task_id).with_for_update().first()
        if task:
            task.status = "completed"
            task.updated_at = now

        # 4. Double-Entry Ledger Records
        _create_ledger_entry(
            db,
            settlement_id=settlement.id,
            escrow_id=escrow.id,
            task_id=task.id if task else None,
            wallet_id=req_wallet.id,
            entry_type="settlement_debit",
            amount=settlement.amount,
            balance_type="locked",
            description=f"Settlement {settlement.settlement_code}: {settlement.amount} AP debited from locked balance for task {task.task_code if task else ''}.",
        )

        _create_ledger_entry(
            db,
            settlement_id=settlement.id,
            escrow_id=escrow.id,
            task_id=task.id if task else None,
            wallet_id=wrk_wallet.id,
            entry_type="settlement_credit",
            amount=settlement.amount,
            balance_type="available",
            description=f"Settlement {settlement.settlement_code}: {settlement.amount} AP credited to available balance for completed task {task.task_code if task else ''}.",
        )

        # 5. Finalize Settlement
        settlement.status = "completed"
        settlement.completed_at = now
        settlement.updated_at = now
        settlement.failure_reason = None

        _log_settlement_audit(
            db,
            settlement_id=settlement.id,
            action="settlement_completed",
            actor_type="system",
            actor_id="AgentPay-Settlement-Engine",
            amount=settlement.amount,
            previous_status="processing",
            new_status="completed",
            message=f"Settlement completed successfully. {settlement.amount} AP transferred to {wrk_wallet.wallet_code}.",
        )

        db.commit()
        db.refresh(settlement)

        # Phase 13: Recalculate worker reputation upon successful settlement
        try:
            reputation_service.on_settlement_completed(db, settlement.id)
            db.commit()
        except Exception as rep_err:
            print(f"Reputation recalculation note on settlement: {rep_err}")

        return settlement

    except Exception as e:
        db.rollback()
        # Record failure state
        settlement.status = "failed"
        settlement.failed_at = datetime.utcnow()
        settlement.failure_reason = str(e)
        settlement.updated_at = datetime.utcnow()
        try:
            _log_settlement_audit(
                db,
                settlement_id=settlement.id,
                action="settlement_failed",
                actor_type="system",
                actor_id="AgentPay-Settlement-Engine",
                amount=settlement.amount,
                previous_status="processing",
                new_status="failed",
                message=f"Settlement execution failed: {str(e)}",
            )
            db.commit()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Settlement transaction failed: {str(e)}",
        )


def auto_settle_releasable_escrow(db: Session, escrow_id: int) -> Optional[Settlement]:
    """
    Hook called immediately after verification passes to automatically trigger settlement.
    """
    try:
        settlement = create_settlement(db, escrow_id, trigger_type="automatic")
        settlement = execute_settlement(db, settlement.id)
        return settlement
    except Exception as e:
        # Non-blocking for the caller; error is recorded on the settlement record
        print(f"Auto-settlement note for escrow {escrow_id}: {e}")
        return None


def get_settlement(db: Session, settlement_id: int) -> Optional[Settlement]:
    """Retrieve settlement by primary ID."""
    return db.query(Settlement).filter(Settlement.id == settlement_id).first()


def get_settlement_by_code(db: Session, settlement_code: str) -> Optional[Settlement]:
    """Retrieve settlement by code."""
    return db.query(Settlement).filter(Settlement.settlement_code == settlement_code).first()


def get_task_settlement(db: Session, task_id: int) -> Optional[Settlement]:
    """Retrieve settlement linked to a task."""
    return (
        db.query(Settlement)
        .filter(Settlement.task_id == task_id)
        .order_by(Settlement.id.desc())
        .first()
    )


def get_escrow_settlement(db: Session, escrow_id: int) -> Optional[Settlement]:
    """Retrieve settlement linked to an escrow."""
    return (
        db.query(Settlement)
        .filter(Settlement.escrow_id == escrow_id)
        .order_by(Settlement.id.desc())
        .first()
    )


def list_settlements(
    db: Session,
    status_filter: Optional[str] = None,
    task_id: Optional[int] = None,
) -> List[Settlement]:
    """List all settlements with optional filtering."""
    query = db.query(Settlement)
    if status_filter and status_filter.lower() != "all":
        query = query.filter(Settlement.status == status_filter.lower())
    if task_id:
        query = query.filter(Settlement.task_id == task_id)
    return query.order_by(Settlement.id.desc()).all()


def get_settlement_audit_logs(db: Session, settlement_id: int) -> List[SettlementAuditLog]:
    """Retrieve chronological audit trail for a settlement."""
    return (
        db.query(SettlementAuditLog)
        .filter(SettlementAuditLog.settlement_id == settlement_id)
        .order_by(SettlementAuditLog.id.asc())
        .all()
    )


def get_settlement_ledger_entries(db: Session, settlement_id: int) -> List[LedgerEntry]:
    """Retrieve ledger entries associated with a settlement."""
    return (
        db.query(LedgerEntry)
        .filter(LedgerEntry.settlement_id == settlement_id)
        .order_by(LedgerEntry.id.asc())
        .all()
    )


def get_settlement_summary(db: Session) -> Dict[str, Any]:
    """Return aggregate statistics across all settlements and financial balances."""
    settlements = db.query(Settlement).all()
    escrows = db.query(Escrow).all()

    total_settlements = len(settlements)
    completed_settlements = sum(1 for s in settlements if s.status == "completed")
    blocked_settlements = sum(1 for s in settlements if s.status == "blocked")
    failed_settlements = sum(1 for s in settlements if s.status == "failed")
    pending_settlements = sum(1 for s in settlements if s.status == "pending")

    total_ap_settled = sum(s.amount for s in settlements if s.status == "completed")
    ap_currently_locked = sum(
        e.reward_amount for e in escrows if e.status in ("locked", "awaiting_verification", "releasable")
    )
    ap_awaiting_resolution = sum(
        e.reward_amount for e in escrows if e.status in ("blocked", "awaiting_review")
    )

    return {
        "total_settlements": total_settlements,
        "completed_settlements": completed_settlements,
        "blocked_settlements": blocked_settlements,
        "failed_settlements": failed_settlements,
        "pending_settlements": pending_settlements,
        "total_ap_settled": total_ap_settled,
        "ap_currently_locked": ap_currently_locked,
        "ap_awaiting_resolution": ap_awaiting_resolution,
    }


def retry_failed_settlement(db: Session, settlement_id: int) -> Settlement:
    """
    Retries a failed settlement after re-running all eligibility checks.
    """
    settlement = db.query(Settlement).filter(Settlement.id == settlement_id).first()
    if not settlement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Settlement with id {settlement_id} not found.",
        )

    if settlement.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only failed settlements can be retried. Current status is '{settlement.status}'.",
        )

    return execute_settlement(db, settlement_id)
