"""
Phase 10 — Independent Verifier Selection Service.

Selects the best eligible verifier agent for a submission:
  - Strict Independence: verifier != worker
  - Eligibility: active, agent_type == 'verifier', not suspended
  - Deterministic Ranking:
      • Capability alignment: 40%
      • Reputation score: 35%
      • Availability: 25%
"""
from __future__ import annotations

import json
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.result_submission import ResultSubmission
from app.config.verification import (
    VERIFIER_CAPABILITY_WEIGHT,
    VERIFIER_REPUTATION_WEIGHT,
    VERIFIER_AVAILABILITY_WEIGHT,
)


def calculate_verifier_suitability(
    verifier: Agent, required_capability: Optional[str]
) -> Tuple[float, dict]:
    """Calculate deterministic suitability score (0.00 – 1.00) for a verifier agent."""
    caps: List[str] = verifier.capabilities or []
    if isinstance(caps, str):
        try:
            caps = json.loads(caps)
        except Exception:
            caps = [caps]

    caps_lower = [c.lower() for c in caps]
    req_lower = (required_capability or "").lower()

    # 1. Capability factor (0.0 – 1.0)
    if req_lower and req_lower in caps_lower:
        cap_score = 1.0
        cap_note = f"Exact match for required capability: '{required_capability}'"
    elif any("verif" in c or "quality" in c or "eval" in c or "audit" in c for c in caps_lower):
        cap_score = 0.90
        cap_note = "Certified general verification capability"
    elif len(caps_lower) > 0:
        cap_score = 0.60
        cap_note = "General capability match"
    else:
        cap_score = 0.30
        cap_note = "No specialized capabilities declared"

    # 2. Reputation factor (0.0 – 1.0)
    rep_score = min(1.0, max(0.0, (verifier.reputation_score or 80.0) / 100.0))

    # 3. Availability factor (0.0 – 1.0)
    if verifier.status == "available":
        avail_score = 1.0
    elif verifier.status == "busy":
        avail_score = 0.50
    else:
        avail_score = 0.20

    # Weighted overall suitability
    overall = (
        cap_score * VERIFIER_CAPABILITY_WEIGHT
        + rep_score * VERIFIER_REPUTATION_WEIGHT
        + avail_score * VERIFIER_AVAILABILITY_WEIGHT
    )
    overall = round(overall, 4)

    breakdown = {
        "overall_suitability": overall,
        "capability_score": cap_score,
        "capability_note": cap_note,
        "reputation_score": rep_score,
        "availability_score": avail_score,
    }
    return overall, breakdown


def select_verifier(db: Session, submission: ResultSubmission) -> Optional[Agent]:
    """
    Select the optimal eligible verifier agent for a result submission.

    Rules:
      1. verifier.agent_type == 'verifier'
      2. verifier.is_active == True
      3. verifier.id != submission.agent_id (strict independence)
      4. Ranked by deterministic suitability formula
    """
    worker_id = submission.agent_id

    # Parse task required capability from frozen snapshot if available
    required_capability = None
    if submission.task_snapshot:
        try:
            ts = json.loads(submission.task_snapshot) if isinstance(submission.task_snapshot, str) else submission.task_snapshot
            required_capability = ts.get("required_capability")
        except Exception:
            pass

    # Query all active, non-suspended verifier candidates (excluding the worker)
    candidates = db.query(Agent).filter(
        Agent.agent_type == "verifier",
        Agent.is_active == True,
        Agent.is_suspended == False,
        Agent.status != "suspended",
        Agent.risk_score < 80.0,
        Agent.id != worker_id,
    ).all()

    if not candidates:
        return None

    # Score and rank candidates deterministically
    scored_candidates = []
    for verifier in candidates:
        suitability, _ = calculate_verifier_suitability(verifier, required_capability)
        scored_candidates.append((suitability, verifier.reputation_score or 0, verifier.id, verifier))

    # Sort descending by suitability, then reputation, then ascending ID for absolute determinism
    scored_candidates.sort(key=lambda item: (-item[0], -item[1], item[2]))

    # Best verifier
    return scored_candidates[0][3]
