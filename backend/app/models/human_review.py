from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, event
from sqlalchemy.orm import relationship
from database import Base

class HumanReview(Base):
    __tablename__ = "human_reviews"

    id = Column(Integer, primary_key=True, index=True)
    review_code = Column(String(50), unique=True, index=True, nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    submission_id = Column(Integer, ForeignKey("result_submissions.id"), nullable=False, index=True)
    verification_id = Column(Integer, ForeignKey("verifications.id"), nullable=False, index=True)
    worker_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    
    # pending, in_review, approved, rejected, resolved
    status = Column(String(50), default="pending", nullable=False)
    # APPROVE, REJECT
    decision = Column(String(50), nullable=True)
    reviewer_note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    task = relationship("Task")
    submission = relationship("ResultSubmission")
    verification = relationship("Verification")
    worker_agent = relationship("Agent")
    audit_logs = relationship("HumanReviewAuditLog", back_populates="review", cascade="all, delete-orphan")

class HumanReviewAuditLog(Base):
    __tablename__ = "human_review_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("human_reviews.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)  # review_created, review_started, review_approved, etc.
    actor_type = Column(String(50), default="system")  # system | human_reviewer
    actor_id = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    review = relationship("HumanReview", back_populates="audit_logs")

def _generate_human_review_code(mapper, connection, target):
    if not target.review_code:
        code = f"HR-{1000 + target.id}"
        connection.execute(
            target.__table__.update()
            .where(target.__table__.c.id == target.id)
            .values(review_code=code)
        )
        target.review_code = code

event.listen(HumanReview, "after_insert", _generate_human_review_code)
