"""
Reputation & Trust Engine Service for AgentPay (Phase 13).

Calculates deterministic, observable performance-based reputation scores (0-100),
tracks immutable reputation audit events, and powers agent matching/bidding trust factors.
"""
import math
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from fastapi import HTTPException, status

from app.models.agent import Agent
from app.models.task import Task
from app.models.verification import Verification
from app.models.settlement import Settlement
from app.models.result_submission import ResultSubmission
from app.models.reputation import ReputationEvent

# 5-Factor Formula Component Weights (Sum = 1.0)
QUALITY_WEIGHT = 0.35
SUCCESS_RATE_WEIGHT = 0.30
RELIABILITY_WEIGHT = 0.20
CONSISTENCY_WEIGHT = 0.10
EXPERIENCE_WEIGHT = 0.05

PROVISIONAL_THRESHOLD = 3  # Minimum finalized verified tasks required for Established status
DEFAULT_COLD_START_SCORE = 80.0


def calculate_experience_score(completed_tasks_count: int) -> float:
    """
    Tiered experience score rewarding volume of successfully verified tasks.
    0 tasks: 50 | 1-2: 60 | 3-5: 70 | 6-10: 80 | 11-20: 90 | 21+: 100
    """
    if completed_tasks_count <= 0:
        return 50.0
    elif completed_tasks_count <= 2:
        return 60.0
    elif completed_tasks_count <= 5:
        return 70.0
    elif completed_tasks_count <= 10:
        return 80.0
    elif completed_tasks_count <= 20:
        return 90.0
    else:
        return 100.0


def calculate_consistency_score(verification_scores: List[float]) -> float:
    """
    Measures performance stability derived from standard deviation of recent verified scores.
    Consistency = max(0, min(100, 100 - std_dev * 2.0)).
    Default: 80.0 if fewer than 2 scores.
    """
    if not verification_scores or len(verification_scores) < 2:
        return DEFAULT_COLD_START_SCORE

    # Take up to last 10 scores
    recent_scores = verification_scores[-10:]
    n = len(recent_scores)
    mean = sum(recent_scores) / n
    variance = sum((x - mean) ** 2 for x in recent_scores) / n
    std_dev = math.sqrt(variance)

    score = 100.0 - (std_dev * 2.0)
    return max(0.0, min(100.0, round(score, 1)))


def determine_reputation_level(score: float, is_provisional: bool) -> str:
    """
    Map numerical reputation score to human-interpretable tier.
    """
    if is_provisional:
        return "Provisional"
    if score >= 90.0:
        return "Excellent"
    elif score >= 80.0:
        return "Strong"
    elif score >= 70.0:
        return "Good"
    elif score >= 60.0:
        return "Moderate"
    elif score >= 40.0:
        return "Weak"
    else:
        return "High Risk"


def compute_reputation_breakdown(
    verification_scores: List[float],
    successful_count: int,
    failed_count: int,
    integrity_fail_count: int = 0,
) -> Dict[str, Any]:
    """
    Pure mathematical calculation of 5-factor reputation breakdown.
    """
    total_finalized = successful_count + failed_count
    is_provisional = total_finalized < PROVISIONAL_THRESHOLD

    # 1. Quality Component (35%)
    if verification_scores:
        quality_score = sum(verification_scores) / len(verification_scores)
    else:
        quality_score = DEFAULT_COLD_START_SCORE
    quality_score = max(0.0, min(100.0, round(quality_score, 1)))

    # 2. Success Rate Component (30%)
    if total_finalized > 0:
        success_rate_score = (successful_count / total_finalized) * 100.0
    else:
        success_rate_score = DEFAULT_COLD_START_SCORE
    success_rate_score = max(0.0, min(100.0, round(success_rate_score, 1)))

    # 3. Reliability Component (20%)
    total_attempts = successful_count + failed_count + integrity_fail_count
    if total_attempts > 0:
        reliability_score = (successful_count / total_attempts) * 100.0
    else:
        reliability_score = DEFAULT_COLD_START_SCORE
    reliability_score = max(0.0, min(100.0, round(reliability_score, 1)))

    # 4. Consistency Component (10%)
    consistency_score = calculate_consistency_score(verification_scores)

    # 5. Experience Component (5%)
    experience_score = calculate_experience_score(successful_count)

    # Final Weighted Computation
    raw_reputation = (
        (quality_score * QUALITY_WEIGHT)
        + (success_rate_score * SUCCESS_RATE_WEIGHT)
        + (reliability_score * RELIABILITY_WEIGHT)
        + (consistency_score * CONSISTENCY_WEIGHT)
        + (experience_score * EXPERIENCE_WEIGHT)
    )

    reputation_score = max(0.0, min(100.0, round(raw_reputation, 1)))
    reputation_level = determine_reputation_level(reputation_score, is_provisional)

    return {
        "reputation_score": reputation_score,
        "reputation_level": reputation_level,
        "is_provisional": is_provisional,
        "quality_score": quality_score,
        "success_rate_score": success_rate_score,
        "reliability_score": reliability_score,
        "consistency_score": consistency_score,
        "experience_score": experience_score,
        "total_verified_tasks": total_finalized,
        "successful_verified_tasks": successful_count,
        "failed_verified_tasks": failed_count,
        "average_quality_score": quality_score,
    }


def record_reputation_event(
    db: Session,
    agent_id: int,
    event_type: str,
    previous_score: float,
    new_score: float,
    reason: str,
    task_id: Optional[int] = None,
    verification_id: Optional[int] = None,
    settlement_id: Optional[int] = None,
    quality_score: Optional[float] = None,
    verification_decision: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> ReputationEvent:
    """
    Creates an immutable reputation event audit entry with sequential RE-xxxx code.
    Guarantees idempotency for duplicate outcome triggers.
    """
    # Idempotency check: don't create duplicate event for identical outcome
    if task_id and event_type in ("successful_settlement", "verification_pass", "verification_fail", "integrity_failure", "review_required"):
        existing = db.query(ReputationEvent).filter(
            ReputationEvent.agent_id == agent_id,
            ReputationEvent.task_id == task_id,
            ReputationEvent.event_type == event_type,
        ).first()
        if existing:
            return existing

    score_delta = round(new_score - previous_score, 1)
    now = datetime.utcnow()

    event_obj = ReputationEvent(
        agent_id=agent_id,
        task_id=task_id,
        verification_id=verification_id,
        settlement_id=settlement_id,
        event_type=event_type,
        previous_score=previous_score,
        score_delta=score_delta,
        new_score=new_score,
        quality_score=quality_score,
        verification_decision=verification_decision,
        reason=reason,
        details=details or {},
        created_at=now,
    )
    db.add(event_obj)
    db.flush()
    return event_obj


def recalculate_agent_reputation(
    db: Session,
    agent_id: int,
    trigger_event_type: str = "recalculation",
    task_id: Optional[int] = None,
    verification_id: Optional[int] = None,
    settlement_id: Optional[int] = None,
    quality_score: Optional[float] = None,
    decision: Optional[str] = None,
    reason: Optional[str] = None,
) -> Tuple[Agent, Optional[ReputationEvent]]:
    """
    Recalculates an agent's reputation from full observable historical behavior,
    updates the Agent record, and writes an immutable ReputationEvent.
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).with_for_update().first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found.",
        )

    # 1. Gather historical verification outcomes where agent was the worker
    # We query submissions made by this agent that have a completed verification
    submissions = (
        db.query(ResultSubmission)
        .filter(ResultSubmission.agent_id == agent_id)
        .all()
    )
    submission_ids = [s.id for s in submissions]

    verification_scores: List[float] = []
    successful_count = 0
    failed_count = 0
    review_count = 0
    integrity_fail_count = 0

    if submission_ids:
        verifications = (
            db.query(Verification)
            .filter(Verification.submission_id.in_(submission_ids))
            .order_by(Verification.id.asc())
            .all()
        )

        for v in verifications:
            if v.decision == "PASS":
                successful_count += 1
                if v.overall_score is not None:
                    verification_scores.append(float(v.overall_score))
            elif v.decision == "FAIL":
                failed_count += 1
                if v.overall_score is not None:
                    verification_scores.append(float(v.overall_score))
            elif v.decision == "REVIEW":
                review_count += 1

            # Check if integrity was compromised
            if hasattr(v, "integrity_valid") and not v.integrity_valid:
                integrity_fail_count += 1

    # Also account for legacy task counts if they exist and exceed verifications
    if agent.tasks_completed and agent.tasks_completed > successful_count and not verification_scores:
        successful_count = agent.tasks_completed
    if agent.tasks_failed and agent.tasks_failed > failed_count and not verification_scores:
        failed_count = agent.tasks_failed

    # 2. Compute 5-Factor Reputation Breakdown
    breakdown = compute_reputation_breakdown(
        verification_scores=verification_scores,
        successful_count=successful_count,
        failed_count=failed_count,
        integrity_fail_count=integrity_fail_count,
    )

    prev_score = float(agent.reputation_score or DEFAULT_COLD_START_SCORE)
    new_score = breakdown["reputation_score"]
    delta = round(new_score - prev_score, 1)

    # 3. Update Agent Record
    now = datetime.utcnow()
    agent.reputation_score = new_score
    agent.reputation_level = breakdown["reputation_level"]
    agent.is_provisional = breakdown["is_provisional"]
    agent.total_verified_tasks = breakdown["total_verified_tasks"]
    agent.successful_verified_tasks = breakdown["successful_verified_tasks"]
    agent.failed_verified_tasks = breakdown["failed_verified_tasks"]
    agent.review_tasks = review_count
    agent.average_quality_score = breakdown["average_quality_score"]
    agent.average_verification_score = breakdown["average_quality_score"]
    agent.consistency_score = breakdown["consistency_score"]
    agent.reliability_score = breakdown["reliability_score"]
    agent.experience_score = breakdown["experience_score"]
    agent.tasks_completed = successful_count
    agent.tasks_failed = failed_count
    agent.success_rate = breakdown["success_rate_score"]
    agent.reputation_updated_at = now
    agent.updated_at = now

    # 4. Generate Explainable Audit Reason if not provided
    if not reason:
        if trigger_event_type == "successful_settlement":
            reason = (
                f"Reputation updated to {new_score:.1f} ({delta:+.1f}) after task "
                f"settlement completed successfully with verification score {quality_score or breakdown['average_quality_score']:.1f}."
            )
        elif trigger_event_type == "verification_fail":
            reason = (
                f"Reputation decreased to {new_score:.1f} ({delta:+.1f}) after task "
                f"failed independent verification (Score: {quality_score or 0.0:.1f})."
            )
        elif trigger_event_type == "integrity_failure":
            reason = (
                f"Reputation penalized to {new_score:.1f} ({delta:+.1f}) due to submission package integrity validation failure."
            )
        elif trigger_event_type == "review_required":
            reason = (
                f"Recorded review required for task. Reputation held at {new_score:.1f} awaiting outcome resolution."
            )
        else:
            reason = f"Reputation recalculated to {new_score:.1f} based on verified history ({successful_count} PASS, {failed_count} FAIL)."

    # 5. Record Reputation Event
    rep_event = record_reputation_event(
        db=db,
        agent_id=agent.id,
        event_type=trigger_event_type,
        previous_score=prev_score,
        new_score=new_score,
        reason=reason,
        task_id=task_id,
        verification_id=verification_id,
        settlement_id=settlement_id,
        quality_score=quality_score,
        verification_decision=decision,
        details=breakdown,
    )

    db.flush()
    return agent, rep_event


# ---------------------------------------------------------------------------
# Lifecycle Hooks
# ---------------------------------------------------------------------------

def on_settlement_completed(db: Session, settlement_id: int) -> Optional[ReputationEvent]:
    """
    Hook invoked when Phase 12 conditional settlement successfully releases AP credits to worker.
    Recalculates worker reputation with positive outcome event.
    """
    settlement = db.query(Settlement).filter(Settlement.id == settlement_id).first()
    if not settlement or settlement.status != "completed":
        return None

    verification = (
        db.query(Verification).filter(Verification.id == settlement.verification_id).first()
        if settlement.verification_id
        else None
    )

    task = db.query(Task).filter(Task.id == settlement.task_id).first()
    task_code = task.task_code if task else f"TK-{settlement.task_id}"

    quality = float(verification.overall_score) if verification and verification.overall_score else None

    reason = (
        f"Reputation increased after task {task_code} received a verification "
        f"PASS ({quality:.1f}/100) and completed settlement of {settlement.amount} AP."
    )

    _, event_obj = recalculate_agent_reputation(
        db=db,
        agent_id=settlement.worker_agent_id,
        trigger_event_type="successful_settlement",
        task_id=settlement.task_id,
        verification_id=settlement.verification_id,
        settlement_id=settlement.id,
        quality_score=quality,
        decision="PASS",
        reason=reason,
    )
    return event_obj


def on_verification_finalized(db: Session, verification_id: int) -> Optional[ReputationEvent]:
    """
    Hook invoked when Phase 10 verification is finalized (specifically for FAIL, REVIEW, or integrity failure).
    """
    verification = db.query(Verification).filter(Verification.id == verification_id).first()
    if not verification:
        return None

    submission = db.query(ResultSubmission).filter(ResultSubmission.id == verification.submission_id).first()
    if not submission:
        return None

    worker_id = submission.agent_id
    task = db.query(Task).filter(Task.id == verification.task_id).first()
    task_code = task.task_code if task else f"TK-{verification.task_id}"
    quality = float(verification.overall_score) if verification.overall_score else 0.0

    # Integrity Failure
    if hasattr(verification, "integrity_valid") and not verification.integrity_valid:
        reason = (
            f"Reputation penalized for task {task_code}: Submission package SHA-256 integrity validation failed."
        )
        _, event_obj = recalculate_agent_reputation(
            db=db,
            agent_id=worker_id,
            trigger_event_type="integrity_failure",
            task_id=verification.task_id,
            verification_id=verification.id,
            quality_score=quality,
            decision="FAIL",
            reason=reason,
        )
        return event_obj

    # Verification FAIL
    if verification.decision == "FAIL":
        reason = (
            f"Reputation decreased after task {task_code} failed independent verification "
            f"(Score: {quality:.1f} vs required {verification.required_score:.1f})."
        )
        _, event_obj = recalculate_agent_reputation(
            db=db,
            agent_id=worker_id,
            trigger_event_type="verification_fail",
            task_id=verification.task_id,
            verification_id=verification.id,
            quality_score=quality,
            decision="FAIL",
            reason=reason,
        )
        return event_obj

    # Verification REVIEW
    if verification.decision == "REVIEW":
        reason = (
            f"Recorded review required for task {task_code} (Score: {quality:.1f}). Reputation held pending resolution."
        )
        _, event_obj = recalculate_agent_reputation(
            db=db,
            agent_id=worker_id,
            trigger_event_type="review_required",
            task_id=verification.task_id,
            verification_id=verification.id,
            quality_score=quality,
            decision="REVIEW",
            reason=reason,
        )
        return event_obj

    return None


# ---------------------------------------------------------------------------
# Queries & APIs
# ---------------------------------------------------------------------------

def get_agent_reputation_breakdown(db: Session, agent_id: int) -> Dict[str, Any]:
    """Retrieve full reputation score breakdown and performance components for an agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found.",
        )

    # If reputation has never been populated, compute it
    if agent.reputation_score is None:
        agent, _ = recalculate_agent_reputation(db, agent_id)
        db.commit()

    return {
        "agent_id": agent.id,
        "agent_code": agent.agent_code,
        "agent_name": agent.name,
        "reputation_score": agent.reputation_score,
        "reputation_level": agent.reputation_level or determine_reputation_level(agent.reputation_score, agent.is_provisional),
        "is_provisional": agent.is_provisional if agent.is_provisional is not None else True,
        "quality_score": agent.average_quality_score or DEFAULT_COLD_START_SCORE,
        "success_rate_score": agent.success_rate or DEFAULT_COLD_START_SCORE,
        "reliability_score": agent.reliability_score or DEFAULT_COLD_START_SCORE,
        "consistency_score": agent.consistency_score or DEFAULT_COLD_START_SCORE,
        "experience_score": agent.experience_score or 50.0,
        "weights": {
            "quality": QUALITY_WEIGHT,
            "success_rate": SUCCESS_RATE_WEIGHT,
            "reliability": RELIABILITY_WEIGHT,
            "consistency": CONSISTENCY_WEIGHT,
            "experience": EXPERIENCE_WEIGHT,
        },
        "total_verified_tasks": agent.total_verified_tasks or 0,
        "successful_verified_tasks": agent.successful_verified_tasks or 0,
        "failed_verified_tasks": agent.failed_verified_tasks or 0,
        "review_tasks": agent.review_tasks or 0,
        "average_quality_score": agent.average_quality_score or DEFAULT_COLD_START_SCORE,
        "reputation_updated_at": agent.reputation_updated_at,
    }


def get_agent_reputation_history(
    db: Session,
    agent_id: int,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Retrieve chronological reputation events for an agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found.",
        )

    events = (
        db.query(ReputationEvent)
        .filter(ReputationEvent.agent_id == agent_id)
        .order_by(desc(ReputationEvent.id))
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = []
    for ev in events:
        task = db.query(Task).filter(Task.id == ev.task_id).first() if ev.task_id else None
        verif = db.query(Verification).filter(Verification.id == ev.verification_id).first() if ev.verification_id else None
        settle = db.query(Settlement).filter(Settlement.id == ev.settlement_id).first() if ev.settlement_id else None

        items.append({
            "id": ev.id,
            "event_code": ev.event_code,
            "agent_id": ev.agent_id,
            "task_id": ev.task_id,
            "task_code": task.task_code if task else None,
            "verification_id": ev.verification_id,
            "verification_code": verif.verification_code if verif else None,
            "settlement_id": ev.settlement_id,
            "settlement_code": settle.settlement_code if settle else None,
            "event_type": ev.event_type,
            "previous_score": ev.previous_score,
            "score_delta": ev.score_delta,
            "new_score": ev.new_score,
            "quality_score": ev.quality_score,
            "verification_decision": ev.verification_decision,
            "reason": ev.reason,
            "details": ev.details or {},
            "created_at": ev.created_at,
        })
    return items


def get_reputation_leaderboard(
    db: Session,
    limit: int = 50,
    agent_type: Optional[str] = None,
    capability: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve ranked agents sorted by reputation_score descending, then verified task count.
    """
    query = db.query(Agent).filter(Agent.is_active == True)

    if agent_type:
        query = query.filter(Agent.agent_type == agent_type.lower())

    agents = query.all()

    # In-memory filter for capability if requested
    if capability:
        cap_clean = capability.strip().lower()
        agents = [
            a for a in agents
            if any(cap_clean == c.strip().lower() for c in (a.capabilities or []))
        ]

    # Sort primarily by reputation_score desc, then total_verified_tasks desc
    agents.sort(
        key=lambda a: (
            float(a.reputation_score or 0.0),
            int(a.total_verified_tasks or 0),
            int(a.successful_verified_tasks or 0),
        ),
        reverse=True,
    )

    ranked_items = []
    for rank, a in enumerate(agents[:limit], start=1):
        ranked_items.append({
            "rank": rank,
            "agent_id": a.id,
            "agent_code": a.agent_code,
            "name": a.name,
            "agent_type": a.agent_type,
            "status": a.status,
            "is_active": a.is_active,
            "reputation_score": float(a.reputation_score or DEFAULT_COLD_START_SCORE),
            "reputation_level": a.reputation_level or determine_reputation_level(a.reputation_score or DEFAULT_COLD_START_SCORE, a.is_provisional),
            "is_provisional": a.is_provisional if a.is_provisional is not None else True,
            "total_verified_tasks": int(a.total_verified_tasks or 0),
            "successful_verified_tasks": int(a.successful_verified_tasks or 0),
            "success_rate": float(a.success_rate or 0.0),
            "average_quality_score": float(a.average_quality_score or DEFAULT_COLD_START_SCORE),
        })

    return ranked_items


def get_reputation_summary(db: Session) -> Dict[str, Any]:
    """Retrieve platform-wide trust & reputation summary distribution."""
    agents = db.query(Agent).filter(Agent.is_active == True).all()
    total = len(agents)
    if total == 0:
        return {
            "total_agents": 0,
            "established_agents": 0,
            "provisional_agents": 0,
            "excellent_count": 0,
            "strong_count": 0,
            "good_count": 0,
            "moderate_count": 0,
            "weak_count": 0,
            "high_risk_count": 0,
            "average_reputation": 0.0,
        }

    scores = [float(a.reputation_score or DEFAULT_COLD_START_SCORE) for a in agents]
    avg_score = round(sum(scores) / total, 1)

    provisional_count = sum(1 for a in agents if getattr(a, "is_provisional", True))
    established_count = total - provisional_count

    excellent = sum(1 for s in scores if s >= 90.0)
    strong = sum(1 for s in scores if 80.0 <= s < 90.0)
    good = sum(1 for s in scores if 70.0 <= s < 80.0)
    moderate = sum(1 for s in scores if 60.0 <= s < 70.0)
    weak = sum(1 for s in scores if 40.0 <= s < 60.0)
    high_risk = sum(1 for s in scores if s < 40.0)

    return {
        "total_agents": total,
        "established_agents": established_count,
        "provisional_agents": provisional_count,
        "excellent_count": excellent,
        "strong_count": strong,
        "good_count": good,
        "moderate_count": moderate,
        "weak_count": weak,
        "high_risk_count": high_risk,
        "average_reputation": avg_score,
    }


def recalculate_all_agent_reputations(db: Session) -> int:
    """Recalculate reputation for all agents in database."""
    agents = db.query(Agent).all()
    for a in agents:
        recalculate_agent_reputation(db, a.id, trigger_event_type="recalculation")
    db.commit()
    return len(agents)
