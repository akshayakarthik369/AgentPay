"""
app/schemas/canary.py — Pydantic schemas for Phase 21 Canary Testing & Trust Lifecycle.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class CanarySubCheckDetail(BaseModel):
    name: str
    passed: bool
    score: float
    details: str


class CanaryTestRunRequest(BaseModel):
    """Optional payload when manually requesting a canary test run."""
    force_pass: Optional[bool] = None
    force_fail: Optional[bool] = None
    test_type: Optional[str] = None


class CanaryTestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canary_code: Optional[str] = None
    agent_id: int
    test_type: str
    required_capability: str
    attempt_number: int
    status: str
    score: Optional[float] = None
    required_score: float = 80.0
    integrity_passed: Optional[bool] = None
    policy_passed: Optional[bool] = None
    execution_passed: Optional[bool] = None
    result_summary: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class PromotionProgress(BaseModel):
    current_verified_tasks: int
    required_verified_tasks: int
    verified_tasks_met: bool
    current_reputation: float
    required_reputation: float
    reputation_met: bool
    current_risk_score: float
    max_risk_score: float
    risk_met: bool
    eligible_for_promotion: bool


class AgentTrustReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent_id: int
    agent_code: Optional[str] = None
    agent_name: str
    agent_type: str
    trust_status: str
    trust_label: str
    is_provisional: bool
    canary_passed: bool
    canary_attempts: int
    max_canary_attempts: int
    last_canary_score: Optional[float] = None
    reputation_score: float
    total_verified_tasks: int
    risk_score: float
    max_allowed_reward: Optional[float] = None
    promotion_progress: PromotionProgress
    recent_canary_tests: List[CanaryTestResponse] = []


class PromotionCheckResponse(BaseModel):
    agent_id: int
    promoted: bool
    previous_status: str
    new_status: str
    reason: str
    criteria_met: Dict[str, bool]
