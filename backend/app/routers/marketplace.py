from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from app.services.task_service import get_marketplace_stats

router = APIRouter(prefix="/api/marketplace", tags=["Marketplace"])


@router.get(
    "/stats",
    summary="Get real-time marketplace statistics",
)
def marketplace_stats(db: Session = Depends(get_db)):
    """
    Returns live marketplace statistics sourced from the Task table.

    - open_tasks: number of tasks currently in 'open' status
    - total_rewards: total AP Credits available across all open tasks
    - active_categories: number of distinct task categories with open tasks

    Used by the frontend marketplace summary bar.
    Also available to autonomous AI agents for discovery telemetry.
    """
    return get_marketplace_stats(db)
