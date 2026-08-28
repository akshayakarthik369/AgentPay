"""
Matching Service for AgentPay.
Calculates agent-task suitability scores (0-100), factor breakdowns, eligibility, and human-readable explainability reasons.
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.models.task import Task
from app.config.matching import (
    CAPABILITY_WEIGHT,
    REPUTATION_WEIGHT,
    QUALITY_WEIGHT,
    SUCCESS_WEIGHT,
    AVAILABILITY_WEIGHT,
    EXACT_CAPABILITY_SCORE,
    RELATED_CAPABILITY_SCORE,
    NO_CAPABILITY_SCORE,
    DEFAULT_NEW_AGENT_QUALITY,
    DEFAULT_NEW_AGENT_SUCCESS_RATE,
    CAPABILITY_RELATIONSHIP_MAP,
    get_match_level,
)


def _normalize_str(val: Optional[str]) -> str:
    """Normalize string for robust, case-insensitive comparison."""
    return val.strip().lower() if val else ""


def _is_task_expired(task: Task) -> bool:
    """Check whether a task deadline has passed."""
    if not task.deadline:
        return False
    now = datetime.now(timezone.utc)
    dl = task.deadline
    if dl.tzinfo is None:
        dl = dl.replace(tzinfo=timezone.utc)
    return dl < now


def calculate_capability_score(agent: Agent, task: Task) -> Tuple[float, Optional[str]]:
    """
    Calculate capability match factor (0 to 100).
    - Exact match: 100
    - Related match via capability relationship map: 70
    - No match: 0
    """
    task_req = _normalize_str(task.required_capability)
    if not task_req:
        return 100.0, "No specific capability required by task"

    agent_caps = [_normalize_str(c) for c in (agent.capabilities or [])]

    # 1. Exact match check
    if task_req in agent_caps:
        return EXACT_CAPABILITY_SCORE, f"Exact capability match for '{task.required_capability}'"

    # 2. Related capability check
    for cap in agent_caps:
        related = CAPABILITY_RELATIONSHIP_MAP.get(cap, set())
        if task_req in related:
            return RELATED_CAPABILITY_SCORE, f"Related capability match ('{task.required_capability}' aligns with agent's '{cap}')"

    # Also check reverse in map
    task_related = CAPABILITY_RELATIONSHIP_MAP.get(task_req, set())
    for cap in agent_caps:
        if cap in task_related:
            return RELATED_CAPABILITY_SCORE, f"Related capability match ('{task.required_capability}' aligns with agent's '{cap}')"

    return NO_CAPABILITY_SCORE, f"No match for required capability '{task.required_capability}'"


def calculate_reputation_score(agent: Agent, task: Task) -> Tuple[float, str]:
    """
    Calculate reputation fit factor (0 to 100).
    Compares agent.reputation_score against task.minimum_reputation.
    """
    min_rep = task.minimum_reputation or 0
    agent_rep = float(agent.reputation_score if agent.reputation_score is not None else 80.0)

    if min_rep <= 0:
        return 100.0, "No minimum reputation required"

    if agent_rep >= min_rep:
        surplus = round(agent_rep - min_rep, 1)
        score = 100.0
        reason = f"Reputation ({agent_rep:.1f}) satisfies requirement (min {min_rep})"
        if surplus > 10:
            reason = f"Reputation ({agent_rep:.1f}) exceeds minimum requirement by {surplus} points"
        return score, reason
    else:
        deficit = round(min_rep - agent_rep, 1)
        score = max(0.0, round(100.0 - (deficit * 3.0), 1))
        reason = f"Reputation ({agent_rep:.1f}) is {deficit} points below required minimum ({min_rep})"
        return score, reason


def calculate_quality_score(agent: Agent, task: Task) -> Tuple[float, str]:
    """
    Calculate historical quality factor (0 to 100).
    Compares agent.average_quality_score against task.minimum_quality_score.
    Uses DEFAULT_NEW_AGENT_QUALITY baseline if agent has 0 verified tasks.
    """
    min_qual = task.minimum_quality_score or 0
    is_new = (getattr(agent, "total_verified_tasks", 0) or agent.tasks_completed or 0) == 0

    if is_new:
        agent_qual = DEFAULT_NEW_AGENT_QUALITY
        base_note = f"New agent quality baseline used ({DEFAULT_NEW_AGENT_QUALITY:.0f})"
    else:
        agent_qual = getattr(agent, "average_quality_score", None) or agent.average_verification_score or DEFAULT_NEW_AGENT_QUALITY
        base_note = f"Historical verification quality is {agent_qual:.1f}"

    if min_qual <= 0:
        return float(agent_qual), f"{base_note} (no minimum specified)"

    if agent_qual >= min_qual:
        return 100.0, f"{base_note}, meeting quality threshold (min {min_qual})"
    else:
        deficit = min_qual - agent_qual
        score = max(0.0, round(100.0 - (deficit * 2.0), 1))
        return score, f"{base_note}, below required quality threshold ({min_qual})"


def calculate_success_score(agent: Agent) -> Tuple[float, str]:
    """
    Calculate success rate factor (0 to 100).
    Uses DEFAULT_NEW_AGENT_SUCCESS_RATE if agent has 0 verified tasks.
    """
    is_new = (getattr(agent, "total_verified_tasks", 0) or agent.tasks_completed or 0) == 0
    if is_new:
        return DEFAULT_NEW_AGENT_SUCCESS_RATE, f"New agent success rate baseline used ({DEFAULT_NEW_AGENT_SUCCESS_RATE:.0f}%)"

    rate = float(agent.success_rate if agent.success_rate is not None else 0.0)
    if rate >= 90.0:
        return rate, f"High historical success rate ({rate:.1f}%)"
    elif rate >= 70.0:
        return rate, f"Standard historical success rate ({rate:.1f}%)"
    else:
        return rate, f"Historical success rate ({rate:.1f}%) below preferred target"


def calculate_availability_score_and_eligibility(agent: Agent, task: Task) -> Tuple[float, bool, List[str]]:
    """
    Calculate availability score (0 to 100), boolean eligibility, and status reasons.
    """
    reasons = []
    eligible = True
    avail_score = 100.0

    # 1. Agent active state
    if not agent.is_active:
        avail_score = 0.0
        eligible = False
        reasons.append("Agent is currently inactive / disabled")

    # 2. Agent status
    status_lower = _normalize_str(agent.status)
    if status_lower == "available":
        if agent.is_active:
            reasons.append("Agent is active and currently available")
    elif status_lower == "busy":
        avail_score = min(avail_score, 40.0)
        # Busy agents are still theoretically capable of evaluating matches, but penalized
        reasons.append("Agent is currently busy with ongoing tasks")
    elif status_lower in ("offline", "suspended"):
        avail_score = 0.0
        eligible = False
        reasons.append(f"Agent is {status_lower}")
    else:
        avail_score = 0.0
        eligible = False
        reasons.append(f"Agent has unknown status '{agent.status}'")

    # 3. Task status & expiration
    task_status_lower = _normalize_str(task.status)
    if task_status_lower != "open":
        eligible = False
        reasons.append(f"Task is not open (status: {task.status})")

    if _is_task_expired(task):
        eligible = False
        reasons.append("Task deadline has expired")

    return avail_score, eligible, reasons


def score_agent_task_pair(agent: Agent, task: Task) -> Dict[str, Any]:
    """
    Calculate complete 5-factor suitability score, eligibility, match level, and explainability reasons.
    """
    reasons: List[str] = []

    # 1. Capability Factor (50%)
    cap_score, cap_reason = calculate_capability_score(agent, task)
    if cap_reason:
        reasons.append(cap_reason)

    # 2. Reputation Fit (20%)
    rep_score, rep_reason = calculate_reputation_score(agent, task)
    reasons.append(rep_reason)

    # 3. Quality Factor (15%)
    qual_score, qual_reason = calculate_quality_score(agent, task)
    reasons.append(qual_reason)

    # 4. Success Rate (10%)
    succ_score, succ_reason = calculate_success_score(agent)
    reasons.append(succ_reason)

    # 5. Availability & Eligibility (5%)
    avail_score, eligible, avail_reasons = calculate_availability_score_and_eligibility(agent, task)
    reasons.extend(avail_reasons)

    # Weighted Overall Score (0 - 100)
    overall_score = round(
        (cap_score * CAPABILITY_WEIGHT)
        + (rep_score * REPUTATION_WEIGHT)
        + (qual_score * QUALITY_WEIGHT)
        + (succ_score * SUCCESS_WEIGHT)
        + (avail_score * AVAILABILITY_WEIGHT),
        1
    )

    # Clean bounds
    overall_score = max(0.0, min(100.0, overall_score))
    match_level = get_match_level(overall_score)

    return {
        "overall_score": overall_score,
        "capability_score": round(cap_score, 1),
        "reputation_score": round(rep_score, 1),
        "quality_score": round(qual_score, 1),
        "success_score": round(succ_score, 1),
        "availability_score": round(avail_score, 1),
        "eligible": eligible,
        "match_level": match_level,
        "reasons": reasons,
    }


def _task_to_summary(task: Task) -> Dict[str, Any]:
    return {
        "id": task.id,
        "task_code": task.task_code,
        "title": task.title,
        "category": task.category,
        "required_capability": task.required_capability,
        "reward": task.reward,
        "deadline": task.deadline,
        "minimum_reputation": task.minimum_reputation,
        "minimum_quality_score": task.minimum_quality_score,
        "status": task.status,
    }


def _agent_to_summary(agent: Agent) -> Dict[str, Any]:
    return {
        "id": agent.id,
        "agent_code": agent.agent_code,
        "name": agent.name,
        "agent_type": agent.agent_type,
        "capabilities": agent.capabilities or [],
        "status": agent.status,
        "is_active": agent.is_active,
        "reputation_score": agent.reputation_score,
        "wallet_balance": agent.wallet_balance,
    }


def get_ranked_discoverable_tasks_for_agent(
    db: Session,
    agent_id: int,
    min_score: Optional[float] = None,
    limit: int = 20,
) -> Optional[Dict[str, Any]]:
    """
    Retrieve and rank all compatible open tasks for an agent, sorted by overall suitability descending.
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        return None

    limit = max(1, min(50, limit))

    # If agent is inactive or offline, they cannot discover eligible tasks
    if not agent.is_active or agent.status not in ("available", "busy"):
        return {
            "agent": _agent_to_summary(agent),
            "matches": [],
            "total_matches": 0,
            "tasks": [],
        }


    # Query all open tasks
    open_tasks = db.query(Task).filter(Task.status == "open").all()
    results = []

    for task in open_tasks:
        # Exclude expired tasks from regular discovery
        if _is_task_expired(task):
            continue

        match_data = score_agent_task_pair(agent, task)

        # Filter by min_score if provided
        if min_score is not None and match_data["overall_score"] < min_score:
            continue

        # For discoverable tasks, only include tasks with at least partial capability match or score > 0
        if match_data["capability_score"] <= 0 and min_score is None:
            # Skip completely unrelated tasks from primary discovery list
            continue

        results.append({
            "task": _task_to_summary(task),
            **match_data,
        })

    # Sort descending by overall_score, then reward
    results.sort(key=lambda x: (x["overall_score"], x["task"]["reward"]), reverse=True)
    sliced_results = results[:limit]

    return {
        "agent": _agent_to_summary(agent),
        "matches": sliced_results,
        "total_matches": len(results),
        "tasks": [r["task"] for r in sliced_results],
    }



def get_single_agent_task_match(
    db: Session,
    agent_id: int,
    task_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Calculate in-depth suitability score and factor breakdown for a specific agent-task pair.
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    task = db.query(Task).filter(Task.id == task_id).first()

    if not agent or not task:
        return None

    match_data = score_agent_task_pair(agent, task)

    return {
        "agent": _agent_to_summary(agent),
        "task": _task_to_summary(task),
        **match_data,
    }


def get_ranked_matching_agents_for_task(
    db: Session,
    task_id: int,
    min_score: Optional[float] = None,
    limit: int = 20,
) -> Optional[Dict[str, Any]]:
    """
    Reverse matching: Rank all registered AI agents for a specific task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return None

    limit = max(1, min(50, limit))
    agents = db.query(Agent).all()
    results = []

    for agent in agents:
        match_data = score_agent_task_pair(agent, task)

        if min_score is not None and match_data["overall_score"] < min_score:
            continue

        results.append({
            "agent": _agent_to_summary(agent),
            **match_data,
        })

    # Sort descending by overall_score, then agent reputation
    results.sort(key=lambda x: (x["overall_score"], x["agent"]["reputation_score"]), reverse=True)
    sliced_results = results[:limit]

    return {
        "task": _task_to_summary(task),
        "agents": sliced_results,
        "total_agents": len(results),
    }
