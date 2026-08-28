"""
Phase 11 — Wallet API Router.
Endpoints for retrieving AP Credit wallet data.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from app.models.wallet import Wallet
from app.services import wallet_service

router = APIRouter(prefix="/api", tags=["Wallets"])


@router.get("/wallets/{wallet_id}")
def get_wallet(wallet_id: int, db: Session = Depends(get_db)):
    """Retrieve wallet by ID."""
    wallet = wallet_service.get_wallet(db, wallet_id)
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wallet with id {wallet_id} not found.",
        )
    return wallet_service.get_wallet_summary(db, wallet_id)


@router.get("/agents/{agent_id}/wallet")
def get_agent_wallet(agent_id: int, db: Session = Depends(get_db)):
    """Get or create wallet for a specific agent."""
    wallet = wallet_service.get_or_create_agent_wallet(db, agent_id)
    return wallet_service.get_wallet_summary(db, wallet.id)


@router.get("/client/wallet")
def get_client_wallet(db: Session = Depends(get_db)):
    """Get or create the requester/client wallet, seeded with 5000 AP Credits."""
    wallet = wallet_service.get_or_create_requester_wallet(db, seed_amount=5000.0)
    return wallet_service.get_wallet_summary(db, wallet.id)
