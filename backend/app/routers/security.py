from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db

from app.schemas.security import (
    SecurityEventResponse,
    AgentSecuritySummary,
    SuspendAgentRequest,
    RestoreAgentRequest,
)
from app.schemas.agent import AgentResponse
from app.services import security_service

router = APIRouter(tags=["security"])


@router.get(
    "/api/security/events",
    response_model=List[SecurityEventResponse],
    summary="List immutable platform security events and audit records",
)
def get_security_events(
    agent_id: Optional[int] = Query(None, description="Filter by agent ID"),
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return security_service.get_security_events(
        db,
        agent_id=agent_id,
        task_id=task_id,
        severity=severity,
        event_type=event_type,
        limit=limit,
    )


@router.get(
    "/api/agents/{agent_id}/security",
    response_model=AgentSecuritySummary,
    summary="Get security, risk, and violation summary for a specific agent",
)
def get_agent_security(
    agent_id: int,
    db: Session = Depends(get_db),
):
    return security_service.get_agent_security_summary(db, agent_id=agent_id)


@router.post(
    "/api/agents/{agent_id}/suspend",
    response_model=AgentResponse,
    summary="Suspend an agent due to policy or security violations",
)
def suspend_agent(
    agent_id: int,
    payload: SuspendAgentRequest,
    db: Session = Depends(get_db),
):
    return security_service.suspend_agent(
        db,
        agent_id=agent_id,
        reason=payload.reason,
        actor=payload.actor or "admin",
    )


@router.post(
    "/api/agents/{agent_id}/restore",
    response_model=AgentResponse,
    summary="Restore a suspended agent to active service",
)
def restore_agent(
    agent_id: int,
    payload: RestoreAgentRequest,
    db: Session = Depends(get_db),
):
    return security_service.restore_agent(
        db,
        agent_id=agent_id,
        reason=payload.reason,
        actor=payload.actor or "admin",
    )
