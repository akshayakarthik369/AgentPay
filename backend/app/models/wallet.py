from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    wallet_code = Column(String(30), unique=True, index=True, nullable=False)  # e.g. "WL-1001"
    owner_type = Column(String(30), nullable=False)  # "requester", "agent", "system"
    owner_id = Column(Integer, nullable=True, index=True)  # agent_id for agents, or 1 for requester
    available_balance = Column(Float, default=0.0, nullable=False)
    locked_balance = Column(Float, default=0.0, nullable=False)
    total_earned = Column(Float, default=0.0, nullable=False)
    total_spent = Column(Float, default=0.0, nullable=False)
    currency = Column(String(10), default="AP", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
