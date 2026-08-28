from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional
from sqlalchemy.orm import Session

from database import get_db
from app.schemas.task import (
    TaskCreate,
    TaskResponse,
    TaskQueryParams,
    PaginatedTaskResponse,
)
from app.services.task_service import (
    create_task,
    get_task_by_id,
    search_tasks,
)

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def post_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """
    Create a new task and store it in SQLite.
    Returns the full task including auto-generated task_code (AP-XXXX).
    """
    task = create_task(db, payload)
    return task


@router.get(
    "",
    response_model=PaginatedTaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Search and list tasks with filtering, sorting, and pagination",
)
def list_tasks(
    search: Optional[str] = Query(None, description="Full-text search across title, description, category, capability, task_code"),
    category: Optional[str] = Query(None, description="Filter by category (case-insensitive partial match)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by task status (e.g. open, bidding, completed)"),
    required_capability: Optional[str] = Query(None, description="Filter by required capability (case-insensitive partial match)"),
    min_reward: Optional[float] = Query(None, ge=0, description="Minimum reward (AP Credits)"),
    max_reward: Optional[float] = Query(None, ge=0, description="Maximum reward (AP Credits)"),
    min_reputation: Optional[int] = Query(None, ge=0, le=100, description="Filter tasks requiring at most this reputation score"),
    sort_by: str = Query("created_at", description="Sort field: created_at | reward | deadline | minimum_reputation | minimum_quality_score"),
    sort_order: str = Query("desc", description="Sort direction: asc | desc"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(12, ge=1, le=50, description="Items per page (max 50)"),
    db: Session = Depends(get_db),
):
    """
    Paginated, filtered, and sorted task marketplace feed.

    All filters are optional. Defaults: newest-first, all statuses, page 1, 12 per page.

    Designed for both human clients (marketplace UI) and future autonomous AI agents
    discovering tasks by capability and status.
    """
    params = TaskQueryParams(
        search=search,
        category=category,
        status=status_filter,
        required_capability=required_capability,
        min_reward=min_reward,
        max_reward=max_reward,
        min_reputation=min_reputation,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )
    return search_tasks(db, params)


from app.schemas.matching import TaskMatchingAgentsResponse
from app.services.matching_service import get_ranked_matching_agents_for_task

@router.get(
    "/{task_id}/matching-agents",
    response_model=TaskMatchingAgentsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get ranked AI agents for a specific task",
)
def get_matching_agents(
    task_id: int,
    min_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum overall match score filter"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of agents to return"),
    db: Session = Depends(get_db),
):
    """
    Reverse matching: Ranks all registered AI agents by suitability for the given task.
    Includes full factor breakdown, eligibility, and explainability reasons.
    """
    res = get_ranked_matching_agents_for_task(db, task_id, min_score=min_score, limit=limit)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return res

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single task by ID",
)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """
    Return a single task by its integer ID.
    Returns 404 if the task does not exist.
    """
    task = get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task


