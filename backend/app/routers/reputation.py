"""
Reputation & Trust Engine API Router for AgentPay (Phase 13).
Provides endpoints for agent reputation breakdown, audit history, leaderboard, and platform trust summary.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db

from app.schemas.reputation import (
    ReputationBreakdownResponse,
    ReputationEventResponse,
    LeaderboardAgentItem,
    ReputationSummaryResponse,
)
from app.services import reputation_service

router = APIRouter(tags=["reputation"])


@router.get(
    "/api/agents/{agent_id}/reputation",
    response_model=ReputationBreakdownResponse,
    summary="Get 5-factor reputation breakdown for a specific agent",
)
def get_agent_reputation(
    agent_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve full reputation score breakdown, 5 performance components, and weights."""
    return reputation_service.get_agent_reputation_breakdown(db, agent_id)


@router.get(
    "/api/agents/{agent_id}/reputation/history",
    response_model=List[ReputationEventResponse],
    summary="Get chronological reputation audit trail for an agent",
)
def get_agent_reputation_history(
    agent_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve immutable reputation delta and state transition events."""
    return reputation_service.get_agent_reputation_history(db, agent_id, limit=limit, offset=offset)


@router.get(
    "/api/agents/reputation/leaderboard",
    response_model=List[LeaderboardAgentItem],
    summary="Get ranked agent leaderboard by reputation",
)
@router.get(
    "/api/reputation/leaderboard",
    response_model=List[LeaderboardAgentItem],
    summary="Get ranked agent leaderboard by reputation (alias)",
)
def get_reputation_leaderboard(
    limit: int = Query(50, ge=1, le=200),
    agent_type: Optional[str] = Query(None, description="Filter by agent type: worker, verifier, etc."),
    capability: Optional[str] = Query(None, description="Filter by capability"),
    db: Session = Depends(get_db),
):
    """Retrieve ranked active agents sorted by reputation score and completed task count."""
    return reputation_service.get_reputation_leaderboard(
        db, limit=limit, agent_type=agent_type, capability=capability
    )


@router.get(
    "/api/reputation/summary",
    response_model=ReputationSummaryResponse,
    summary="Get platform-wide trust and reputation summary metrics",
)
def get_reputation_summary(
    db: Session = Depends(get_db),
):
    """Retrieve high-level trust metrics, tier distributions, and average reputation."""
    return reputation_service.get_reputation_summary(db)


@router.post(
    "/api/reputation/recalculate-all",
    summary="Recalculate reputation for all agents (Admin/Migration utility)",
)
def recalculate_all_reputations(
    db: Session = Depends(get_db),
):
    """Recomputes all agent reputations from full verified history."""
    count = reputation_service.recalculate_all_agent_reputations(db)
    return {"status": "ok", "recalculated_agents": count}
