from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, ForeignKey, event
from sqlalchemy.orm import relationship
from database import Base


class ReputationEvent(Base):
    """
    SQLAlchemy model for immutable AgentPay reputation audit trail and state events.
    Records every reputation recalculation, delta, and triggering outcome.
    """
    __tablename__ = "reputation_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_code = Column(String(30), unique=True, nullable=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    verification_id = Column(Integer, ForeignKey("verifications.id"), nullable=True, index=True)
    settlement_id = Column(Integer, ForeignKey("settlements.id"), nullable=True, index=True)
    
    # Event types: 'initial_provisional', 'verification_pass', 'verification_fail', 
    # 'review_required', 'successful_settlement', 'task_completed', 'integrity_failure', 'recalculation'
    event_type = Column(String(50), nullable=False, index=True)
    
    previous_score = Column(Float, nullable=False)
    score_delta = Column(Float, nullable=False)
    new_score = Column(Float, nullable=False)
    
    quality_score = Column(Float, nullable=True)
    verification_decision = Column(String(20), nullable=True)
    
    reason = Column(Text, nullable=False)
    details = Column(JSON, default=dict, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    agent = relationship("Agent", back_populates="reputation_events")

    def __repr__(self) -> str:
        return (
            f"<ReputationEvent id={self.id} event_code={self.event_code!r} "
            f"agent_id={self.agent_id} delta={self.score_delta:+.1f} new={self.new_score:.1f}>"
        )


@event.listens_for(ReputationEvent, "after_insert")
def assign_reputation_event_code(mapper, connection, target):
    """Auto-generate sequential unique event_code (RE-1001, RE-1002, ...) after insert."""
    code = f"RE-{1000 + target.id}"
    connection.execute(
        mapper.persist_selectable.update()
        .where(mapper.persist_selectable.c.id == target.id)
        .values(event_code=code)
    )
    target.event_code = code
