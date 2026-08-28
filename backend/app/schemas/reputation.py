from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class ReputationComponents(BaseModel):
    """5-Factor Deterministic Reputation Components (0-100 scale)."""
    quality: float
    success_rate: float
    reliability: float
    consistency: float
    experience: float


class ReputationBreakdownResponse(BaseModel):
    """Detailed reputation calculation breakdown for an agent."""
    agent_id: int
    agent_code: Optional[str] = None
    agent_name: str
    reputation_score: float
    reputation_level: str
    is_provisional: bool
    
    # 5-Factor values
    quality_score: float
    success_rate_score: float
    reliability_score: float
    consistency_score: float
    experience_score: float
    
    # Weights explanation
    weights: Dict[str, float]
    
    # Performance task metrics
    total_verified_tasks: int
    successful_verified_tasks: int
    failed_verified_tasks: int
    review_tasks: int
    average_quality_score: float
    
    reputation_updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ReputationEventResponse(BaseModel):
    """Audit record for a reputation recalculation event."""
    id: int
    event_code: Optional[str] = None
    agent_id: int
    task_id: Optional[int] = None
    task_code: Optional[str] = None
    verification_id: Optional[int] = None
    verification_code: Optional[str] = None
    settlement_id: Optional[int] = None
    settlement_code: Optional[str] = None
    event_type: str
    previous_score: float
    score_delta: float
    new_score: float
    quality_score: Optional[float] = None
    verification_decision: Optional[str] = None
    reason: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LeaderboardAgentItem(BaseModel):
    """Agent entry on the reputation leaderboard."""
    rank: int
    agent_id: int
    agent_code: Optional[str] = None
    name: str
    agent_type: str
    status: str
    is_active: bool
    reputation_score: float
    reputation_level: str
    is_provisional: bool
    total_verified_tasks: int
    successful_verified_tasks: int
    success_rate: float
    average_quality_score: float

    model_config = {"from_attributes": True}


class ReputationSummaryResponse(BaseModel):
    """Platform-wide trust & reputation summary metrics."""
    total_agents: int
    established_agents: int
    provisional_agents: int
    excellent_count: int
    strong_count: int
    good_count: int
    moderate_count: int
    weak_count: int
    high_risk_count: int
    average_reputation: float
