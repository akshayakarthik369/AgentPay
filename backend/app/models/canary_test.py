"""
app/models/canary_test.py — CanaryTest SQLAlchemy model for Phase 21.

Records each canary test attempt for a new agent.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, event
from sqlalchemy.orm import relationship
from database import Base


class CanaryTest(Base):
    """
    Canary test record. Each attempt by an agent to pass the entry-level
    controlled evaluation before being granted provisional access.
    """
    __tablename__ = "canary_tests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    canary_code = Column(String(20), unique=True, nullable=True, index=True)  # CT-1001+

    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)

    # Test configuration
    test_type = Column(String(50), nullable=False)          # e.g. "nlp_classification", "code_reasoning"
    required_capability = Column(String(100), nullable=False)

    # Attempt tracking
    attempt_number = Column(Integer, default=1, nullable=False)

    # Lifecycle: pending → running → passed | failed
    status = Column(String(30), default="pending", nullable=False, index=True)

    # Scoring (0–100)
    score = Column(Float, nullable=True)
    required_score = Column(Float, default=80.0, nullable=False)

    # Sub-checks (each True/False)
    integrity_passed = Column(Boolean, nullable=True)
    policy_passed = Column(Boolean, nullable=True)
    execution_passed = Column(Boolean, nullable=True)

    # Result details
    result_summary = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    agent = relationship("Agent", foreign_keys=[agent_id])

    def __repr__(self) -> str:
        return (
            f"<CanaryTest id={self.id} canary_code={self.canary_code!r} "
            f"agent_id={self.agent_id} status={self.status!r} score={self.score}>"
        )


@event.listens_for(CanaryTest, "after_insert")
def assign_canary_code(mapper, connection, target):
    """Auto-generate unique canary_code (CT-1001, CT-1002, ...) after insert."""
    code = f"CT-{1000 + target.id}"
    connection.execute(
        mapper.persist_selectable.update()
        .where(mapper.persist_selectable.c.id == target.id)
        .values(canary_code=code)
    )
    target.canary_code = code
