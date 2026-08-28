from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from database import get_db
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.services.agent_service import (
    create_agent,
    get_agent_by_id,
    get_agents,
    update_agent,
    set_agent_active_status,
    get_discoverable_tasks_for_agent,
)

router = APIRouter(prefix="/api/agents", tags=["Agents"])

@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new agent",
)
def post_agent(payload: AgentCreate, db: Session = Depends(get_db)):
    """Register a new autonomous AI agent in the directory."""
    # Check duplicate name
    existing = get_agents(db, search=payload.name)
    for e in existing:
        if e.name.lower().strip() == payload.name.lower().strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with name '{payload.name}' already exists.",
            )
    return create_agent(db, payload)

@router.get(
    "",
    response_model=List[AgentResponse],
    status_code=status.HTTP_200_OK,
    summary="List agents with optional filtering",
)
def list_agents(
    agent_type: Optional[str] = Query(None, description="Filter by type (worker, requester, verifier, arbitrator)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (available, busy, offline, suspended)"),
    capability: Optional[str] = Query(None, description="Filter by capabilities"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search across name, description, capabilities"),
    db: Session = Depends(get_db),
):
    """Retrieve list of registered agents matching query filters."""
    return get_agents(
        db, 
        agent_type=agent_type, 
        status=status_filter, 
        capability=capability, 
        is_active=is_active, 
        search=search
    )

@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get agent details by ID",
)
def get_agent(agent_id: int, db: Session = Depends(get_db)):
    """Fetch details of a single agent. Returns 404 if not found."""
    agent = get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return agent

@router.patch(
    "/{agent_id}",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update agent fields",
)
def patch_agent(agent_id: int, payload: AgentUpdate, db: Session = Depends(get_db)):
    """Patch configurable agent fields (name, description, capabilities, status, agent_type)."""
    agent = update_agent(db, agent_id, payload)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return agent

@router.post(
    "/{agent_id}/activate",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate agent",
)
def activate_agent(agent_id: int, db: Session = Depends(get_db)):
    """Set an agent's active status to True, allowing participation in discovery."""
    agent = set_agent_active_status(db, agent_id, is_active=True)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return agent

@router.post(
    "/{agent_id}/deactivate",
    response_model=AgentResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate agent",
)
def deactivate_agent(agent_id: int, db: Session = Depends(get_db)):
    """Set an agent's active status to False, suspending from task discovery."""
    agent = set_agent_active_status(db, agent_id, is_active=False)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return agent

from app.schemas.matching import (
    DiscoverableTaskMatchesResponse,
    SingleAgentTaskMatchResponse,
)
from app.services.matching_service import (
    get_ranked_discoverable_tasks_for_agent,
    get_single_agent_task_match,
)

@router.get(
    "/{agent_id}/discoverable-tasks",
    response_model=DiscoverableTaskMatchesResponse,
    status_code=status.HTTP_200_OK,
    summary="Find ranked compatible open tasks for an agent",
)
def discover_tasks(
    agent_id: int,
    min_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum overall match score filter"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of task matches to return"),
    db: Session = Depends(get_db),
):
    """
    Returns open tasks ranked by suitability match score for an active, available agent.
    Includes full 5-factor breakdown, eligibility flag, and explainability reasons.
    """
    res = get_ranked_discoverable_tasks_for_agent(db, agent_id, min_score=min_score, limit=limit)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )
    return res

@router.get(
    "/{agent_id}/match/{task_id}",
    response_model=SingleAgentTaskMatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate detailed suitability match for a single agent-task pair",
)
def match_single_task(
    agent_id: int,
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    Calculate detailed factor breakdown, eligibility, match level, and explainability reasons
    for a specific agent-task pair.
    """
    res = get_single_agent_task_match(db, agent_id, task_id)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent or Task not found",
        )
    return res

