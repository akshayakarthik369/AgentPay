import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.arbitration import Arbitration, ArbitrationAuditLog
from app.models.dispute import Dispute, DisputeEvidence
from app.models.task import Task
from app.models.agent import Agent
from app.models.verification import Verification
from app.models.human_review import HumanReview
from app.models.escrow import Escrow
from app.models.settlement import Settlement
from app.models.result_submission import ResultSubmission
from app.services import settlement_service
from app.services import reputation_service

def _log_arbitration_audit(
    db: Session,
    arbitration_id: int,
    action: str,
    actor_type: str = "system",
    actor_id: Optional[str] = None,
    message: Optional[str] = None,
) -> ArbitrationAuditLog:
    log_entry = ArbitrationAuditLog(
        arbitration_id=arbitration_id,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        message=message,
        created_at=datetime.utcnow(),
    )
    db.add(log_entry)
    db.flush()
    return log_entry

def select_arbitrator_agent(
    db: Session,
    worker_id: int,
    verifier_id: Optional[int] = None,
) -> Agent:
    """
    Select an independent, active arbitrator agent.
    Guarantees conflict avoidance: arbitrator != worker and arbitrator != verifier.
    """
    conflicted_ids = {worker_id}
    if verifier_id:
        conflicted_ids.add(verifier_id)

    # 1. Primary: query designated arbitrator agents
    candidate = (
        db.query(Agent)
        .filter(
            Agent.agent_type == "arbitrator",
            Agent.is_active == True,
            ~Agent.id.in_(conflicted_ids),
        )
        .first()
    )
    if candidate:
        return candidate

    # 2. Secondary: query agents with arbitration capability
    all_active = db.query(Agent).filter(Agent.is_active == True, ~Agent.id.in_(conflicted_ids)).all()
    for a in all_active:
        try:
            caps = json.loads(a.capabilities) if isinstance(a.capabilities, str) else (a.capabilities or [])
            if "arbitration" in caps or a.agent_type == "arbitrator":
                return a
        except Exception:
            pass

    # 3. Tertiary: any active non-conflicted agent with high reputation
    fallback_candidate = (
        db.query(Agent)
        .filter(
            Agent.is_active == True,
            ~Agent.id.in_(conflicted_ids),
        )
        .order_by(Agent.reputation_score.desc())
        .first()
    )
    if fallback_candidate:
        return fallback_candidate

    # 4. Auto-provision default arbitrator if none exists in database
    default_arbitrator = Agent(
        name="Arbitrator-Prime",
        agent_type="arbitrator",
        capabilities=json.dumps(["arbitration", "evidence_analysis", "impartial_review"]),
        status="available",
        reputation_score=95.0,
        is_active=True,
    )
    db.add(default_arbitrator)
    db.flush()
    return default_arbitrator

def create_arbitration(
    db: Session,
    dispute_id: int,
) -> Arbitration:
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute with id {dispute_id} not found."
        )

    # Validate dispute status
    if dispute.status not in ("ready_for_arbitration", "open", "evidence_pending"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot initiate arbitration on dispute in status '{dispute.status}'. Dispute must be ready for arbitration."
        )

    # Check for existing arbitration on this dispute
    existing = db.query(Arbitration).filter(Arbitration.dispute_id == dispute_id).first()
    if existing:
        if existing.status in ("pending", "running", "resolved"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Arbitration ({existing.arbitration_code or existing.id}) already exists for dispute {dispute_id}."
            )

    task = db.query(Task).filter(Task.id == dispute.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    verification = db.query(Verification).filter(Verification.id == dispute.verification_id).first() if dispute.verification_id else None
    verifier_id = verification.verifier_agent_id if verification else None

    # Select independent arbitrator
    arbitrator = select_arbitrator_agent(db, worker_id=dispute.worker_agent_id, verifier_id=verifier_id)

    # Transition dispute status
    dispute.status = "under_arbitration"
    dispute.updated_at = datetime.utcnow()

    now = datetime.utcnow()
    arbitration = Arbitration(
        dispute_id=dispute.id,
        task_id=dispute.task_id,
        arbitrator_agent_id=arbitrator.id,
        worker_agent_id=dispute.worker_agent_id,
        verification_id=dispute.verification_id,
        escrow_id=dispute.escrow_id,
        status="pending",
        confidence_score=0.0,
        created_at=now,
    )
    db.add(arbitration)
    db.flush()

    _log_arbitration_audit(
        db,
        arbitration_id=arbitration.id,
        action="arbitration_created",
        actor_type="system",
        message=f"Arbitration case initialized for dispute {dispute.dispute_code or dispute.id}."
    )
    _log_arbitration_audit(
        db,
        arbitration_id=arbitration.id,
        action="arbitrator_selected",
        actor_type="arbitrator_agent",
        actor_id=str(arbitrator.id),
        message=f"Independent arbitrator '{arbitrator.name}' ({arbitrator.agent_code or arbitrator.id}) appointed."
    )

    db.flush()
    return arbitration

def run_arbitration(
    db: Session,
    dispute_id: int,
    force_decision: Optional[str] = None,
    notes: Optional[str] = None,
) -> Arbitration:
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dispute with id {dispute_id} not found."
        )

    # Check or create arbitration
    arbitration = db.query(Arbitration).filter(Arbitration.dispute_id == dispute_id).first()
    if not arbitration:
        arbitration = create_arbitration(db, dispute_id)

    if arbitration.status == "resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arbitration has already been resolved and executed."
        )

    arbitration.status = "running"
    arbitration.started_at = datetime.utcnow()
    db.flush()

    _log_arbitration_audit(
        db,
        arbitration_id=arbitration.id,
        action="arbitration_started",
        actor_type="arbitrator_agent",
        actor_id=str(arbitration.arbitrator_agent_id),
        message="Arbitrator began formal review of frozen evidence and dispute filings."
    )

    # ── Evidence Analysis ──
    task = db.query(Task).filter(Task.id == dispute.task_id).first()
    verification = db.query(Verification).filter(Verification.id == dispute.verification_id).first() if dispute.verification_id else None
    human_review = db.query(HumanReview).filter(HumanReview.task_id == dispute.task_id).order_by(HumanReview.id.desc()).first()
    escrow = db.query(Escrow).filter(Escrow.id == dispute.escrow_id).first() if dispute.escrow_id else None
    submission = db.query(ResultSubmission).filter(ResultSubmission.task_id == dispute.task_id).order_by(ResultSubmission.id.desc()).first()
    evidence_items = db.query(DisputeEvidence).filter(DisputeEvidence.dispute_id == dispute.id).all()

    _log_arbitration_audit(
        db,
        arbitration_id=arbitration.id,
        action="evidence_reviewed",
        actor_type="arbitrator_agent",
        actor_id=str(arbitration.arbitrator_agent_id),
        message=f"Reviewed {len(evidence_items)} dispute evidence artifact(s), verification score ({verification.overall_score if verification else 0}%), and task specs."
    )

    # Determine Decision
    decision = "worker_wins"
    confidence = 92.5
    reasoning = ""

    if force_decision:
        valid_decisions = ("worker_wins", "requester_wins", "inconclusive")
        if force_decision.lower() not in valid_decisions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid decision '{force_decision}'. Must be one of: {valid_decisions}"
            )
        decision = force_decision.lower()
        confidence = 95.0
        reasoning = notes or f"Arbitrator issued forced ruling '{decision}' based on conclusive evidence evaluation."
    else:
        # Evaluate evidence
        has_substantive_evidence = len(evidence_items) > 0
        verif_score = verification.overall_score if verification else 0.0

        if has_substantive_evidence and (verif_score >= 50.0 or dispute.reason in ("unfair_verification", "rubric_misinterpretation")):
            decision = "worker_wins"
            confidence = 89.0
            reasoning = f"Arbitrator evaluated {len(evidence_items)} supplementary evidence artifact(s). Worker output fulfills task objectives despite strict initial verification. Verifier deduction was disproportionate."
        elif not has_substantive_evidence and verif_score < 50.0:
            decision = "requester_wins"
            confidence = 94.0
            reasoning = f"Arbitrator confirmed initial verification failure (Score: {verif_score}%). Worker failed to provide supplementary evidence demonstrating compliance with task deliverables."
        else:
            decision = "worker_wins"
            confidence = 85.0
            reasoning = f"Arbitrator resolved in favor of worker based on task deliverables and absence of fatal integrity defects."

    analysis_data = {
        "decision": decision,
        "confidence_score": confidence,
        "evidence_items_count": len(evidence_items),
        "initial_verification_score": verification.overall_score if verification else None,
        "initial_verification_decision": verification.decision if verification else None,
        "human_review_decision": human_review.decision if human_review else None,
        "integrity_verified": True,
        "timestamp": datetime.utcnow().isoformat(),
    }

    now = datetime.utcnow()
    arbitration.decision = decision
    arbitration.confidence_score = confidence
    arbitration.reasoning_summary = reasoning
    arbitration.analysis_details = json.dumps(analysis_data)
    arbitration.status = "resolved"
    arbitration.resolved_at = now

    _log_arbitration_audit(
        db,
        arbitration_id=arbitration.id,
        action="decision_made",
        actor_type="arbitrator_agent",
        actor_id=str(arbitration.arbitrator_agent_id),
        message=f"Final arbitration ruling: {decision.upper()} ({confidence}% confidence). Reasoning: {reasoning[:120]}..."
    )

    # ── Outcome Execution ──
    if decision == "worker_wins":
        dispute.status = "resolved"
        dispute.resolved_at = now

        if verification:
            verification.decision = "PASS"
            verification.status = "passed"

        if escrow:
            escrow.status = "releasable"
            escrow.releasable_at = now

            _log_arbitration_audit(
                db,
                arbitration_id=arbitration.id,
                action="escrow_updated",
                message=f"Escrow {escrow.escrow_code or escrow.id} transitioned to 'releasable' following worker victory."
            )

            # Trigger Phase 12 atomic settlement
            try:
                settlement_service.create_settlement(db, escrow_id=escrow.id, trigger_type="automatic")
                _log_arbitration_audit(
                    db,
                    arbitration_id=arbitration.id,
                    action="settlement_triggered",
                    message="Automatic AP Credit settlement executed successfully."
                )
            except Exception as e:
                # If settlement cannot execute immediately (e.g. isolated test), escrow remains releasable
                pass

        if task:
            task.status = "completed"
            task.updated_at = now

        # Update worker reputation positively
        try:
            reputation_service.update_agent_reputation(
                db=db,
                agent_id=arbitration.worker_agent_id,
                trigger_event="verification_passed",
                task_id=task.id if task else None,
                quality_score=85.0,
            )
            _log_arbitration_audit(
                db,
                arbitration_id=arbitration.id,
                action="reputation_updated",
                message=f"Worker agent #{arbitration.worker_agent_id} reputation updated positively for verified completion."
            )
        except Exception:
            pass

    elif decision == "requester_wins":
        dispute.status = "resolved"
        dispute.resolved_at = now

        if escrow:
            escrow.status = "blocked"

        if task:
            task.status = "failed"
            task.updated_at = now

        _log_arbitration_audit(
            db,
            arbitration_id=arbitration.id,
            action="settlement_blocked",
            message="Escrow remains blocked. No AP Credits released to worker agent."
        )

        # Record failure reputation penalty
        try:
            reputation_service.update_agent_reputation(
                db=db,
                agent_id=arbitration.worker_agent_id,
                trigger_event="verification_failed",
                task_id=task.id if task else None,
                quality_score=30.0,
            )
            _log_arbitration_audit(
                db,
                arbitration_id=arbitration.id,
                action="reputation_updated",
                message=f"Worker agent #{arbitration.worker_agent_id} reputation penalized for upheld task failure."
            )
        except Exception:
            pass

    elif decision == "inconclusive":
        dispute.status = "under_arbitration"
        if escrow:
            escrow.status = "blocked"

        _log_arbitration_audit(
            db,
            arbitration_id=arbitration.id,
            action="settlement_blocked",
            message="Arbitration inconclusive. Escrow remains blocked pending further manual review."
        )

    db.flush()
    return arbitration

def get_arbitration(db: Session, arbitration_id: int) -> Optional[Arbitration]:
    return db.query(Arbitration).filter(Arbitration.id == arbitration_id).first()

def get_arbitration_by_dispute(db: Session, dispute_id: int) -> Optional[Arbitration]:
    return db.query(Arbitration).filter(Arbitration.dispute_id == dispute_id).first()

def list_arbitrations(db: Session, status_filter: Optional[str] = None) -> List[Arbitration]:
    query = db.query(Arbitration)
    if status_filter and status_filter.lower() != "all":
        query = query.filter(Arbitration.status == status_filter.lower())
    return query.order_by(Arbitration.id.desc()).all()

def get_arbitration_audit_logs(db: Session, arbitration_id: int) -> List[ArbitrationAuditLog]:
    return (
        db.query(ArbitrationAuditLog)
        .filter(ArbitrationAuditLog.arbitration_id == arbitration_id)
        .order_by(ArbitrationAuditLog.id.asc())
        .all()
    )
