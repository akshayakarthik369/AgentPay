from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.wallet import Wallet


def get_or_create_requester_wallet(db: Session, seed_amount: float = 5000.0) -> Wallet:
    """
    Get or create the singleton Client/Requester wallet (seeded with AP Credits).
    """
    wallet = db.query(Wallet).filter(Wallet.owner_type == "requester").first()
    if not wallet:
        wallet = Wallet(
            wallet_code="WL-1000",
            owner_type="requester",
            owner_id=1,
            available_balance=seed_amount,
            locked_balance=0.0,
            total_earned=0.0,
            total_spent=0.0,
            currency="AP",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(wallet)
        db.flush()
        db.refresh(wallet)
    elif (wallet.available_balance + wallet.locked_balance) <= 0.0:
        wallet.available_balance += seed_amount
        wallet.updated_at = datetime.utcnow()
        db.flush()
        db.refresh(wallet)
    return wallet


def get_or_create_agent_wallet(db: Session, agent_id: int) -> Wallet:
    """
    Get or create a dedicated wallet for an agent.
    """
    wallet = db.query(Wallet).filter(
        Wallet.owner_type == "agent",
        Wallet.owner_id == agent_id,
    ).first()

    if not wallet:
        wallet_code = f"WL-{2000 + agent_id}"
        wallet = Wallet(
            wallet_code=wallet_code,
            owner_type="agent",
            owner_id=agent_id,
            available_balance=0.0,
            locked_balance=0.0,
            total_earned=0.0,
            total_spent=0.0,
            currency="AP",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(wallet)
        db.flush()
        db.refresh(wallet)
    return wallet


def get_wallet(db: Session, wallet_id: int) -> Optional[Wallet]:
    """Retrieve wallet by ID."""
    return db.query(Wallet).filter(Wallet.id == wallet_id).first()


def get_wallet_by_code(db: Session, wallet_code: str) -> Optional[Wallet]:
    """Retrieve wallet by code."""
    return db.query(Wallet).filter(Wallet.wallet_code == wallet_code).first()


def lock_balance(db: Session, wallet_id: int, amount: float) -> Wallet:
    """
    Atomically reserve/lock an amount from available balance into locked balance.
    Enforces available_balance >= amount and strictly non-negative balances.
    """
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lock amount must be strictly greater than 0 AP Credits.",
        )

    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).with_for_update().first()
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wallet with id {wallet_id} not found.",
        )

    if not wallet.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wallet is inactive. Cannot reserve balance.",
        )

    if wallet.available_balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient AP Credits to lock task reward. (Required: {amount} AP, Available: {wallet.available_balance} AP).",
        )

    wallet.available_balance -= amount
    wallet.locked_balance += amount
    wallet.updated_at = datetime.utcnow()
    
    # db.flush() instead of commit so this can participate in parent atomic transactions
    db.flush()
    return wallet


def unlock_balance(db: Session, wallet_id: int, amount: float) -> Wallet:
    """
    Unlock previously locked balance back to available balance.
    """
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unlock amount must be strictly greater than 0 AP Credits.",
        )

    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).with_for_update().first()
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wallet with id {wallet_id} not found.",
        )

    if wallet.locked_balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot unlock {amount} AP: only {wallet.locked_balance} AP is currently locked.",
        )

    wallet.locked_balance -= amount
    wallet.available_balance += amount
    wallet.updated_at = datetime.utcnow()

    db.flush()
    return wallet


def settle_transfer(
    db: Session, requester_wallet_id: int, worker_wallet_id: int, amount: float
) -> tuple[Wallet, Wallet]:
    """
    Atomically executes the financial transfer for a settlement:
      - Requester: locked_balance -= amount, total_spent += amount (available_balance unchanged)
      - Worker: available_balance += amount, total_earned += amount
    Enforces amount > 0 and requester.locked_balance >= amount.
    Flushes changes to participate in parent atomic transaction.
    """
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Settlement transfer amount must be strictly greater than 0 AP Credits.",
        )

    requester_wallet = (
        db.query(Wallet).filter(Wallet.id == requester_wallet_id).with_for_update().first()
    )
    if not requester_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Requester wallet with id {requester_wallet_id} not found.",
        )

    worker_wallet = (
        db.query(Wallet).filter(Wallet.id == worker_wallet_id).with_for_update().first()
    )
    if not worker_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker wallet with id {worker_wallet_id} not found.",
        )

    if requester_wallet.locked_balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Insufficient locked balance for settlement. "
                f"Required: {amount} AP, Locked: {requester_wallet.locked_balance} AP."
            ),
        )

    now = datetime.utcnow()

    # Debit requester's locked balance and increase total_spent
    requester_wallet.locked_balance -= amount
    requester_wallet.total_spent += amount
    requester_wallet.updated_at = now

    # Credit worker's available balance and increase total_earned
    worker_wallet.available_balance += amount
    worker_wallet.total_earned += amount
    worker_wallet.updated_at = now

    db.flush()
    return requester_wallet, worker_wallet


def get_wallet_summary(db: Session, wallet_id: int) -> Dict[str, Any]:
    """Retrieve structured summary of a wallet."""
    wallet = get_wallet(db, wallet_id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wallet with id {wallet_id} not found.",
        )

    return {
        "id": wallet.id,
        "wallet_code": wallet.wallet_code,
        "owner_type": wallet.owner_type,
        "owner_id": wallet.owner_id,
        "available_balance": wallet.available_balance,
        "locked_balance": wallet.locked_balance,
        "total_balance": wallet.available_balance + wallet.locked_balance,
        "total_earned": wallet.total_earned,
        "total_spent": wallet.total_spent,
        "currency": wallet.currency,
        "is_active": wallet.is_active,
    }
