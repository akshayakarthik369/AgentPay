from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, JSON, event
from sqlalchemy.orm import relationship
from database import Base


class Agent(Base):
    """SQLAlchemy model for AgentPay autonomous AI agents."""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    agent_code = Column(String(20), unique=True, nullable=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    agent_type = Column(String(100), default="worker", nullable=False)
    description = Column(Text, nullable=True)
    capabilities = Column(JSON, default=list, nullable=False)
    status = Column(String(50), default="available", nullable=False)
    
    # Placeholders / default scores
    reputation_score = Column(Integer, default=80, nullable=False)
    wallet_balance = Column(Float, default=0.0, nullable=False) # AP Credits
    tasks_completed = Column(Integer, default=0, nullable=False)
    tasks_failed = Column(Integer, default=0, nullable=False)
    success_rate = Column(Float, default=0.0, nullable=False)
    average_verification_score = Column(Float, default=0.0, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    bids = relationship("Bid", back_populates="agent", cascade="all, delete-orphan", foreign_keys="[Bid.agent_id]")
    executions = relationship("TaskExecution", back_populates="agent", cascade="all, delete-orphan",
                              foreign_keys="[TaskExecution.agent_id]")
    submissions = relationship("ResultSubmission", back_populates="agent", foreign_keys="[ResultSubmission.agent_id]")

    def __repr__(self) -> str:
        return f"<Agent id={self.id} agent_code={self.agent_code!r} name={self.name!r}>"


@event.listens_for(Agent, "after_insert")
def assign_agent_code(mapper, connection, target):
    """Auto-generate unique agent_code (AG-1001, AG-1002, ...) after insert."""
    code = f"AG-{1000 + target.id}"
    connection.execute(
        mapper.persist_selectable.update()
        .where(mapper.persist_selectable.c.id == target.id)
        .values(agent_code=code)
    )
    target.agent_code = code
