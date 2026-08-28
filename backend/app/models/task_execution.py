from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, event
from sqlalchemy.orm import relationship
from database import Base


class TaskExecution(Base):
    """SQLAlchemy model for a single task execution run by an assigned autonomous agent."""
    __tablename__ = "task_executions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    execution_code = Column(String(20), unique=True, nullable=True, index=True)  # EX-1001...

    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    bid_id = Column(Integer, ForeignKey("bids.id"), nullable=False)

    # Lifecycle status
    status = Column(
        String(50), default="pending", nullable=False
    )  # pending | running | completed | submitted | failed | cancelled

    # Frozen input context captured at start time
    input_snapshot = Column(Text, nullable=True)  # JSON string

    # Outputs
    output_text = Column(Text, nullable=True)           # Human-readable result
    structured_output = Column(Text, nullable=True)     # JSON string

    # Progress & retry
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    attempt_number = Column(Integer, default=1, nullable=False)

    # Executor metadata
    execution_metadata = Column(Text, nullable=True)  # JSON string

    # Failure
    error_message = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    task = relationship("Task", back_populates="executions", foreign_keys=[task_id])
    agent = relationship("Agent", back_populates="executions", foreign_keys=[agent_id])
    bid = relationship("Bid", back_populates="execution", foreign_keys=[bid_id])
    logs = relationship("ExecutionLog", back_populates="execution", cascade="all, delete-orphan",
                        order_by="ExecutionLog.created_at")
    submission = relationship("ResultSubmission", back_populates="execution", uselist=False,
                              foreign_keys="[ResultSubmission.execution_id]")

    def __repr__(self) -> str:
        return f"<TaskExecution id={self.id} code={self.execution_code!r} status={self.status!r}>"


@event.listens_for(TaskExecution, "after_insert")
def assign_execution_code(mapper, connection, target):
    """Auto-generate unique execution_code (EX-1001, EX-1002, ...) after insert."""
    code = f"EX-{1000 + target.id}"
    connection.execute(
        mapper.persist_selectable.update()
        .where(mapper.persist_selectable.c.id == target.id)
        .values(execution_code=code)
    )
    target.execution_code = code


class ExecutionLog(Base):
    """Ordered log entries for a task execution."""
    __tablename__ = "execution_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    execution_id = Column(Integer, ForeignKey("task_executions.id"), nullable=False, index=True)
    level = Column(String(20), default="info", nullable=False)  # info | warning | error
    step = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    execution = relationship("TaskExecution", back_populates="logs")

    def __repr__(self) -> str:
        return f"<ExecutionLog id={self.id} execution_id={self.execution_id} level={self.level!r}>"
