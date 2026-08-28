from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class Escrow(Base):
    __tablename__ = "escrows"

    id = Column(Integer, primary_key=True, index=True)
    escrow_code = Column(String(30), unique=True, index=True, nullable=False)  # e.g. "ES-1001"
    task_id = Column(Integer, ForeignKey("tasks.id"), unique=True, nullable=False, index=True)
    requester_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    worker_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    worker_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    verification_id = Column(Integer, ForeignKey("verifications.id"), nullable=True)
    reward_amount = Column(Float, nullable=False)
    
    # Statuses: "pending", "locked", "awaiting_verification", "releasable", "blocked", "released", "refunded", "cancelled"
    status = Column(String(30), default="locked", nullable=False)
    
    locked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    releasable_at = Column(DateTime, nullable=True)
    released_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    audit_logs = relationship("EscrowAuditLog", back_populates="escrow", cascade="all, delete-orphan")


class EscrowAuditLog(Base):
    __tablename__ = "escrow_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    escrow_id = Column(Integer, ForeignKey("escrows.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    actor_type = Column(String(30), nullable=False)  # "requester", "system", "agent", "verifier"
    actor_id = Column(String(50), nullable=True)
    message = Column(Text, nullable=False)
    amount = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    escrow = relationship("Escrow", back_populates="audit_logs")
