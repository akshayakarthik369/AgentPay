"""
app/routers/canary.py — REST API router for Phase 21 Canary Testing & Trust Lifecycle.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from app.schemas.canary import (
    CanaryTestResponse,
    CanaryTestRunRequest,
    AgentTrustReportResponse,
    PromotionCheckResponse,
)
from app.services import canary_service

router = APIRouter(prefix="/api/canary", tags=["Canary & Trust Lifecycle"])


@router.post("/run/{agent_id}", response_model=CanaryTestResponse, status_code=status.HTTP_201_CREATED)
def run_canary_benchmark(
    agent_id: int,
    payload: Optional[CanaryTestRunRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Trigger an automated or manual canary evaluation test for a newly registered or retry agent.
    Evaluates synthetic capability benchmarks across Integrity, Policy, and Execution accuracy.
    """
    force_pass = payload.force_pass if payload else None
    force_fail = payload.force_fail if payload else None
    test_type = payload.test_type if payload else None

    return canary_service.run_canary_test(
        db=db,
        agent_id=agent_id,
        force_pass=force_pass,
        force_fail=force_fail,
        test_type=test_type,
    )


@router.get("/tests", response_model=List[CanaryTestResponse])
def list_canary_tests(
    agent_id: Optional[int] = Query(None, description="Filter tests by specific agent ID"),
    status: Optional[str] = Query(None, description="Filter tests by status (passed, failed, running)"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve historical canary evaluation records sorted newest first."""
    return canary_service.get_all_canary_tests(
        db=db,
        agent_id=agent_id,
        status_filter=status,
        limit=limit,
    )


@router.get("/tests/{test_id}", response_model=CanaryTestResponse)
def get_canary_test(
    test_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a single canary evaluation record by ID."""
    test = canary_service.get_canary_test_by_id(db, test_id=test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canary test with id {test_id} not found",
        )
    return test


@router.get("/agent/{agent_id}/trust", response_model=AgentTrustReportResponse)
def get_agent_trust_report(
    agent_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve comprehensive trust lifecycle metrics, canary audit history,
    and progression status towards Trusted tier for an agent.
    """
    return canary_service.get_agent_trust_report(db=db, agent_id=agent_id)


@router.post("/agent/{agent_id}/promote", response_model=PromotionCheckResponse)
def evaluate_and_promote_agent(
    agent_id: int,
    db: Session = Depends(get_db),
):
    """
    Check if a provisional agent qualifies for promotion to Trusted tier
    (3+ verified tasks, 70+ rep score, <60 risk score) and execute promotion.
    """
    return canary_service.check_and_promote_agent(db=db, agent_id=agent_id)
