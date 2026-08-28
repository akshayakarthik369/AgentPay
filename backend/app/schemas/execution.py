from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


class ExecutionStartResponse(BaseModel):
    id: int
    execution_code: Optional[str]
    task_id: int
    agent_id: int
    bid_id: int
    status: str
    progress: int
    started_at: Optional[datetime]
    created_at: datetime
    message: str

    model_config = {"from_attributes": True}


class ExecutionLogResponse(BaseModel):
    id: int
    execution_id: int
    level: str
    step: Optional[str]
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecutionResponse(BaseModel):
    id: int
    execution_code: Optional[str]
    task_id: int
    agent_id: int
    bid_id: int
    status: str
    progress: int
    attempt_number: int
    output_text: Optional[str]
    structured_output: Optional[str]
    execution_metadata: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    submitted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExecutionAgentSummary(BaseModel):
    id: int
    agent_code: Optional[str]
    name: str
    agent_type: str
    reputation_score: float


class ExecutionTaskSummary(BaseModel):
    id: int
    task_code: Optional[str]
    title: str
    description: str
    category: str
    required_capability: str
    reward: float
    status: str


class ExecutionBidSummary(BaseModel):
    id: int
    bid_code: Optional[str]
    bid_amount: float
    estimated_completion_minutes: int
    proposal: str
    selection_score: float


class ExecutionDetailResponse(BaseModel):
    id: int
    execution_code: Optional[str]
    task_id: int
    agent_id: int
    bid_id: int
    status: str
    progress: int
    attempt_number: int
    output_text: Optional[str]
    structured_output: Optional[str]
    execution_metadata: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    submitted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    task: Optional[ExecutionTaskSummary] = None
    agent: Optional[ExecutionAgentSummary] = None
    bid: Optional[ExecutionBidSummary] = None

    model_config = {"from_attributes": True}


class ExecutionLogsResponse(BaseModel):
    execution_id: int
    execution_code: Optional[str]
    logs: List[ExecutionLogResponse]
    total_logs: int


class ExecutionSubmitResponse(BaseModel):
    message: str
    execution_id: int
    execution_code: Optional[str]
    execution_status: str
    task_id: int
    task_code: Optional[str]
    task_status: str
    submitted_at: Optional[datetime]
    # Phase 9 additions
    submission_id: Optional[int] = None
    submission_code: Optional[str] = None


class AgentAssignedTaskItem(BaseModel):
    task_id: int
    task_code: Optional[str]
    title: str
    category: str
    required_capability: str
    reward: float
    deadline: datetime
    task_status: str
    bid_id: Optional[int]
    bid_code: Optional[str]
    bid_amount: Optional[float]
    execution_id: Optional[int]
    execution_code: Optional[str]
    execution_status: Optional[str]
    execution_progress: Optional[int]
    assigned_at: Optional[datetime]


class AgentAssignedTasksResponse(BaseModel):
    agent_id: int
    agent_code: Optional[str]
    tasks: List[AgentAssignedTaskItem]
    total: int
