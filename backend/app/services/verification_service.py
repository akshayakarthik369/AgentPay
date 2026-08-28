"""
Phase 10 — Independent Verification Engine Service.

Orchestrates verification creation, verifier assignment, integrity checking,
deterministic multi-criterion scoring, explainable decision calculation,
state transitions, and audit logging.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.verification import Verification, VerificationAuditLog
from app.models.result_submission import ResultSubmission
from app.models.task import Task
from app.models.agent import Agent
from app.services.verifier_selection_service import select_verifier
from app.services import submission_service
from app.services import escrow_service
from app.verification import get_verifier_for_category, VerificationResult


def _log_verification_audit(
    db: Session,
    verification_id: int,
    action: str,
    actor_type: str = "system",
    actor_id: Optional[str] = "system",
    message: Optional[str] = None,
) -> VerificationAuditLog:
    """Record an immutable verification audit log event."""
    log_entry = VerificationAuditLog(
        verification_id=verification_id,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        message=message,
        created_at=datetime.utcnow(),
    )
    db.add(log_entry)
    db.flush()
    return log_entry


def build_verifier_snapshot(verifier: Agent) -> str:
    """Freeze verifier state at verification time into JSON string."""
    snap = {
        "verifier_id": verifier.id,
        "verifier_code": verifier.agent_code,
        "name": verifier.name,
        "agent_type": verifier.agent_type,
        "capabilities": verifier.capabilities or [],
        "reputation_score": verifier.reputation_score,
        "status_at_verification": verifier.status,
    }
    return json.dumps(snap, sort_keys=True)


def create_verification_for_submission(
    db: Session, submission_id: int
) -> Verification:
    """
    Initiates independent verification for a locked result submission.

    Guards:
      1. Submission must exist, be locked, and verification_ready.
      2. No duplicate finalized verification (returns 409 marker).
      3. Verifier must be strictly independent (verifier != worker).
      4. Verifier must exist and be active.
    """
    # 1. Load submission
    submission = (
        db.query(ResultSubmission)
        .filter(ResultSubmission.id == submission_id)
        .first()
    )
    if not submission:
        raise ValueError(f"Submission with ID {submission_id} not found.")

    if not submission.is_locked or not submission.verification_ready:
        raise ValueError(
            f"Submission {submission.submission_code or submission_id} is not locked or ready for verification."
        )

    # 2. Check for existing verification
    existing = (
        db.query(Verification)
        .filter(Verification.submission_id == submission_id)
        .first()
    )
    if existing:
        if existing.status in ("passed", "failed", "review_required"):
            raise ValueError(
                f"DUPLICATE_VERIFICATION:{existing.id}:{existing.verification_code}"
            )
        # If pending or running, return existing
        return existing

    # 3. Select independent verifier
    verifier = select_verifier(db, submission)
    if not verifier:
        raise ValueError(
            "NO_VERIFIER_AVAILABLE: No eligible independent verifier agent is active."
        )

    # 4. Freeze verifier snapshot
    verifier_snap = build_verifier_snapshot(verifier)

    # Parse required quality score from task snapshot or task record
    required_score = 85.0
    if submission.task_snapshot:
        try:
            ts = (
                json.loads(submission.task_snapshot)
                if isinstance(submission.task_snapshot, str)
                else submission.task_snapshot
            )
            required_score = float(ts.get("minimum_quality_score", 85.0))
        except Exception:
            pass

    # 5. Create Verification record
    verification = Verification(
        submission_id=submission.id,
        task_id=submission.task_id,
        worker_agent_id=submission.agent_id,
        verifier_agent_id=verifier.id,
        status="pending",
        required_score=required_score,
        verifier_snapshot=verifier_snap,
        submission_hash_snapshot=submission.integrity_hash,
        started_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(verification)
    db.flush()

    # 6. Mark verifier agent as busy
    verifier.status = "busy"
    verifier.updated_at = datetime.utcnow()

    # 7. Write audit log entries
    _log_verification_audit(
        db,
        verification.id,
        action="verification_created",
        actor_type="system",
        actor_id="system",
        message=f"Verification initiated for submission {submission.submission_code}.",
    )
    _log_verification_audit(
        db,
        verification.id,
        action="verifier_selected",
        actor_type="system",
        actor_id="system",
        message=f"Independent verifier {verifier.agent_code} ({verifier.name}) selected.",
    )

    db.commit()
    db.refresh(verification)
    return verification


def run_verification(db: Session, verification_id: int) -> Verification:
    """
    Executes the full evaluation pipeline for a verification:
      1. Check SHA-256 submission integrity.
      2. If invalid -> FAIL immediately.
      3. Evaluate 5 criteria using category verifier.
      4. Calculate weighted overall score and decision.
      5. Update Task and Agent statuses.
      6. Record audit trail.
    """
    verification = (
        db.query(Verification)
        .filter(Verification.id == verification_id)
        .first()
    )
    if not verification:
        raise ValueError(f"Verification with ID {verification_id} not found.")

    if verification.status in ("passed", "failed", "review_required"):
        # Already finalized
        return verification

    submission = (
        db.query(ResultSubmission)
        .filter(ResultSubmission.id == verification.submission_id)
        .first()
    )
    if not submission:
        raise ValueError(f"Submission for verification {verification_id} not found.")

    task = db.query(Task).filter(Task.id == verification.task_id).first()
    worker = db.query(Agent).filter(Agent.id == verification.worker_agent_id).first()
    verifier = db.query(Agent).filter(Agent.id == verification.verifier_agent_id).first()

    verification.status = "running"
    db.flush()

    _log_verification_audit(
        db,
        verification.id,
        action="scoring_started",
        actor_type="verifier_agent",
        actor_id=verifier.agent_code if verifier else "verifier",
        message="Independent evaluation pipeline started.",
    )

    # ── Step 1: Check SHA-256 Integrity ────────────────────────────────────────
    integrity_res = submission_service.verify_submission_integrity(submission)
    verification.integrity_valid = integrity_res.get("valid", False)

    _log_verification_audit(
        db,
        verification.id,
        action="integrity_checked",
        actor_type="verifier_agent",
        actor_id=verifier.agent_code if verifier else "verifier",
        message=(
            "Cryptographic SHA-256 integrity valid."
            if verification.integrity_valid
            else "Integrity validation FAILED: data modified after submission."
        ),
    )

    # If integrity failed -> FAIL immediately
    if not verification.integrity_valid:
        verification.status = "failed"
        verification.decision = "FAIL"
        verification.overall_score = 0.0
        verification.accuracy_score = 0.0
        verification.completeness_score = 0.0
        verification.quality_score = 0.0
        verification.format_compliance_score = 0.0
        verification.evidence_score = 0.0
        verification.reasons = json.dumps({
            "integrity": ["Submission integrity validation failed. Hash mismatch detected."]
        })
        verification.warnings = json.dumps([
            "Integrity check failed — data was altered after packaging."
        ])
        verification.completed_at = datetime.utcnow()

        if verifier:
            verifier.status = "available"
        if worker:
            worker.status = "available"
        if task:
            task.status = "failed"

        _log_verification_audit(
            db,
            verification.id,
            action="decision_calculated",
            actor_type="verifier_agent",
            actor_id=verifier.agent_code if verifier else "verifier",
            message="Decision: FAIL (Integrity check failure).",
        )
        _log_verification_audit(
            db,
            verification.id,
            action="verification_finalized",
            actor_type="system",
            actor_id="system",
            message="Verification finalized as FAILED.",
        )
        # Phase 11: Update escrow status from FAIL decision
        try:
            escrow_service.update_escrow_from_verification(db, verification.id, "FAIL")
        except Exception:
            pass  # Non-blocking; escrow may not exist for legacy tasks

        db.commit()
        db.refresh(verification)
        return verification

    # ── Step 2: Load Frozen Snapshots ─────────────────────────────────────────
    task_snap = (
        json.loads(submission.task_snapshot)
        if isinstance(submission.task_snapshot, str)
        else (submission.task_snapshot or {})
    )
    structured_out = (
        json.loads(submission.structured_output)
        if isinstance(submission.structured_output, str)
        else (submission.structured_output or {})
    )
    evidence = (
        json.loads(submission.evidence)
        if isinstance(submission.evidence, str)
        else (submission.evidence or {})
    )
    provenance = (
        json.loads(submission.provenance)
        if isinstance(submission.provenance, str)
        else (submission.provenance or {})
    )
    limitations = (
        json.loads(submission.limitations)
        if isinstance(submission.limitations, str)
        else (submission.limitations or [])
    )

    category = task_snap.get("category") or (task.category if task else "Generic")
    required_score = verification.required_score or float(task_snap.get("minimum_quality_score", 85.0))

    # ── Step 3: Run Category Verifier Strategy ────────────────────────────────
    strategy = get_verifier_for_category(category)
    result: VerificationResult = strategy.verify(
        output_text=submission.output_text or "",
        structured_output=structured_out,
        task_snapshot=task_snap,
        evidence=evidence,
        provenance=provenance,
        limitations=limitations,
        required_score=required_score,
    )

    # ── Step 4: Populate Verification Record ──────────────────────────────────
    verification.accuracy_score = result.accuracy_score
    verification.completeness_score = result.completeness_score
    verification.format_compliance_score = result.format_compliance_score
    verification.quality_score = result.quality_score
    verification.evidence_score = result.evidence_score
    verification.overall_score = result.overall_score
    verification.required_score = result.required_score
    verification.decision = result.decision
    verification.reasons = json.dumps(result.reasons)
    verification.warnings = json.dumps(result.warnings)
    verification.verification_details = json.dumps(result.details)
    verification.completed_at = datetime.utcnow()

    # ── Step 5: State Transitions ─────────────────────────────────────────────
    if result.decision == "PASS":
        verification.status = "passed"
        if task:
            task.status = "verified"
        if worker:
            worker.status = "available"
        if verifier:
            verifier.status = "available"

    elif result.decision == "FAIL":
        verification.status = "failed"
        if task:
            task.status = "failed"
        if worker:
            worker.status = "available"
        if verifier:
            verifier.status = "available"

    else:  # REVIEW
        verification.status = "review_required"
        if task:
            task.status = "verifying"  # Remains in verifying state for Human Review
        if worker:
            worker.status = "busy"     # Worker stays busy during review
        if verifier:
            verifier.status = "available"

    # ── Step 6: Audit Trail ───────────────────────────────────────────────────
    _log_verification_audit(
        db,
        verification.id,
        action="criterion_scored",
        actor_type="verifier_agent",
        actor_id=verifier.agent_code if verifier else "verifier",
        message=(
            f"Scores: Acc={result.accuracy_score}, Comp={result.completeness_score}, "
            f"Qual={result.quality_score}, Fmt={result.format_compliance_score}, "
            f"Ev={result.evidence_score}."
        ),
    )
    _log_verification_audit(
        db,
        verification.id,
        action="decision_calculated",
        actor_type="verifier_agent",
        actor_id=verifier.agent_code if verifier else "verifier",
        message=f"Overall Score: {result.overall_score}% vs Required: {required_score}% -> Decision: {result.decision}.",
    )
    _log_verification_audit(
        db,
        verification.id,
        action="verification_finalized",
        actor_type="system",
        actor_id="system",
        message=f"Verification finalized with status '{verification.status}'.",
    )

    # Phase 11: Update linked Escrow status based on verification decision
    try:
        escrow_service.update_escrow_from_verification(db, verification.id, result.decision)
    except Exception:
        pass  # Non-blocking; escrow may not exist for legacy tasks

    db.commit()
    db.refresh(verification)
    return verification


def get_verification_by_id(db: Session, verification_id: int) -> Optional[Verification]:
    """Fetch verification by primary key ID."""
    return db.query(Verification).filter(Verification.id == verification_id).first()


def get_verification_by_code(db: Session, code: str) -> Optional[Verification]:
    """Fetch verification by human-readable VR code."""
    return db.query(Verification).filter(Verification.verification_code == code).first()


def get_task_verification(db: Session, task_id: int) -> Optional[Verification]:
    """Fetch the latest verification for a task."""
    return (
        db.query(Verification)
        .filter(Verification.task_id == task_id)
        .order_by(Verification.created_at.desc())
        .first()
    )


def get_submission_verification(db: Session, submission_id: int) -> Optional[Verification]:
    """Fetch verification for a result submission."""
    return (
        db.query(Verification)
        .filter(Verification.submission_id == submission_id)
        .first()
    )


def get_verification_audit_logs(
    db: Session, verification_id: int
) -> List[VerificationAuditLog]:
    """Fetch ordered chronological audit logs for a verification."""
    return (
        db.query(VerificationAuditLog)
        .filter(VerificationAuditLog.verification_id == verification_id)
        .order_by(VerificationAuditLog.created_at.asc())
        .all()
    )


def list_verifications(
    db: Session, limit: int = 50, offset: int = 0
) -> List[Verification]:
    """List completed/historical verification records."""
    return (
        db.query(Verification)
        .order_by(Verification.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
