"""
Bidding & Agent Selection Service for AgentPay.
Manages bid creation, validation gates, ranking, updates, withdrawals, and transactional winner selection.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.bid import Bid
from app.models.task import Task
from app.models.agent import Agent
from app.schemas.bid import BidCreate, BidUpdate
from app.config.bidding import (
    MIN_BID_MATCH_SCORE,
    calculate_price_score,
    calculate_speed_score,
    calculate_bid_selection_score,
)
from app.services.matching_service import score_agent_task_pair, _is_task_expired
from app.services import escrow_service


def _generate_bid_explainability_reasons(
    match_score: float,
    reputation: int,
    price_score: float,
    speed_score: float,
    bid_amount: float,
    task_reward: float,
    estimated_minutes: int,
    agent_status: str,
) -> List[str]:
    """Generate human-readable explainability bullet points for a bid."""
    reasons = []

    # Match reason
    if match_score >= 90:
        reasons.append(f"Outstanding {match_score:.1f}% agent-task capability match")
    elif match_score >= 75:
        reasons.append(f"Strong {match_score:.1f}% agent-task capability match")
    else:
        reasons.append(f"Acceptable {match_score:.1f}% capability match")

    # Reputation
    if reputation >= 90:
        reasons.append(f"Top-tier reputation score ({reputation}/100)")
    elif reputation >= 80:
        reasons.append(f"Solid reputation score ({reputation}/100)")
    else:
        reasons.append(f"Reputation score is {reputation}/100")

    # Price competitiveness
    discount_pct = round(((task_reward - bid_amount) / task_reward) * 100) if task_reward > 0 else 0
    if discount_pct > 0:
        reasons.append(f"Competitive bid: {discount_pct}% below task budget ({bid_amount:.1f} / {task_reward:.1f} AP)")
    else:
        reasons.append(f"Bid is at full task reward ({bid_amount:.1f} AP)")

    # Completion speed
    if estimated_minutes <= 30:
        reasons.append(f"Rapid turnaround estimate ({estimated_minutes} mins)")
    elif estimated_minutes <= 60:
        reasons.append(f"Standard completion estimate ({estimated_minutes} mins)")
    else:
        reasons.append(f"Extended completion estimate ({estimated_minutes} mins)")

    return reasons


def create_bid(db: Session, payload: BidCreate) -> Bid:
    """
    Submit an agent bid on a task with comprehensive integrity and eligibility checks.
    """
    # 1. Task Existence & Status Check
    task = db.query(Task).filter(Task.id == payload.task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {payload.task_id} not found",
        )

    if task.status not in ("open", "bidding"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot bid on task with status '{task.status}'. Task must be 'open' or 'bidding'.",
        )

    if _is_task_expired(task):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot bid on task: deadline has expired.",
        )

    # 2. Agent Existence & Status Check
    agent = db.query(Agent).filter(Agent.id == payload.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {payload.agent_id} not found",
        )

    if not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent '{agent.name}' is currently inactive / disabled.",
        )

    if agent.status != "available":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent '{agent.name}' cannot bid while in '{agent.status}' status. Must be 'available'.",
        )

    # 3. Bid Amount Validation
    if payload.bid_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Bid amount must be greater than 0 AP Credits.",
        )

    if payload.bid_amount > task.reward:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bid amount ({payload.bid_amount} AP) cannot exceed task reward ({task.reward} AP).",
        )

    # 4. Duplicate Pending Bid Prevention
    existing_bid = db.query(Bid).filter(
        Bid.task_id == payload.task_id,
        Bid.agent_id == payload.agent_id,
        Bid.status == "pending",
    ).first()

    if existing_bid:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Agent '{agent.name}' already has a pending bid ({existing_bid.bid_code}) on this task. Update or withdraw existing bid.",
        )

    # 5. Suitability Match Evaluation & Gate
    match_data = score_agent_task_pair(agent, task)
    match_score = match_data["overall_score"]

    if match_score < MIN_BID_MATCH_SCORE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent '{agent.name}' suitability score ({match_score}%) is below minimum bidding threshold ({MIN_BID_MATCH_SCORE}%).",
        )

    # 6. Calculate Selection Score
    selection_score = calculate_bid_selection_score(
        match_score=match_score,
        reputation=float(agent.reputation_score or 80),
        bid_amount=payload.bid_amount,
        task_reward=task.reward,
        estimated_minutes=payload.estimated_completion_minutes,
    )

    # 7. Create Bid Record
    bid = Bid(
        task_id=payload.task_id,
        agent_id=payload.agent_id,
        bid_amount=payload.bid_amount,
        estimated_completion_minutes=payload.estimated_completion_minutes,
        proposal=payload.proposal,
        match_score_snapshot=match_score,
        reputation_snapshot=agent.reputation_score or 80,
        selection_score=selection_score,
        status="pending",
    )

    db.add(bid)

    # 8. Transition task status to 'bidding' if it was 'open'
    if task.status == "open":
        task.status = "bidding"

    db.commit()
    db.refresh(bid)
    return bid


def get_bids_for_task(db: Session, task_id: int, status_filter: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve all bids for a task, ranked descending by selection_score.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return None

    query = db.query(Bid).filter(Bid.task_id == task_id)
    if status_filter:
        query = query.filter(Bid.status == status_filter.lower())

    bids = query.all()

    ranked_items = []
    for b in bids:
        agent = b.agent or db.query(Agent).filter(Agent.id == b.agent_id).first()
        price_score = calculate_price_score(b.bid_amount, task.reward)
        speed_score = calculate_speed_score(b.estimated_completion_minutes)

        reasons = _generate_bid_explainability_reasons(
            match_score=b.match_score_snapshot,
            reputation=b.reputation_snapshot,
            price_score=price_score,
            speed_score=speed_score,
            bid_amount=b.bid_amount,
            task_reward=task.reward,
            estimated_minutes=b.estimated_completion_minutes,
            agent_status=agent.status if agent else "available",
        )

        ranked_items.append({
            "id": b.id,
            "bid_code": b.bid_code,
            "task_id": b.task_id,
            "agent_id": b.agent_id,
            "bid_amount": b.bid_amount,
            "estimated_completion_minutes": b.estimated_completion_minutes,
            "proposal": b.proposal,
            "match_score": b.match_score_snapshot,
            "price_score": price_score,
            "speed_score": speed_score,
            "selection_score": b.selection_score,
            "status": b.status,
            "created_at": b.created_at,
            "updated_at": b.updated_at,
            "reasons": reasons,
            "agent": {
                "id": agent.id if agent else b.agent_id,
                "agent_code": agent.agent_code if agent else f"AG-{b.agent_id}",
                "name": agent.name if agent else "Unknown Agent",
                "agent_type": agent.agent_type if agent else "worker",
                "reputation_score": agent.reputation_score if agent else b.reputation_snapshot,
                "status": agent.status if agent else "available",
            }
        })

    # Sort descending by selection_score, then created_at
    ranked_items.sort(key=lambda x: (x["selection_score"], x["created_at"]), reverse=True)

    return {
        "task_id": task.id,
        "task_code": task.task_code,
        "task_status": task.status,
        "reward": task.reward,
        "bids": ranked_items,
        "total_bids": len(ranked_items),
    }


def get_bids_for_agent(db: Session, agent_id: int, status_filter: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve bid history for a specific agent.
    """
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        return None

    query = db.query(Bid).filter(Bid.agent_id == agent_id)
    if status_filter:
        query = query.filter(Bid.status == status_filter.lower())

    bids = query.order_by(Bid.created_at.desc()).all()

    items = []
    for b in bids:
        task = b.task or db.query(Task).filter(Task.id == b.task_id).first()
        items.append({
            "id": b.id,
            "bid_code": b.bid_code,
            "task_id": b.task_id,
            "agent_id": b.agent_id,
            "bid_amount": b.bid_amount,
            "estimated_completion_minutes": b.estimated_completion_minutes,
            "proposal": b.proposal,
            "match_score_snapshot": b.match_score_snapshot,
            "reputation_snapshot": b.reputation_snapshot,
            "selection_score": b.selection_score,
            "status": b.status,
            "created_at": b.created_at,
            "updated_at": b.updated_at,
            "accepted_at": b.accepted_at,
            "rejected_at": b.rejected_at,
            "withdrawn_at": b.withdrawn_at,
            "task": {
                "id": task.id if task else b.task_id,
                "task_code": task.task_code if task else f"AP-{b.task_id}",
                "title": task.title if task else "Task",
                "category": task.category if task else "General",
                "required_capability": task.required_capability if task else "General",
                "reward": task.reward if task else 0.0,
                "status": task.status if task else "open",
            } if task else None,
            "agent": {
                "id": agent.id,
                "agent_code": agent.agent_code,
                "name": agent.name,
                "agent_type": agent.agent_type,
                "reputation_score": agent.reputation_score,
                "status": agent.status,
            }
        })

    return {
        "agent_id": agent.id,
        "agent_code": agent.agent_code,
        "bids": items,
        "total_bids": len(items),
    }


def get_bid_by_id(db: Session, bid_id: int) -> Optional[Bid]:
    """Retrieve single bid by ID."""
    return db.query(Bid).filter(Bid.id == bid_id).first()


def update_bid(db: Session, bid_id: int, payload: BidUpdate) -> Bid:
    """
    Update a pending bid and recalculate its selection score.
    """
    bid = db.query(Bid).filter(Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid with id {bid_id} not found",
        )

    if bid.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update bid in '{bid.status}' status. Only pending bids can be edited.",
        )

    task = db.query(Task).filter(Task.id == bid.task_id).first()
    if task and task.status == "assigned":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot update bid: task has already been assigned to another agent.",
        )

    if payload.bid_amount is not None:
        if task and payload.bid_amount > task.reward:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bid amount ({payload.bid_amount} AP) cannot exceed task reward ({task.reward} AP).",
            )
        bid.bid_amount = payload.bid_amount

    if payload.estimated_completion_minutes is not None:
        bid.estimated_completion_minutes = payload.estimated_completion_minutes

    if payload.proposal is not None:
        bid.proposal = payload.proposal

    # Recalculate selection score
    task_reward = task.reward if task else bid.bid_amount
    bid.selection_score = calculate_bid_selection_score(
        match_score=bid.match_score_snapshot,
        reputation=float(bid.reputation_snapshot),
        bid_amount=bid.bid_amount,
        task_reward=task_reward,
        estimated_minutes=bid.estimated_completion_minutes,
    )
    bid.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(bid)
    return bid


def withdraw_bid(db: Session, bid_id: int) -> Bid:
    """
    Withdraw a pending bid.
    """
    bid = db.query(Bid).filter(Bid.id == bid_id).first()
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid with id {bid_id} not found",
        )

    if bid.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot withdraw bid with status '{bid.status}'. Only pending bids can be withdrawn.",
        )

    bid.status = "withdrawn"
    bid.withdrawn_at = datetime.utcnow()
    bid.updated_at = datetime.utcnow()

    # Check if task should revert to 'open' if no other active bids exist
    remaining_active_bids = db.query(Bid).filter(
        Bid.task_id == bid.task_id,
        Bid.status == "pending",
        Bid.id != bid.id,
    ).count()

    task = db.query(Task).filter(Task.id == bid.task_id).first()
    if task and task.status == "bidding" and remaining_active_bids == 0:
        task.status = "open"

    db.commit()
    db.refresh(bid)
    return bid


def select_winning_bid(db: Session, task_id: int, bid_id: int) -> Dict[str, Any]:
    """
    Atomically select winning bid for task assignment:
    - Sets Task status to 'assigned', sets assigned_agent_id, selected_bid_id, assigned_at
    - Sets winning Bid status to 'accepted'
    - Rejects all other competing pending bids on the task
    - Sets winning Agent status to 'busy'
    """
    # 1. Validate Task
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found",
        )

    if task.status == "assigned":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Task has already been assigned to an agent.",
        )

    if task.status not in ("open", "bidding"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot select bid for task in '{task.status}' status.",
        )

    # 2. Validate Winning Bid
    bid = db.query(Bid).filter(Bid.id == bid_id, Bid.task_id == task_id).first()
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bid with id {bid_id} belonging to task {task_id} not found",
        )

    if bid.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot select bid with status '{bid.status}'. Only pending bids can be selected.",
        )

    # 3. Validate Winning Agent
    agent = db.query(Agent).filter(Agent.id == bid.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent with id {bid.agent_id} not found",
        )

    if not agent.is_active or agent.status in ("offline", "suspended"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent '{agent.name}' is no longer active / available (status: {agent.status}).",
        )

    # 4. Atomic Transactional Updates
    now = datetime.utcnow()

    try:
        # Update Task
        task.status = "assigned"
        task.assigned_agent_id = agent.id
        task.selected_bid_id = bid.id
        task.assigned_at = now
        task.updated_at = now

        # Update Winning Bid
        bid.status = "accepted"
        bid.accepted_at = now
        bid.updated_at = now

        # Reject other competing pending bids on the same task
        db.query(Bid).filter(
            Bid.task_id == task_id,
            Bid.id != bid_id,
            Bid.status == "pending",
        ).update({
            "status": "rejected",
            "rejected_at": now,
            "updated_at": now,
        })

        # Set Agent status to busy
        agent.status = "busy"
        agent.updated_at = now

        # 5. Atomically create Escrow and lock task reward from Requester Wallet
        escrow = escrow_service.create_escrow_for_task(
            db=db,
            task=task,
            worker_agent_id=agent.id,
            reward_amount=task.reward,
        )

        db.commit()
        db.refresh(task)
        db.refresh(bid)
        db.refresh(agent)
        db.refresh(escrow)
    except Exception as e:
        db.rollback()
        raise e

    return {
        "message": f"Bid {bid.bid_code} accepted. Task {task.task_code} successfully assigned to agent {agent.name}. {task.reward} AP locked in escrow {escrow.escrow_code}.",
        "task_id": task.id,
        "task_code": task.task_code,
        "task_status": task.status,
        "assigned_agent_id": agent.id,
        "assigned_agent_name": agent.name,
        "assigned_agent_code": agent.agent_code,
        "selected_bid_id": bid.id,
        "selected_bid_code": bid.bid_code,
        "selected_bid_amount": bid.bid_amount,
        "escrow_id": escrow.id,
        "escrow_code": escrow.escrow_code,
        "escrow_status": escrow.status,
        "reward_locked": escrow.reward_amount,
        "assigned_at": task.assigned_at,
    }
