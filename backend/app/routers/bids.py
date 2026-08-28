from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db

from app.schemas.bid import (
    BidCreate,
    BidUpdate,
    BidResponse,
    TaskBidsListResponse,
    AgentBidsListResponse,
    SelectBidResponse,
)
from app.services.bidding_service import (
    create_bid,
    get_bids_for_task,
    get_bids_for_agent,
    get_bid_by_id,
    update_bid,
    withdraw_bid,
    select_winning_bid,
)

router = APIRouter(prefix="/api", tags=["Bidding"])


@router.post(
    "/bids",
    response_model=BidResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new bid on a task",
)
def post_bid(payload: BidCreate, db: Session = Depends(get_db)):
    """
    Submit an agent bid for an open/bidding task.
    Enforces suitability match score >= 60%, valid budget, and available status.
    Automatically moves task status to 'bidding' on first bid.
    """
    bid = create_bid(db, payload)
    return bid


@router.get(
    "/tasks/{task_id}/bids",
    response_model=TaskBidsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all ranked bids for a specific task",
)
def list_task_bids(
    task_id: int,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (pending, accepted, rejected, withdrawn)"),
    db: Session = Depends(get_db),
):
    """
    Retrieve all submitted bids for a task, ranked descending by multi-factor selection score.
    """
    res = get_bids_for_task(db, task_id, status_filter=status_filter)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )
    return res


@router.get(
    "/agents/{agent_id}/bids",
    response_model=AgentBidsListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all bids submitted by a specific agent",
)
def list_agent_bids(
    agent_id: int,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (pending, accepted, rejected, withdrawn)"),
    db: Session = Depends(get_db),
):
    """
    Retrieve bid history for a specific agent.
    """
    res = get_bids_for_agent(db, agent_id, status_filter=status_filter)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {agent_id} not found",
        )
    return res


@router.get(
    "/bids/{bid_id}",
    response_model=BidResponse,
    status_code=status.HTTP_200_OK,
    summary="Get details of a single bid",
)
def get_bid(bid_id: int, db: Session = Depends(get_db)):
    """
    Fetch a single bid by ID.
    """
    bid = get_bid_by_id(db, bid_id)
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid with id {bid_id} not found",
        )
    return bid


@router.patch(
    "/bids/{bid_id}",
    response_model=BidResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a pending bid",
)
def patch_bid(bid_id: int, payload: BidUpdate, db: Session = Depends(get_db)):
    """
    Update bid amount, completion estimate, or proposal.
    Allowed only while bid is pending. Recalculates selection score.
    """
    bid = update_bid(db, bid_id, payload)
    return bid


@router.post(
    "/bids/{bid_id}/withdraw",
    response_model=BidResponse,
    status_code=status.HTTP_200_OK,
    summary="Withdraw a pending bid",
)
def withdraw_agent_bid(bid_id: int, db: Session = Depends(get_db)):
    """
    Withdraw a pending bid from consideration.
    """
    bid = withdraw_bid(db, bid_id)
    return bid


@router.post(
    "/tasks/{task_id}/select-bid/{bid_id}",
    response_model=SelectBidResponse,
    status_code=status.HTTP_200_OK,
    summary="Select winning agent and assign task",
)
def select_winner(
    task_id: int,
    bid_id: int,
    db: Session = Depends(get_db),
):
    """
    Atomically select winning bid:
    - Sets Task to 'assigned' with assigned_agent_id and selected_bid_id
    - Sets winning Bid to 'accepted'
    - Rejects other competing pending bids
    - Sets winning Agent to 'busy'
    """
    return select_winning_bid(db, task_id, bid_id)
