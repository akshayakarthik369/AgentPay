from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, event
from sqlalchemy.orm import relationship
from database import Base

class Dispute(Base):
    __tablename__ = "disputes"

    id = Column(Integer, primary_key=True, index=True)
    dispute_code = Column(String(50), unique=True, index=True, nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    submission_id = Column(Integer, ForeignKey("result_submissions.id"), nullable=False, index=True)
    verification_id = Column(Integer, ForeignKey("verifications.id"), nullable=False, index=True)
    escrow_id = Column(Integer, ForeignKey("escrows.id"), nullable=False, index=True)
    settlement_id = Column(Integer, ForeignKey("settlements.id"), nullable=True, index=True)
    
    raised_by_type = Column(String(50), default="worker", nullable=False) # worker | requester | client | agent
    raised_by_id = Column(String(50), nullable=True)
    worker_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)

    reason = Column(String(100), nullable=False) # e.g. unfair_verification, rubric_misinterpretation, evidence_ignored, technical_error
    description = Column(Text, nullable=False)
    
    # Statuses: open, evidence_pending, ready_for_arbitration, under_arbitration, resolved, rejected, cancelled
    status = Column(String(50), default="open", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Relationships
    task = relationship("Task")
    submission = relationship("ResultSubmission")
    verification = relationship("Verification")
    escrow = relationship("Escrow")
    settlement = relationship("Settlement")
    worker_agent = relationship("Agent")
    
    evidence_items = relationship("DisputeEvidence", back_populates="dispute", cascade="all, delete-orphan", order_by="DisputeEvidence.id.asc()")
    audit_logs = relationship("DisputeAuditLog", back_populates="dispute", cascade="all, delete-orphan", order_by="DisputeAuditLog.id.asc()")


class DisputeEvidence(Base):
    __tablename__ = "dispute_evidence"

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(Integer, ForeignKey("disputes.id"), nullable=False, index=True)
    submitted_by_type = Column(String(50), nullable=False) # worker | requester | admin
    submitted_by_id = Column(String(50), nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    evidence_data = Column(Text, nullable=True) # JSON or structured text
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    dispute = relationship("Dispute", back_populates="evidence_items")


class DisputeAuditLog(Base):
    __tablename__ = "dispute_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(Integer, ForeignKey("disputes.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False) # dispute_created, evidence_added, status_changed, ready_for_arbitration, dispute_cancelled
    actor_type = Column(String(50), default="system")
    actor_id = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    dispute = relationship("Dispute", back_populates="audit_logs")


def _generate_dispute_code(mapper, connection, target):
    if not target.dispute_code:
        code = f"DP-{1000 + target.id}"
        connection.execute(
            target.__table__.update()
            .where(target.__table__.c.id == target.id)
            .values(dispute_code=code)
        )
        target.dispute_code = code

event.listen(Dispute, "after_insert", _generate_dispute_code)
