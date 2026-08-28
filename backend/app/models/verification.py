"""
Phase 10 — Verification and VerificationAuditLog models.

Verification:
  Immutable verification record produced by an independent verifier agent.
  Enforces verifier independence, evaluates frozen snapshots, scores 5 criteria,
  and issues a deterministic PASS / FAIL / REVIEW decision.

VerificationAuditLog:
  Chronological audit trail of all verification actions.
"""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text,
    DateTime, ForeignKey, UniqueConstraint, event
)
from sqlalchemy.orm import relationship
from database import Base


def _generate_verification_code(mapper, connection, target):
    """Auto-generate VR-NNNN code after insert."""
    if not target.verification_code:
        code = f"VR-{1000 + target.id}"
        connection.execute(
            target.__table__.update()
            .where(target.__table__.c.id == target.id)
            .values(verification_code=code)
        )
        target.verification_code = code


class Verification(Base):
    __tablename__ = "verifications"

    # ── Identity ──────────────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)
    verification_code = Column(String(20), unique=True, index=True, nullable=True)

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    submission_id = Column(Integer, ForeignKey("result_submissions.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    worker_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    verifier_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)

    # ── Lifecycle & Decision ──────────────────────────────────────────────────
    # pending | running | passed | failed | review_required | error
    status = Column(String(50), default="pending", nullable=False)
    # PASS | FAIL | REVIEW
    decision = Column(String(20), nullable=True)

    # ── Integrity Check Result ────────────────────────────────────────────────
    integrity_valid = Column(Boolean, default=True, nullable=False)

    # ── 5 Criteria Scores (0.00 – 100.00) ─────────────────────────────────────
    accuracy_score = Column(Float, default=0.0, nullable=False)
    completeness_score = Column(Float, default=0.0, nullable=False)
    format_compliance_score = Column(Float, default=0.0, nullable=False)
    quality_score = Column(Float, default=0.0, nullable=False)
    evidence_score = Column(Float, default=0.0, nullable=False)

    # ── Overall & Requirement ─────────────────────────────────────────────────
    overall_score = Column(Float, default=0.0, nullable=False)
    required_score = Column(Float, default=0.0, nullable=False)

    # ── Explainability & Warnings ─────────────────────────────────────────────
    reasons = Column(Text, nullable=True)               # JSON dict of reasons per criterion
    warnings = Column(Text, nullable=True)              # JSON list of warning strings
    verification_details = Column(Text, nullable=True)  # JSON dict of itemized checks

    # ── Frozen Snapshots at Verification Time ──────────────────────────────────
    verifier_snapshot = Column(Text, nullable=True)     # JSON dict of verifier agent state
    submission_hash_snapshot = Column(String, nullable=True)  # sha256:... from ResultSubmission

    # ── Timestamps ────────────────────────────────────────────────────────────
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    submission = relationship("ResultSubmission", back_populates="verification", foreign_keys=[submission_id])
    task = relationship("Task", back_populates="verifications", foreign_keys=[task_id])
    worker_agent = relationship("Agent", foreign_keys=[worker_agent_id])
    verifier_agent = relationship("Agent", foreign_keys=[verifier_agent_id])
    audit_logs = relationship(
        "VerificationAuditLog",
        back_populates="verification",
        order_by="VerificationAuditLog.created_at",
        cascade="all, delete-orphan",
    )

    # ── Unique Constraint: 1 active verification per submission ───────────────
    __table_args__ = (
        UniqueConstraint("submission_id", name="uq_verification_submission"),
    )

    def __repr__(self) -> str:
        return f"<Verification id={self.id} code={self.verification_code!r} decision={self.decision!r}>"


event.listen(Verification, "after_insert", _generate_verification_code)


class VerificationAuditLog(Base):
    __tablename__ = "verification_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    verification_id = Column(
        Integer, ForeignKey("verifications.id"), nullable=False, index=True
    )
    action = Column(String(100), nullable=False)         # e.g. "verifier_selected"
    actor_type = Column(String(50), default="system")    # system | verifier_agent
    actor_id = Column(String(50), nullable=True)         # agent code or "system"
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    verification = relationship("Verification", back_populates="audit_logs")
