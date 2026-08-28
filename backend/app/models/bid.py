from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, event
from sqlalchemy.orm import relationship
from database import Base

class Bid(Base):
    """SQLAlchemy model for autonomous agent bids on tasks."""
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bid_code = Column(String(20), unique=True, nullable=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    
    bid_amount = Column(Float, nullable=False) # AP Credits
    estimated_completion_minutes = Column(Integer, nullable=False)
    proposal = Column(Text, nullable=False)
    
    match_score_snapshot = Column(Float, nullable=False)
    reputation_snapshot = Column(Integer, nullable=False)
    selection_score = Column(Float, default=0.0, nullable=False)
    
    status = Column(String(50), default="pending", nullable=False) # pending, accepted, rejected, withdrawn
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    withdrawn_at = Column(DateTime, nullable=True)

    task = relationship("Task", back_populates="bids", foreign_keys=[task_id])
    agent = relationship("Agent", back_populates="bids", foreign_keys=[agent_id])
    execution = relationship("TaskExecution", back_populates="bid", uselist=False, foreign_keys="[TaskExecution.bid_id]")
    submission = relationship("ResultSubmission", back_populates="bid", uselist=False, foreign_keys="[ResultSubmission.bid_id]")


    def __repr__(self) -> str:
        return f"<Bid id={self.id} bid_code={self.bid_code!r} task_id={self.task_id} agent_id={self.agent_id} status={self.status!r}>"


@event.listens_for(Bid, "after_insert")
def assign_bid_code(mapper, connection, target):
    """Auto-generate unique bid_code (BD-1001, BD-1002, ...) after insert."""
    code = f"BD-{1000 + target.id}"
    connection.execute(
        mapper.persist_selectable.update()
        .where(mapper.persist_selectable.c.id == target.id)
        .values(bid_code=code)
    )
    target.bid_code = code
