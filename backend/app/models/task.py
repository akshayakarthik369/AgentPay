from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, event
from sqlalchemy.orm import relationship
from database import Base


class Task(Base):
    """SQLAlchemy model for AgentPay tasks."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_code = Column(String(20), unique=True, nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    required_capability = Column(String(255), nullable=False)
    reward = Column(Float, nullable=False)
    deadline = Column(DateTime, nullable=False)
    minimum_reputation = Column(Integer, default=0, nullable=False)
    minimum_quality_score = Column(Integer, default=0, nullable=False)
    status = Column(String(50), default="open", nullable=False)
    
    # Phase 7 Assignment fields
    assigned_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    selected_bid_id = Column(Integer, ForeignKey("bids.id"), nullable=True)
    assigned_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    bids = relationship("Bid", back_populates="task", cascade="all, delete-orphan", foreign_keys="[Bid.task_id]")
    assigned_agent = relationship("Agent", foreign_keys=[assigned_agent_id])
    selected_bid = relationship("Bid", foreign_keys=[selected_bid_id])
    executions = relationship("TaskExecution", back_populates="task", cascade="all, delete-orphan",
                              foreign_keys="[TaskExecution.task_id]")
    submission = relationship("ResultSubmission", back_populates="task", uselist=False,
                              foreign_keys="[ResultSubmission.task_id]")
    verifications = relationship("Verification", back_populates="task", cascade="all, delete-orphan",
                                 foreign_keys="[Verification.task_id]")


    def __repr__(self) -> str:
        return f"<Task id={self.id} task_code={self.task_code!r} title={self.title!r} status={self.status!r}>"



@event.listens_for(Task, "after_insert")
def assign_task_code(mapper, connection, target):
    """
    Auto-generate a human-readable task_code (AP-1001, AP-1002, ...)
    immediately after a new Task row is inserted, before the session commits.
    """
    code = f"AP-{1000 + target.id}"
    connection.execute(
        mapper.persist_selectable.update()
        .where(mapper.persist_selectable.c.id == target.id)
        .values(task_code=code)
    )
    # Reflect the generated code back onto the in-memory object so callers
    # see the correct value without needing an extra refresh.
    target.task_code = code
