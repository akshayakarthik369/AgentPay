from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True)
    settlement_code = Column(String(30), unique=True, index=True, nullable=False)  # e.g. "ST-1001"
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    escrow_id = Column(Integer, ForeignKey("escrows.id"), unique=True, nullable=False, index=True)
    verification_id = Column(Integer, ForeignKey("verifications.id"), nullable=True)
    requester_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    worker_wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    worker_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="AP", nullable=False)
    
    # Statuses: "pending", "processing", "completed", "failed", "blocked"
    status = Column(String(30), default="pending", nullable=False)
    
    # Trigger: "automatic", "manual"
    trigger_type = Column(String(30), default="automatic", nullable=False)
    
    verification_decision = Column(String(20), nullable=True)
    integrity_verified = Column(Boolean, default=True, nullable=False)
    failure_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    audit_logs = relationship("SettlementAuditLog", back_populates="settlement", cascade="all, delete-orphan")
    ledger_entries = relationship("LedgerEntry", back_populates="settlement", cascade="all, delete-orphan")


class SettlementAuditLog(Base):
    __tablename__ = "settlement_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    settlement_id = Column(Integer, ForeignKey("settlements.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False)
    actor_type = Column(String(30), nullable=False)  # "system", "verifier", "requester", "agent"
    actor_id = Column(String(50), nullable=True)
    amount = Column(Float, nullable=True)
    previous_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    settlement = relationship("Settlement", back_populates="audit_logs")


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    entry_code = Column(String(30), unique=True, index=True, nullable=False)  # e.g. "LE-1001"
    settlement_id = Column(Integer, ForeignKey("settlements.id"), nullable=True, index=True)
    escrow_id = Column(Integer, ForeignKey("escrows.id"), nullable=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False, index=True)
    
    # Entry types: "escrow_lock", "settlement_debit", "settlement_credit"
    entry_type = Column(String(30), nullable=False)
    amount = Column(Float, nullable=False)
    balance_type = Column(String(30), nullable=False)  # "locked", "available"
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    settlement = relationship("Settlement", back_populates="ledger_entries")
