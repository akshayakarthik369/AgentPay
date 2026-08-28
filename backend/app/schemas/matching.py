from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime

class FactorBreakdown(BaseModel):
    capability_score: float
    reputation_score: float
    quality_score: float
    success_score: float
    availability_score: float

class TaskSummaryForMatch(BaseModel):
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

class AgentSummaryForMatch(BaseModel):
    id: int
    agent_code: Optional[str]
    name: str
    agent_type: str
    capabilities: List[str]
    status: str
    is_active: bool
    reputation_score: int
    wallet_balance: float

class TaskMatchResult(BaseModel):
    task: TaskSummaryForMatch
    overall_score: float
    capability_score: float
    reputation_score: float
    quality_score: float
    success_score: float
    availability_score: float
    eligible: bool
    match_level: str
    reasons: List[str]

class AgentMatchResult(BaseModel):
    agent: AgentSummaryForMatch
    overall_score: float
    capability_score: float
    reputation_score: float
    quality_score: float
    success_score: float
    availability_score: float
    eligible: bool
    match_level: str
    reasons: List[str]

class SingleAgentTaskMatchResponse(BaseModel):
    agent: AgentSummaryForMatch
    task: TaskSummaryForMatch
    overall_score: float
    capability_score: float
    reputation_score: float
    quality_score: float
    success_score: float
    availability_score: float
    eligible: bool
    match_level: str
    reasons: List[str]

class DiscoverableTaskMatchesResponse(BaseModel):
    agent: AgentSummaryForMatch
    matches: List[TaskMatchResult]
    total_matches: int
    tasks: Optional[List[Any]] = None

class TaskMatchingAgentsResponse(BaseModel):
    task: TaskSummaryForMatch
    agents: List[AgentMatchResult]
    total_agents: int
