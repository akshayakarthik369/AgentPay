from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class BidCreate(BaseModel):
    task_id: int
    agent_id: int
    bid_amount: float = Field(..., gt=0, description="Bid amount in AP Credits (must be > 0 and <= task reward)")
    estimated_completion_minutes: int = Field(..., gt=0, description="Estimated completion time in minutes")
    proposal: str = Field(..., min_length=5, max_length=1000, description="Proposal pitch explaining agent approach")

    @field_validator("proposal")
    @classmethod
    def strip_proposal(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 5:
            raise ValueError("Proposal must be at least 5 characters")
        return s

class BidUpdate(BaseModel):
    bid_amount: Optional[float] = Field(None, gt=0)
    estimated_completion_minutes: Optional[int] = Field(None, gt=0)
    proposal: Optional[str] = Field(None, min_length=5, max_length=1000)

class BidAgentSummary(BaseModel):
    id: int
    agent_code: Optional[str]
    name: str
    agent_type: str
    reputation_score: int
    status: str

class BidTaskSummary(BaseModel):
    id: int
    task_code: Optional[str]
    title: str
    category: str
    required_capability: str
    reward: float
    status: str

class BidResponse(BaseModel):
    id: int
    bid_code: Optional[str]
    task_id: int
    agent_id: int
    bid_amount: float
    estimated_completion_minutes: int
    proposal: str
    match_score_snapshot: float
    reputation_snapshot: int
    selection_score: float
    status: str
    created_at: datetime
    updated_at: datetime
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None

    agent: Optional[BidAgentSummary] = None
    task: Optional[BidTaskSummary] = None

class RankedBidItem(BaseModel):
    id: int
    bid_code: Optional[str]
    task_id: int
    agent_id: int
    bid_amount: float
    estimated_completion_minutes: int
    proposal: str
    match_score: float
    price_score: float
    speed_score: float
    selection_score: float
    status: str
    created_at: datetime
    updated_at: datetime
    reasons: List[str]
    agent: BidAgentSummary

class TaskBidsListResponse(BaseModel):
    task_id: int
    task_code: Optional[str]
    task_status: str
    reward: float
    bids: List[RankedBidItem]
    total_bids: int

class AgentBidsListResponse(BaseModel):
    agent_id: int
    agent_code: Optional[str]
    bids: List[BidResponse]
    total_bids: int

class SelectBidResponse(BaseModel):
    message: str
    task_id: int
    task_code: Optional[str]
    task_status: str
    assigned_agent_id: int
    assigned_agent_name: str
    assigned_agent_code: Optional[str]
    selected_bid_id: int
    selected_bid_code: Optional[str]
    selected_bid_amount: float
    assigned_at: datetime
    # Phase 11 — Escrow fields
    escrow_id: Optional[int] = None
    escrow_code: Optional[str] = None
    escrow_status: Optional[str] = None
    reward_locked: Optional[float] = None
