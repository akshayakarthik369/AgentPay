from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class SecurityEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_code: Optional[str] = None
    agent_id: Optional[int] = None
    task_id: Optional[int] = None
    event_type: str
    severity: str
    reason: str
    details: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


class AgentSecuritySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent_id: int
    agent_name: str
    agent_code: Optional[str] = None
    risk_score: float
    risk_level: str
    violation_count: int
    is_suspended: bool
    suspension_reason: Optional[str] = None
    last_violation_at: Optional[datetime] = None
    status: str
    recent_events: List[SecurityEventResponse] = []


class SuspendAgentRequest(BaseModel):
    reason: str
    actor: Optional[str] = "admin"


class RestoreAgentRequest(BaseModel):
    reason: Optional[str] = "Administrative clearance"
    actor: Optional[str] = "admin"
