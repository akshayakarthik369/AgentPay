import json
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.human_review import HumanReview, HumanReviewAuditLog
from app.models.verification import Verification
from app.models.task import Task
from app.models.agent import Agent
from app.models.escrow import Escrow
from app.models.result_submission import ResultSubmission
from app.services import submission_service, settlement_service, escrow_service, reputation_service

def _log_human_review_audit(
    db: Session,
    review_id: int,
    action: str,
    actor_type: str = "system",
    actor_id: Optional[str] = None,
    message: Optional[str] = None,
) -> HumanReviewAuditLog:
    log_entry = HumanReviewAuditLog(
        review_id=review_id,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        message=message,
        created_at=datetime.utcnow(),
    )
    db.add(log_entry)
    db.flush()
    return log_entry

def create_human_review(
    db: Session,
    task_id: int,
    submission_id: int,
    verification_id: int,
    worker_agent_id: int,
) -> HumanReview:
    # Validation: Prevent review for PASS/FAIL
    verif = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification with id {verification_id} not found."
        )
    if verif.decision in ("PASS", "FAIL"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot initiate human review: verification decision is {verif.decision}."
        )

    # Validation: Prevent duplicate reviews
    existing = db.query(HumanReview).filter(
        HumanReview.verification_id == verification_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Human review for verification {verification_id} already exists."
        )

    now = datetime.utcnow()
    review = HumanReview(
        task_id=task_id,
        submission_id=submission_id,
        verification_id=verification_id,
        worker_agent_id=worker_agent_id,
        status="pending",
        created_at=now,
        updated_at=now,
    )
    db.add(review)
    db.flush()

    _log_human_review_audit(
        db,
        review_id=review.id,
        action="review_created",
        message=f"Borderline verification outcome VR-{1000 + verification_id} triggered HITL review."
    )
    return review

def get_human_review(db: Session, review_id: int) -> Optional[HumanReview]:
    return db.query(HumanReview).filter(HumanReview.id == review_id).first()

def get_human_review_by_task(db: Session, task_id: int) -> Optional[HumanReview]:
    return db.query(HumanReview).filter(HumanReview.task_id == task_id).order_by(HumanReview.id.desc()).first()

def list_human_reviews(db: Session, status_filter: Optional[str] = None) -> List[HumanReview]:
    query = db.query(HumanReview)
    if status_filter and status_filter.lower() != "all":
        query = query.filter(HumanReview.status == status_filter.lower())
    return query.order_by(HumanReview.id.desc()).all()

def start_human_review(db: Session, review_id: int) -> HumanReview:
    review = get_human_review(db, review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Human review with id {review_id} not found."
        )
    
    # Validation: Prevent invalid state transitions
    if review.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start human review: current status is {review.status}."
        )

    review.status = "in_review"
    review.started_at = datetime.utcnow()
    review.updated_at = datetime.utcnow()
    
    _log_human_review_audit(
        db,
        review_id=review.id,
        action="review_started",
        message="Review lock obtained by human arbitrator."
    )
    db.flush()
    return review

def resolve_human_review(
    db: Session,
    review_id: int,
    decision: str,
    reviewer_note: str,
) -> HumanReview:
    review = get_human_review(db, review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Human review with id {review_id} not found."
        )

    # Validation: Prevent resolving twice
    if review.status in ("resolved", "approved", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Human review has already been resolved."
        )

    # Validation: Enforce proper state transition
    if review.status != "in_review":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Human review must be in progress (status 'in_review') to resolve."
        )

    decision_upper = decision.upper()
    if decision_upper not in ("APPROVE", "REJECT"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resolution decision must be either 'APPROVE' or 'REJECT'."
        )

    if not reviewer_note or not reviewer_note.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resolution requires a reviewer note."
        )

    # Load associated entities
    verif = db.query(Verification).filter(Verification.id == review.verification_id).with_for_update().first()
    task = db.query(Task).filter(Task.id == review.task_id).with_for_update().first()
    worker = db.query(Agent).filter(Agent.id == review.worker_agent_id).with_for_update().first()
    escrow = db.query(Escrow).filter(Escrow.task_id == review.task_id).with_for_update().first()
    submission = db.query(ResultSubmission).filter(ResultSubmission.id == review.submission_id).first()

    # Validation: Prevent approval with invalid submission integrity
    if decision_upper == "APPROVE" and submission:
        integrity_res = submission_service.verify_submission_integrity(submission)
        if not integrity_res.get("valid", False):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot approve: submission integrity validation failed."
            )

    now = datetime.utcnow()

    # Use a savepoint to rollback cleanly on nested exception
    try:
        with db.begin_nested():
            if decision_upper == "APPROVE":
                # Treat as PASS-equivalent
                verif.decision = "PASS"
                verif.status = "passed"
                verif.completed_at = now
                verif.updated_at = now

                # Mark escrow releasable
                if escrow:
                    escrow_service.update_escrow_from_verification(db, verif.id, "PASS")
                
                # Reuse Phase 12 automatic settlement
                if escrow:
                    settlement = settlement_service.auto_settle_releasable_escrow(db, escrow.id)
                    if not settlement or settlement.status != "completed":
                        raise Exception("Automated escrow settlement failed during approval.")

                # Resolve review
                review.status = "approved"
                review.decision = "APPROVE"
                review.reviewer_note = reviewer_note
                review.resolved_at = now
                review.updated_at = now

                _log_human_review_audit(
                    db,
                    review_id=review.id,
                    action="review_approved",
                    actor_type="human_reviewer",
                    message=f"Arbitrator approved submission. Notes: {reviewer_note}"
                )
                _log_human_review_audit(
                    db,
                    review_id=review.id,
                    action="settlement_triggered",
                    message="Escrow release and settlement successfully processed."
                )
                _log_human_review_audit(
                    db,
                    review_id=review.id,
                    action="reputation_update_triggered",
                    message="Reputation recalculation triggered for positive outcome."
                )

            else:  # REJECT
                # Treat as FAIL-equivalent
                verif.decision = "FAIL"
                verif.status = "failed"
                verif.completed_at = now
                verif.updated_at = now

                if task:
                    task.status = "failed"
                    task.updated_at = now
                if worker:
                    worker.status = "available"
                    worker.updated_at = now

                # Escrow remains blocked (already blocked in verif REVIEW stage)

                # Resolve review
                review.status = "rejected"
                review.decision = "REJECT"
                review.reviewer_note = reviewer_note
                review.resolved_at = now
                review.updated_at = now

                _log_human_review_audit(
                    db,
                    review_id=review.id,
                    action="review_rejected",
                    actor_type="human_reviewer",
                    message=f"Arbitrator rejected submission. Notes: {reviewer_note}"
                )
                _log_human_review_audit(
                    db,
                    review_id=review.id,
                    action="reputation_update_triggered",
                    message="Reputation recalculation triggered for failure outcome."
                )

                # Trigger reputation update for FAIL
                try:
                    reputation_service.on_verification_finalized(db, verif.id)
                except Exception as rep_err:
                    print(f"Reputation trigger note: {rep_err}")

        db.flush()
        return review

    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve review due to internal transaction error: {str(e)}"
        )

def get_human_review_audit_logs(db: Session, review_id: int) -> List[HumanReviewAuditLog]:
    return (
        db.query(HumanReviewAuditLog)
        .filter(HumanReviewAuditLog.review_id == review_id)
        .order_by(HumanReviewAuditLog.id.asc())
        .all()
    )
