"""
Phase 9 — ResultSubmission and SubmissionAuditLog models.

ResultSubmission:
  Immutable package created when a completed execution is submitted.
  Freezes task/agent/bid/execution snapshots, generates SHA-256 integrity hash.

SubmissionAuditLog:
  Append-only event trail for every action taken on a submission.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Text,
    DateTime, ForeignKey, UniqueConstraint, event
)
from sqlalchemy.orm import relationship
from database import Base


def _generate_submission_code(mapper, connection, target):
    """Auto-generate RS-NNNN code after insert."""
    if not target.submission_code:
        connection.execute(
            target.__table__.update()
            .where(target.__table__.c.id == target.id)
            .values(submission_code=f"RS-{1000 + target.id}")
        )
        target.submission_code = f"RS-{1000 + target.id}"


class ResultSubmission(Base):
    __tablename__ = "result_submissions"

    # ── Identity ──────────────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True, index=True)
    submission_code = Column(String, unique=True, index=True, nullable=True)
    version = Column(Integer, default=1, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    execution_id = Column(Integer, ForeignKey("task_executions.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    bid_id = Column(Integer, ForeignKey("bids.id"), nullable=False, index=True)

    # ── Status ────────────────────────────────────────────────────────────────
    # draft → submitted → locked
    status = Column(String, default="submitted", nullable=False)
    is_locked = Column(Boolean, default=True, nullable=False)

    # ── Core output (immutable after locking) ─────────────────────────────────
    output_text = Column(Text, nullable=True)
    structured_output = Column(Text, nullable=True)   # JSON string
    result_summary = Column(Text, nullable=True)
    content_type = Column(String, default="text/plain", nullable=True)

    # ── Evidence & provenance ─────────────────────────────────────────────────
    evidence = Column(Text, nullable=True)            # JSON string
    provenance = Column(Text, nullable=True)          # JSON string

    # ── Frozen snapshots ──────────────────────────────────────────────────────
    task_snapshot = Column(Text, nullable=True)       # JSON string
    agent_snapshot = Column(Text, nullable=True)      # JSON string
    bid_snapshot = Column(Text, nullable=True)        # JSON string
    execution_snapshot = Column(Text, nullable=True)  # JSON string

    # ── Metadata ──────────────────────────────────────────────────────────────
    submission_metadata = Column(Text, nullable=True) # JSON string
    self_assessment = Column(Text, nullable=True)     # JSON string
    limitations = Column(Text, nullable=True)         # JSON array string
    confidence_score = Column(Integer, default=None, nullable=True)  # 0–100

    # ── Integrity ─────────────────────────────────────────────────────────────
    integrity_hash = Column(String, nullable=True)    # sha256:...

    # ── Timestamps ────────────────────────────────────────────────────────────
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────────
    task = relationship("Task", back_populates="submission", foreign_keys=[task_id])
    execution = relationship("TaskExecution", back_populates="submission", foreign_keys=[execution_id])
    agent = relationship("Agent", back_populates="submissions", foreign_keys=[agent_id])
    bid = relationship("Bid", back_populates="submission", foreign_keys=[bid_id])
    verification = relationship("Verification", back_populates="submission", uselist=False,
                                foreign_keys="[Verification.submission_id]")
    audit_logs = relationship(
        "SubmissionAuditLog",
        back_populates="submission",
        order_by="SubmissionAuditLog.created_at",
        cascade="all, delete-orphan",
    )

    # ── Unique constraint: one active submission per execution ─────────────────
    __table_args__ = (
        UniqueConstraint("execution_id", name="uq_submission_execution"),
    )

    # ── Computed property ─────────────────────────────────────────────────────
    @property
    def verification_ready(self) -> bool:
        """True only when the submission is fully locked and complete."""
        return bool(
            self.is_locked
            and self.integrity_hash
            and self.task_snapshot
            and self.agent_snapshot
            and self.output_text
            and self.status in ("submitted", "locked")
        )


# Auto-assign RS-code after first insert
event.listen(ResultSubmission, "after_insert", _generate_submission_code)


class SubmissionAuditLog(Base):
    __tablename__ = "submission_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer, ForeignKey("result_submissions.id"), nullable=False, index=True
    )
    action = Column(String, nullable=False)          # e.g. "submission_created"
    actor_type = Column(String, default="system")    # system | worker_agent | future_verifier
    actor_id = Column(String, nullable=True)         # agent code or "system"
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    submission = relationship("ResultSubmission", back_populates="audit_logs")
