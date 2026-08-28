import json
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.dispute import Dispute, DisputeEvidence, DisputeAuditLog
from app.models.task import Task
from app.models.agent import Agent
from app.models.verification import Verification
from app.models.human_review import HumanReview
from app.models.escrow import Escrow
from app.models.settlement import Settlement
from app.models.result_submission import ResultSubmission

ACTIVE_DISPUTE_STATUSES = ["open", "evidence_pending", "ready_for_arbitration", "under_arbitration"]
FINAL_DISPUTE_STATUSES = ["resolved", "rejected", "cancelled"]

def _log_dispute_audit(
    db: Session,
    dispute_id: int,
    action: str,
    actor_type: str = "system",
    actor_id: Optional[str] = None,
    message: Optional[str] = None,
) -> DisputeAuditLog:
    log_entry = DisputeAuditLog(
        dispute_id=dispute_id,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        message=message,
        created_at=datetime.utcnow(),
    )
    db.add(log_entry)
    db.flush()
    return log_entry

def create_dispute(
    db: Session,
    task_id: int,
    reason: str,
    description: str,
    raised_by_type: str = "worker",
    raised_by_id: Optional[str] = None,
    initial_evidence_title: Optional[str] = None,
    initial_evidence_description: Optional[str] = None,
    initial_evidence_data: Optional[str] = None,
) -> Dispute:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found."
        )

    # Check for active dispute duplicate
    existing_active = (
        db.query(Dispute)
        .filter(Dispute.task_id == task_id, Dispute.status.in_(ACTIVE_DISPUTE_STATUSES))
        .first()
    )
    if existing_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An active dispute ({existing_active.dispute_code or existing_active.id}) already exists for task {task_id}."
        )

    # Fetch associated records
    submission = (
        db.query(ResultSubmission)
        .filter(ResultSubmission.task_id == task_id)
        .order_by(ResultSubmission.id.desc())
        .first()
    )
    verification = (
        db.query(Verification)
        .filter(Verification.task_id == task_id)
        .order_by(Verification.id.desc())
        .first()
    )
    human_review = (
        db.query(HumanReview)
        .filter(HumanReview.task_id == task_id)
        .order_by(HumanReview.id.desc())
        .first()
    )
    escrow = (
        db.query(Escrow)
        .filter(Escrow.task_id == task_id)
        .order_by(Escrow.id.desc())
        .first()
    )
    completed_settlement = (
        db.query(Settlement)
        .filter(Settlement.task_id == task_id, Settlement.status == "completed")
        .first()
    )

    # Rule: Completed successful settlements cannot be disputed through this flow
    if completed_settlement:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot dispute task {task_id}: settlement {completed_settlement.settlement_code} is already completed."
        )

    # Rule: Verification PASS with released escrow cannot be disputed
    if verification and verification.decision == "PASS" and escrow and escrow.status == "released":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot dispute task: verification passed and escrow was successfully released."
        )

    # Rule: Allow dispute for verification FAIL, human review REJECT, or blocked escrow
    is_verif_fail = verification and verification.decision == "FAIL"
    is_review_reject = human_review and human_review.decision == "REJECT"
    is_escrow_blocked = escrow and escrow.status == "blocked"
    is_task_failed = task.status == "failed"

    if not (is_verif_fail or is_review_reject or is_escrow_blocked or is_task_failed):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Disputes are only permitted for failed verification, rejected human review, or blocked escrow outcomes."
        )

    # Require minimum entities
    sub_id = submission.id if submission else (verification.submission_id if verification else 0)
    verif_id = verification.id if verification else (human_review.verification_id if human_review else 0)
    escrow_id = escrow.id if escrow else 0
    worker_id = task.assigned_agent_id or (submission.agent_id if submission else (verification.worker_agent_id if verification else 0))

    if not worker_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create dispute: no assigned worker agent found for task."
        )

    now = datetime.utcnow()
    dispute = Dispute(
        task_id=task.id,
        submission_id=sub_id,
        verification_id=verif_id,
        escrow_id=escrow_id,
        worker_agent_id=worker_id,
        raised_by_type=raised_by_type,
        raised_by_id=raised_by_id,
        reason=reason,
        description=description,
        status="open",
        created_at=now,
        updated_at=now,
    )
    db.add(dispute)
    db.flush()

    # Transition task to disputed
    task.status = "disputed"
    task.updated_at = now

    # Ensure escrow remains blocked (never released)
    if escrow and escrow.status != "blocked":
        escrow.status = "blocked"
        escrow.updated_at = now

    _log_dispute_audit(
        db,
        dispute_id=dispute.id,
        action="dispute_created",
        actor_type=raised_by_type,
        actor_id=raised_by_id or str(worker_id),
        message=f"Dispute opened for reason '{reason}'. Task marked as disputed. Escrow remains blocked."
    )

    # Optional initial evidence
    if initial_evidence_title and initial_evidence_description:
        evidence = DisputeEvidence(
            dispute_id=dispute.id,
            submitted_by_type=raised_by_type,
            submitted_by_id=raised_by_id,
            title=initial_evidence_title,
            description=initial_evidence_description,
            evidence_data=initial_evidence_data,
            created_at=now,
        )
        db.add(evidence)
        db.flush()
        _log_dispute_audit(
            db,
            dispute_id=dispute.id,
            action="evidence_added",
            actor_type=raised_by_type,
            actor_id=raised_by_id,
            message=f"Initial evidence added: '{initial_evidence_title}'"
        )

    db.flush()
    return dispute

def get_dispute(db: Session, dispute_id: int) -> Optional[Dispute]:
    return db.query(Dispute).filter(Dispute.id == dispute_id).first()

def get_dispute_by_task(db: Session, task_id: int) -> Optional[Dispute]:
    return db.query(Dispute).filter(Dispute.task_id == task_id).order_by(Dispute.id.desc()).first()

def list_disputes(db: Session, status_filter: Optional[str] = None, task_id: Optional[int] = None) -> List[Dispute]:
    query = db.query(Dispute)
    if status_filter and status_filter.lower() != "all":
        query = query.filter(Dispute.status == status_filter.lower())
    if task_id:
        query = query.filter(Dispute.task_id == task_id)
    return query.order_by(Dispute.id.desc()).all()

def add_evidence(
    db: Session,
    dispute_id: int,
    title: str,
    description: str,
    evidence_data: Optional[str] = None,
    submitted_by_type: str = "worker",
    submitted_by_id: Optional[str] = None,
) -> DisputeEvidence:
    dispute = get_dispute(db, dispute_id)
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute with id {dispute_id} not found."
        )

    if dispute.status in FINAL_DISPUTE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add evidence to dispute in status '{dispute.status}'."
        )

    if not title or not title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Evidence title is required."
        )
    if not description or not description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Evidence description is required."
        )

    now = datetime.utcnow()
    evidence = DisputeEvidence(
        dispute_id=dispute.id,
        submitted_by_type=submitted_by_type,
        submitted_by_id=submitted_by_id,
        title=title.strip(),
        description=description.strip(),
        evidence_data=evidence_data,
        created_at=now,
    )
    db.add(evidence)

    # If status was evidence_pending, keep or update
    dispute.updated_at = now

    _log_dispute_audit(
        db,
        dispute_id=dispute.id,
        action="evidence_added",
        actor_type=submitted_by_type,
        actor_id=submitted_by_id,
        message=f"Evidence added: '{title.strip()}'"
    )

    db.flush()
    return evidence

def mark_ready_for_arbitration(db: Session, dispute_id: int) -> Dispute:
    dispute = get_dispute(db, dispute_id)
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute with id {dispute_id} not found."
        )

    if dispute.status not in ("open", "evidence_pending"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot mark dispute ready for arbitration from current status '{dispute.status}'."
        )

    now = datetime.utcnow()
    dispute.status = "ready_for_arbitration"
    dispute.updated_at = now

    _log_dispute_audit(
        db,
        dispute_id=dispute.id,
        action="ready_for_arbitration",
        actor_type="system",
        message="Dispute and evidence package marked ready for Phase 16 arbitration."
    )
    db.flush()
    return dispute

def cancel_dispute(db: Session, dispute_id: int, cancelled_by_type: str = "worker", cancelled_by_id: Optional[str] = None) -> Dispute:
    dispute = get_dispute(db, dispute_id)
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute with id {dispute_id} not found."
        )

    if dispute.status in FINAL_DISPUTE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Dispute has already concluded (status '{dispute.status}') and cannot be cancelled."
        )

    now = datetime.utcnow()
    dispute.status = "cancelled"
    dispute.cancelled_at = now
    dispute.updated_at = now

    # Revert task status if it was disputed
    task = db.query(Task).filter(Task.id == dispute.task_id).first()
    if task and task.status == "disputed":
        task.status = "failed"
        task.updated_at = now

    _log_dispute_audit(
        db,
        dispute_id=dispute.id,
        action="dispute_cancelled",
        actor_type=cancelled_by_type,
        actor_id=cancelled_by_id,
        message="Dispute was cancelled by submitter. Task reverted to failed."
    )
    db.flush()
    return dispute

def get_dispute_evidence_list(db: Session, dispute_id: int) -> List[DisputeEvidence]:
    return (
        db.query(DisputeEvidence)
        .filter(DisputeEvidence.dispute_id == dispute_id)
        .order_by(DisputeEvidence.id.asc())
        .all()
    )

def get_dispute_audit_logs(db: Session, dispute_id: int) -> List[DisputeAuditLog]:
    return (
        db.query(DisputeAuditLog)
        .filter(DisputeAuditLog.dispute_id == dispute_id)
        .order_by(DisputeAuditLog.id.asc())
        .all()
    )
