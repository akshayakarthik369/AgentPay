from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator, model_validator


# ---------------------------------------------------------------------------
# Request schema — what the frontend sends to CREATE a task
# ---------------------------------------------------------------------------

class TaskCreate(BaseModel):
    """Payload for creating a new task. Backend controls id, task_code, status, timestamps."""
    title: str
    description: str
    category: str
    required_capability: str
    reward: float
    deadline: datetime
    minimum_reputation: int = 0
    minimum_quality_score: int = 0

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be empty")
        return v

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("description must not be empty")
        return v

    @field_validator("required_capability")
    @classmethod
    def capability_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("required_capability must not be empty")
        return v

    @field_validator("reward")
    @classmethod
    def reward_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("reward must be greater than 0")
        return v

    @field_validator("minimum_reputation")
    @classmethod
    def reputation_range(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError("minimum_reputation must be between 0 and 100")
        return v

    @field_validator("minimum_quality_score")
    @classmethod
    def quality_range(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError("minimum_quality_score must be between 0 and 100")
        return v

    @model_validator(mode="after")
    def deadline_not_in_past(self) -> "TaskCreate":
        now = datetime.now(self.deadline.tzinfo) if self.deadline.tzinfo else datetime.utcnow()
        if self.deadline < now:
            raise ValueError("deadline must be a future date/time")
        return self

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Query parameter schema — marketplace search / filter / sort / pagination
# ---------------------------------------------------------------------------

# Whitelisted sort fields — prevents arbitrary column injection
VALID_SORT_FIELDS = {
    "created_at",
    "reward",
    "deadline",
    "minimum_reputation",
    "minimum_quality_score",
}

VALID_SORT_ORDERS = {"asc", "desc"}


class TaskQueryParams(BaseModel):
    """
    Validated query parameters for GET /api/tasks.
    All fields are optional; defaults produce 'newest-first, all tasks, page 1'.
    """
    search: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    required_capability: Optional[str] = None
    min_reward: Optional[float] = None
    max_reward: Optional[float] = None
    min_reputation: Optional[int] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    page: int = 1
    page_size: int = 12

    @field_validator("page")
    @classmethod
    def page_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("page must be >= 1")
        return v

    @field_validator("page_size")
    @classmethod
    def page_size_valid(cls, v: int) -> int:
        if not (1 <= v <= 50):
            raise ValueError("page_size must be between 1 and 50")
        return v

    @field_validator("min_reward")
    @classmethod
    def min_reward_non_negative(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("min_reward must be >= 0")
        return v

    @field_validator("max_reward")
    @classmethod
    def max_reward_non_negative(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("max_reward must be >= 0")
        return v

    @field_validator("min_reputation")
    @classmethod
    def reputation_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (0 <= v <= 100):
            raise ValueError("min_reputation must be between 0 and 100")
        return v

    @field_validator("sort_by")
    @classmethod
    def sort_by_whitelist(cls, v: str) -> str:
        if v not in VALID_SORT_FIELDS:
            # Safe fallback rather than 422 — keeps frontend resilient
            return "created_at"
        return v

    @field_validator("sort_order")
    @classmethod
    def sort_order_valid(cls, v: str) -> str:
        v = v.lower()
        if v not in VALID_SORT_ORDERS:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v

    @model_validator(mode="after")
    def max_gte_min_reward(self) -> "TaskQueryParams":
        if (
            self.min_reward is not None
            and self.max_reward is not None
            and self.max_reward < self.min_reward
        ):
            raise ValueError("max_reward must be >= min_reward")
        return self

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Response schemas — what the API returns
# ---------------------------------------------------------------------------

class TaskResponse(BaseModel):
    """Full task response including all backend-managed fields."""
    id: int
    task_code: Optional[str]
    title: str
    description: str
    category: str
    required_capability: str
    reward: float
    deadline: datetime
    minimum_reputation: int
    minimum_quality_score: int
    status: str
    assigned_agent_id: Optional[int] = None
    selected_bid_id: Optional[int] = None
    assigned_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}



class TaskListItem(BaseModel):
    """Compact response for marketplace listing."""
    id: int
    task_code: Optional[str]
    title: str
    category: str
    required_capability: str
    reward: float
    deadline: datetime
    minimum_reputation: int
    minimum_quality_score: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedTaskResponse(BaseModel):
    """Paginated task list returned by GET /api/tasks."""
    items: List[TaskResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
