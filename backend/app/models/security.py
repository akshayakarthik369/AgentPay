from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, event
from sqlalchemy.orm import relationship
from database import Base


class SecurityEvent(Base):
    """
    SQLAlchemy model for AgentPay immutable security audit events and malicious-behavior records.
    """
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_code = Column(String(30), unique=True, nullable=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)

    # Event types:
    # integrity_failure, duplicate_action, invalid_settlement, unauthorized_action,
    # conflict_of_interest, repeated_failure, suspicious_bidding, agent_suspended, agent_restored
    event_type = Column(String(50), nullable=False, index=True)

    # Severity: 'low', 'medium', 'high', 'critical'
    severity = Column(String(20), default="low", nullable=False, index=True)

    reason = Column(Text, nullable=False)
    details = Column(JSON, default=dict, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    agent = relationship("Agent", foreign_keys=[agent_id])
    task = relationship("Task", foreign_keys=[task_id])

    def __repr__(self) -> str:
        return (
            f"<SecurityEvent id={self.id} event_code={self.event_code!r} "
            f"type={self.event_type!r} severity={self.severity!r} agent_id={self.agent_id}>"
        )


@event.listens_for(SecurityEvent, "after_insert")
def assign_security_event_code(mapper, connection, target):
    """Auto-generate unique sequential event_code (SEC-1001, SEC-1002, ...) after insert."""
    code = f"SEC-{1000 + target.id}"
    connection.execute(
        mapper.persist_selectable.update()
        .where(mapper.persist_selectable.c.id == target.id)
        .values(event_code=code)
    )
    target.event_code = code
