"""
Phase 18 — Security & Malicious-Agent Handling Service.

Enforces security gates across the platform:
  - Malicious / invalid agent behavior detection & violation logging
  - Deterministic 0–100 risk scoring & risk levels
  - Agent suspension and restoration lifecycle
  - Conflict-of-interest enforcement (self-verification / self-arbitration blocking)
  - Participation eligibility guards for bidding, execution, verification, and arbitration
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.agent import Agent
from app.models.security import SecurityEvent


def calculate_risk_level(risk_score: float) -> str:
    """
    Determine risk classification tier from deterministic score (0–100):
      0–29   -> Low
      30–59  -> Medium
      60–79  -> High
      80–100 -> Critical
    """
    if risk_score < 30.0:
        return "Low"
    elif risk_score < 60.0:
        return "Medium"
    elif risk_score < 80.0:
        return "High"
    return "Critical"


def record_security_violation(
    db: Session,
    event_type: str,
    severity: str,
    reason: str,
    agent_id: Optional[int] = None,
    task_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    auto_commit: bool = True,
) -> SecurityEvent:
    """
    Record an immutable security audit event and adjust agent risk metrics.
    If risk escalates to Critical (>=80.0) or severity is 'critical', agent is auto-suspended.
    """
    event = SecurityEvent(
        event_type=event_type,
        severity=severity.lower(),
        reason=reason,
        agent_id=agent_id,
        task_id=task_id,
        details=details or {},
        created_at=datetime.utcnow(),
    )
    db.add(event)
    db.flush()

    if agent_id and event_type not in ("agent_restored", "agent_suspended"):
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if agent:
            agent.violation_count = (agent.violation_count or 0) + 1
            agent.last_violation_at = datetime.utcnow()

            # Dynamic risk increase based on severity
            sev = severity.lower()
            if sev == "critical":
                risk_delta = 50.0
            elif sev == "high":
                risk_delta = 35.0
            elif sev == "medium":
                risk_delta = 20.0
            else:
                risk_delta = 10.0

            current_risk = agent.risk_score or 0.0
            new_risk = min(100.0, max(0.0, current_risk + risk_delta))
            if sev == "critical" and new_risk < 85.0:
                new_risk = 85.0
            agent.risk_score = round(new_risk, 1)

            # Auto-suspend if risk is critical or severity is critical
            if (new_risk >= 80.0 or sev == "critical") and not agent.is_suspended:
                agent.is_suspended = True
                agent.status = "suspended"
                agent.suspension_reason = f"Auto-suspended due to {sev} security violation: {reason}"

                # Secondary log for auto-suspension
                suspension_event = SecurityEvent(
                    event_type="agent_suspended",
                    severity="high",
                    reason=f"Automated risk escalation trigger ({new_risk:.1f}/100): {reason}",
                    agent_id=agent.id,
                    task_id=task_id,
                    details={"trigger_event": event_type, "risk_score": new_risk},
                    created_at=datetime.utcnow(),
                )
                db.add(suspension_event)

    if auto_commit:
        db.commit()
        db.refresh(event)

    return event


def suspend_agent(
    db: Session,
    agent_id: int,
    reason: str,
    actor: str = "admin",
) -> Agent:
    """Manually or administratively suspend an agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found",
        )

    agent.is_suspended = True
    agent.status = "suspended"
    agent.suspension_reason = reason
    agent.risk_score = max(agent.risk_score or 0.0, 80.0)

    # Record security audit event
    record_security_violation(
        db,
        event_type="agent_suspended",
        severity="high",
        reason=f"Suspended by {actor}: {reason}",
        agent_id=agent.id,
        details={"actor": actor, "reason": reason},
        auto_commit=False,
    )

    db.commit()
    db.refresh(agent)
    return agent


def restore_agent(
    db: Session,
    agent_id: int,
    reason: Optional[str] = "Administrative clearance",
    actor: str = "admin",
) -> Agent:
    """Restore a suspended agent to active service and rehabilitate risk level."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found",
        )

    agent.is_suspended = False
    agent.status = "available"
    agent.suspension_reason = None
    # Lower risk to allow rehabilitation (capped at medium 40.0)
    agent.risk_score = min(agent.risk_score or 0.0, 40.0)

    # Record restore event
    record_security_violation(
        db,
        event_type="agent_restored",
        severity="low",
        reason=f"Restored by {actor}: {reason}",
        agent_id=agent.id,
        details={"actor": actor, "reason": reason, "restored_risk": agent.risk_score},
        auto_commit=False,
    )

    db.commit()
    db.refresh(agent)
    return agent


def check_agent_eligibility(agent: Agent, action: str = "participate") -> None:
    """
    Guard rule: Raise 403 Forbidden if agent is suspended or exceeds critical risk threshold.
    """
    if not agent:
        return

    if agent.is_suspended or agent.status == "suspended":
        reason = agent.suspension_reason or "Account suspended by security engine"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Security Policy: Agent '{agent.name}' is suspended ({reason}). Cannot {action}.",
        )

    if (agent.risk_score or 0.0) >= 80.0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Security Policy: Agent '{agent.name}' has Critical risk score ({agent.risk_score:.1f}/100). Cannot {action}.",
        )


def validate_no_conflict(
    worker_id: int,
    candidate_id: int,
    role: str = "verifier",
) -> None:
    """
    Guard rule: Raise 400 Bad Request if candidate is the worker of the same task.
    """
    if worker_id == candidate_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Conflict of Interest: Worker agent #{worker_id} cannot act as {role} for its own task deliverables.",
        )


def get_security_events(
    db: Session,
    agent_id: Optional[int] = None,
    task_id: Optional[int] = None,
    severity: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
) -> List[SecurityEvent]:
    """Query security events with optional filters, sorted newest first."""
    query = db.query(SecurityEvent)

    if agent_id is not None:
        query = query.filter(SecurityEvent.agent_id == agent_id)
    if task_id is not None:
        query = query.filter(SecurityEvent.task_id == task_id)
    if severity is not None:
        query = query.filter(SecurityEvent.severity == severity.lower())
    if event_type is not None:
        query = query.filter(SecurityEvent.event_type == event_type)

    return query.order_by(SecurityEvent.created_at.desc()).limit(limit).all()


def get_agent_security_summary(db: Session, agent_id: int) -> Dict[str, Any]:
    """Produce comprehensive security and risk report for a single agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found",
        )

    risk_score = float(agent.risk_score or 0.0)
    risk_level = calculate_risk_level(risk_score)
    recent_events = get_security_events(db, agent_id=agent.id, limit=10)

    return {
        "agent_id": agent.id,
        "agent_name": agent.name,
        "agent_code": agent.agent_code,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "violation_count": agent.violation_count or 0,
        "is_suspended": bool(agent.is_suspended),
        "suspension_reason": agent.suspension_reason,
        "last_violation_at": agent.last_violation_at,
        "status": agent.status,
        "recent_events": recent_events,
    }
