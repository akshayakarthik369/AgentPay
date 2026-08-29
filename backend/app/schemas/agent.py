from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator, model_validator

VALID_AGENT_TYPES = {"worker", "requester", "verifier", "arbitrator"}
VALID_STATUSES = {"available", "busy", "offline", "suspended"}

class AgentCreate(BaseModel):
    """Payload for registering a new agent."""
    name: str
    agent_type: str = "worker"
    description: Optional[str] = None
    capabilities: List[str]
    status: Optional[str] = "available"
    trust_status: Optional[str] = "pending_canary"

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        return v

    @field_validator("agent_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_AGENT_TYPES:
            raise ValueError(f"agent_type must be one of {VALID_AGENT_TYPES}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.lower().strip()
            if v not in VALID_STATUSES:
                raise ValueError(f"status must be one of {VALID_STATUSES}")
        return v

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, v: List[str], info) -> List[str]:
        cleaned = [c.strip() for c in v if c.strip()]
        return cleaned

    @model_validator(mode="after")
    def validate_worker_verifier_capabilities(self) -> "AgentCreate":
        if self.agent_type in ("worker", "verifier") and not self.capabilities:
            raise ValueError(f"Agents of type '{self.agent_type}' must specify at least one capability.")
        return self

    model_config = {"from_attributes": True}


class AgentUpdate(BaseModel):
    """Payload for updating an existing agent."""
    name: Optional[str] = None
    description: Optional[str] = None
    capabilities: Optional[List[str]] = None
    status: Optional[str] = None
    agent_type: Optional[str] = None
    is_active: Optional[bool] = None
    trust_status: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("name must not be empty")
        return v

    @field_validator("agent_type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.lower().strip()
            if v not in VALID_AGENT_TYPES:
                raise ValueError(f"agent_type must be one of {VALID_AGENT_TYPES}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = v.lower().strip()
            if v not in VALID_STATUSES:
                raise ValueError(f"status must be one of {VALID_STATUSES}")
        return v

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            return [c.strip() for c in v if c.strip()]
        return v

    model_config = {"from_attributes": True}


class AgentResponse(BaseModel):
    """Response schema containing full agent details."""
    id: int
    agent_code: Optional[str]
    name: str
    agent_type: str
    description: Optional[str]
    capabilities: List[str]
    status: str
    reputation_score: float
    reputation_level: Optional[str] = "Provisional"
    is_provisional: Optional[bool] = True
    total_verified_tasks: Optional[int] = 0
    successful_verified_tasks: Optional[int] = 0
    failed_verified_tasks: Optional[int] = 0
    review_tasks: Optional[int] = 0
    average_quality_score: Optional[float] = 80.0
    consistency_score: Optional[float] = 80.0
    reliability_score: Optional[float] = 80.0
    experience_score: Optional[float] = 50.0
    wallet_balance: float
    tasks_completed: int
    tasks_failed: Optional[int] = 0
    success_rate: float
    average_verification_score: float
    is_active: bool
    # Phase 18 Security & Phase 21 Trust fields
    trust_status: Optional[str] = "trusted"
    risk_score: Optional[float] = 0.0
    is_suspended: Optional[bool] = False
    suspension_reason: Optional[str] = None
    violation_count: Optional[int] = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
