from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, event
from sqlalchemy.orm import relationship
from database import Base

class Arbitration(Base):
    __tablename__ = "arbitrations"

    id = Column(Integer, primary_key=True, index=True)
    arbitration_code = Column(String(50), unique=True, index=True, nullable=True)
    dispute_id = Column(Integer, ForeignKey("disputes.id"), nullable=False, unique=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    arbitrator_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    worker_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    verification_id = Column(Integer, ForeignKey("verifications.id"), nullable=True)
    review_id = Column(Integer, ForeignKey("human_reviews.id"), nullable=True)
    escrow_id = Column(Integer, ForeignKey("escrows.id"), nullable=False)

    # Statuses: pending, running, resolved, failed
    status = Column(String(50), default="pending", nullable=False)
    # Decisions: worker_wins, requester_wins, inconclusive
    decision = Column(String(50), nullable=True)

    confidence_score = Column(Float, default=0.0, nullable=False)
    reasoning_summary = Column(Text, nullable=True)
    analysis_details = Column(Text, nullable=True) # JSON string of itemized criteria evaluations

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    dispute = relationship("Dispute")
    task = relationship("Task")
    arbitrator_agent = relationship("Agent", foreign_keys=[arbitrator_agent_id])
    worker_agent = relationship("Agent", foreign_keys=[worker_agent_id])
    verification = relationship("Verification")
    review = relationship("HumanReview")
    escrow = relationship("Escrow")

    audit_logs = relationship("ArbitrationAuditLog", back_populates="arbitration", cascade="all, delete-orphan", order_by="ArbitrationAuditLog.id.asc()")


class ArbitrationAuditLog(Base):
    __tablename__ = "arbitration_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    arbitration_id = Column(Integer, ForeignKey("arbitrations.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    # arbitration_created, arbitrator_selected, arbitration_started, evidence_reviewed, decision_made, escrow_updated, settlement_triggered, settlement_blocked, reputation_updated
    actor_type = Column(String(50), default="system")
    actor_id = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    arbitration = relationship("Arbitration", back_populates="audit_logs")


def _generate_arbitration_code(mapper, connection, target):
    if not target.arbitration_code:
        code = f"AR-{1000 + target.id}"
        connection.execute(
            target.__table__.update()
            .where(target.__table__.c.id == target.id)
            .values(arbitration_code=code)
        )
        target.arbitration_code = code

event.listen(Arbitration, "after_insert", _generate_arbitration_code)
