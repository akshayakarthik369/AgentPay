import math
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, asc, desc

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskQueryParams, PaginatedTaskResponse, TaskResponse


# ---------------------------------------------------------------------------
# Column map for safe sorting (whitelist prevents SQL injection)
# ---------------------------------------------------------------------------
_SORT_COLUMN_MAP = {
    "created_at": Task.created_at,
    "reward": Task.reward,
    "deadline": Task.deadline,
    "minimum_reputation": Task.minimum_reputation,
    "minimum_quality_score": Task.minimum_quality_score,
}


def create_task(db: Session, data: TaskCreate) -> Task:
    """
    Insert a new Task into the database.
    The after_insert event on the Task model auto-populates task_code.
    We refresh the instance so all generated fields are available.
    """
    task = Task(
        title=data.title,
        description=data.description,
        category=data.category,
        required_capability=data.required_capability,
        reward=data.reward,
        deadline=data.deadline,
        minimum_reputation=data.minimum_reputation,
        minimum_quality_score=data.minimum_quality_score,
        status="open",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_all_tasks(db: Session) -> list[Task]:
    """Return all tasks ordered by newest first (kept for internal use)."""
    return db.query(Task).order_by(Task.created_at.desc()).all()


def get_task_by_id(db: Session, task_id: int) -> Optional[Task]:
    """Return a single task by primary key, or None if not found."""
    return db.query(Task).filter(Task.id == task_id).first()


def search_tasks(db: Session, params: TaskQueryParams) -> PaginatedTaskResponse:
    """
    Full marketplace search with optional filtering, sorting, and pagination.

    All parameters are optional — no filter = return all tasks.
    Uses SQLAlchemy ORM queries only (no raw SQL string concatenation).
    """
    query = db.query(Task)

    # --- Text search (case-insensitive across key fields) ---
    if params.search:
        term = f"%{params.search.strip()}%"
        query = query.filter(
            Task.title.ilike(term)
            | Task.description.ilike(term)
            | Task.category.ilike(term)
            | Task.required_capability.ilike(term)
            | Task.task_code.ilike(term)
        )

    # --- Status filter ---
    if params.status:
        query = query.filter(Task.status == params.status.lower().strip())

    # --- Category filter ---
    if params.category:
        query = query.filter(Task.category.ilike(f"%{params.category.strip()}%"))

    # --- Required capability filter ---
    if params.required_capability:
        query = query.filter(
            Task.required_capability.ilike(f"%{params.required_capability.strip()}%")
        )

    # --- Reward range ---
    if params.min_reward is not None:
        query = query.filter(Task.reward >= params.min_reward)
    if params.max_reward is not None:
        query = query.filter(Task.reward <= params.max_reward)

    # --- Minimum reputation filter ---
    # Return tasks whose required minimum_reputation <= the requested min_reputation
    # (i.e. "show tasks I qualify for").  When used as a pure lower-bound on the
    # field itself, use: Task.minimum_reputation >= params.min_reputation
    # Here we treat it as "tasks requiring AT LEAST this reputation":
    if params.min_reputation is not None:
        query = query.filter(Task.minimum_reputation <= params.min_reputation)

    # --- Count total before pagination ---
    total = query.count()

    # --- Sorting (whitelisted column map) ---
    sort_col = _SORT_COLUMN_MAP.get(params.sort_by, Task.created_at)
    order_fn = asc if params.sort_order == "asc" else desc
    query = query.order_by(order_fn(sort_col))

    # --- Pagination ---
    offset = (params.page - 1) * params.page_size
    tasks = query.offset(offset).limit(params.page_size).all()

    total_pages = max(1, math.ceil(total / params.page_size))

    return PaginatedTaskResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        page=params.page,
        page_size=params.page_size,
        total=total,
        total_pages=total_pages,
    )


def get_marketplace_stats(db: Session) -> dict:
    """
    Real-time marketplace statistics sourced from the Task table.
    Only counts tasks with status='open'.
    """
    open_tasks_query = db.query(Task).filter(Task.status == "open")
    open_tasks = open_tasks_query.count()

    total_rewards_result = db.query(func.sum(Task.reward)).filter(
        Task.status == "open"
    ).scalar()
    total_rewards = float(total_rewards_result or 0)

    active_categories = (
        db.query(Task.category)
        .filter(Task.status == "open")
        .distinct()
        .count()
    )

    return {
        "open_tasks": open_tasks,
        "total_rewards": total_rewards,
        "active_categories": active_categories,
    }


def get_dashboard_metrics(db: Session) -> dict:
    """
    Compute real task metrics from the database for the client dashboard.
    Payment-related fields remain at 0 until Phase 5+.
    """
    terminal_statuses = {"completed", "failed"}

    total_tasks = db.query(Task).count()
    active_tasks = db.query(Task).filter(
        Task.status.notin_(terminal_statuses)
    ).count()
    completed_tasks = db.query(Task).filter(
        Task.status == "completed"
    ).count()

    return {
        "total_tasks": total_tasks,
        "active_tasks": active_tasks,
        "completed_tasks": completed_tasks,
        "total_spent": 0,  # Phase 5+: real payment tracking
    }
