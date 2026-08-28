from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db

from app.schemas.history import ActivityEvent, TransactionItem
from app.services import history_service

router = APIRouter(tags=["history"])


@router.get(
    "/api/activity",
    response_model=List[ActivityEvent],
    summary="Global activity feed — complete task lifecycle events across all tasks",
)
def get_global_activity(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    task_id: Optional[int] = Query(None, description="Filter by task ID"),
    agent_id: Optional[int] = Query(None, description="Filter by agent ID"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return history_service.get_global_activity(
        db, event_type=event_type, task_id=task_id, agent_id=agent_id, limit=limit
    )


@router.get(
    "/api/tasks/{task_id}/activity",
    response_model=List[ActivityEvent],
    summary="Complete lifecycle timeline for a specific task",
)
def get_task_activity(
    task_id: int,
    db: Session = Depends(get_db),
):
    return history_service.get_task_activity(db, task_id=task_id)


@router.get(
    "/api/agents/{agent_id}/activity",
    response_model=List[ActivityEvent],
    summary="Activity history for a specific agent",
)
def get_agent_activity(
    agent_id: int,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return history_service.get_agent_activity(db, agent_id=agent_id, limit=limit)


@router.get(
    "/api/wallets/{wallet_id}/transactions",
    response_model=List[TransactionItem],
    summary="Real AP Credit transaction history for a wallet",
)
def get_wallet_transactions(
    wallet_id: int,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return history_service.get_wallet_transactions(db, wallet_id=wallet_id, limit=limit)


@router.get(
    "/api/wallets/transactions",
    response_model=List[TransactionItem],
    summary="All real AP Credit transactions (ledger)",
)
def get_all_transactions(
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return history_service.get_wallet_transactions(db, wallet_id=None, limit=limit)
