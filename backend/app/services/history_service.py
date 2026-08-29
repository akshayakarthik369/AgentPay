"""
history_service.py — Phase 17 Transaction & Activity History

Aggregates existing database records into unified activity timelines
and transaction histories. Does NOT duplicate existing audit logs or
create new financial records.

Activity Event Types:
  task_created, bid_submitted, worker_selected, escrow_locked,
  execution_started, execution_completed, result_submitted,
  verification_passed, verification_failed, verification_review,
  human_review, dispute_opened, arbitration_decision,
  settlement_completed, settlement_blocked, reputation_updated
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.agent import Agent
from app.models.bid import Bid
from app.models.task_execution import TaskExecution
from app.models.result_submission import ResultSubmission
from app.models.verification import Verification
from app.models.escrow import Escrow
from app.models.settlement import Settlement, LedgerEntry
from app.models.reputation import ReputationEvent
from app.models.human_review import HumanReview
from app.models.dispute import Dispute
from app.models.arbitration import Arbitration


# ─────────────────────────────────────────────────────────────────────────────
# Shared value objects (plain dicts to avoid Pydantic import loops)
# ─────────────────────────────────────────────────────────────────────────────

def _activity(
    event_type: str,
    title: str,
    description: str,
    created_at: datetime,
    *,
    task_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    related_entity_type: Optional[str] = None,
    related_entity_id: Optional[int] = None,
    related_entity_code: Optional[str] = None,
    amount: Optional[float] = None,
    status: Optional[str] = None,
) -> dict:
    return {
        "event_type": event_type,
        "title": title,
        "description": description,
        "task_id": task_id,
        "agent_id": agent_id,
        "related_entity_type": related_entity_type,
        "related_entity_id": related_entity_id,
        "related_entity_code": related_entity_code,
        "amount": amount,
        "status": status,
        "created_at": created_at.isoformat() if created_at else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Core aggregation: build activity events from existing records
# ─────────────────────────────────────────────────────────────────────────────

def _events_for_task(db: Session, task: Task) -> List[dict]:
    """Return all activity events for a single Task in chronological order."""
    events: List[dict] = []

    # 1. Task created
    events.append(_activity(
        "task_created", f"Task Created: {task.title}",
        f"Task {task.task_code or f'AP-{task.id}'} was published with {task.reward} AP reward.",
        task.created_at,
        task_id=task.id,
        related_entity_type="task", related_entity_id=task.id,
        related_entity_code=task.task_code,
        amount=task.reward, status="open",
    ))

    # 2. Bids
    bids = db.query(Bid).filter(Bid.task_id == task.id).order_by(Bid.created_at.asc()).all()
    for bid in bids:
        events.append(_activity(
            "bid_submitted", f"Bid Submitted — Agent #{bid.agent_id}",
            f"Agent #{bid.agent_id} submitted a bid of {bid.bid_amount} AP on task {task.task_code or task.id}.",
            bid.created_at,
            task_id=task.id, agent_id=bid.agent_id,
            related_entity_type="bid", related_entity_id=bid.id,
            amount=bid.bid_amount, status=bid.status,
        ))

    # 3. Assignment / worker selected
    if task.assigned_agent_id and task.assigned_at:
        events.append(_activity(
            "worker_selected", f"Worker Assigned — Agent #{task.assigned_agent_id}",
            f"Agent #{task.assigned_agent_id} was selected as worker for task {task.task_code or task.id}.",
            task.assigned_at,
            task_id=task.id, agent_id=task.assigned_agent_id,
            related_entity_type="task", related_entity_id=task.id, status="assigned",
        ))

    # 4. Escrow
    escrow = db.query(Escrow).filter(Escrow.task_id == task.id).first()
    if escrow:
        events.append(_activity(
            "escrow_locked", f"Escrow Locked — {escrow.reward_amount} AP",
            f"Escrow {escrow.escrow_code} locked {escrow.reward_amount} AP for task {task.task_code or task.id}.",
            escrow.locked_at or escrow.created_at,
            task_id=task.id,
            related_entity_type="escrow", related_entity_id=escrow.id,
            related_entity_code=escrow.escrow_code,
            amount=escrow.reward_amount, status=escrow.status,
        ))

    # 5. Executions
    executions = db.query(TaskExecution).filter(TaskExecution.task_id == task.id).order_by(TaskExecution.started_at.asc()).all()
    for ex in executions:
        if ex.started_at:
            events.append(_activity(
                "execution_started", f"Execution Started",
                f"Worker agent #{ex.agent_id} started executing task {task.task_code or task.id}.",
                ex.started_at,
                task_id=task.id, agent_id=ex.agent_id,
                related_entity_type="execution", related_entity_id=ex.id,
                status="running",
            ))
        if ex.completed_at:
            events.append(_activity(
                "execution_completed", f"Execution Completed",
                f"Execution finished with status '{ex.status}'.",
                ex.completed_at,
                task_id=task.id, agent_id=ex.agent_id,
                related_entity_type="execution", related_entity_id=ex.id,
                status=ex.status,
            ))

    # 6. Submission
    submission = db.query(ResultSubmission).filter(ResultSubmission.task_id == task.id).order_by(ResultSubmission.id.desc()).first()
    if submission:
        events.append(_activity(
            "result_submitted", "Result Package Submitted",
            f"Agent #{submission.agent_id} submitted deliverables for verification.",
            submission.submitted_at or submission.created_at,
            task_id=task.id, agent_id=submission.agent_id,
            related_entity_type="submission", related_entity_id=submission.id,
            related_entity_code=submission.submission_code,
            status=submission.status,
        ))

    # 7. Verifications
    verifications = db.query(Verification).filter(Verification.task_id == task.id).order_by(Verification.id.asc()).all()
    for v in verifications:
        if v.decision == "PASS":
            etype = "verification_passed"
            title = f"Verification PASSED — Score {v.overall_score:.0f}%"
            desc = f"Independent verifier confirmed deliverables meet quality threshold."
        elif v.decision == "FAIL":
            etype = "verification_failed"
            title = f"Verification FAILED — Score {v.overall_score:.0f}%"
            desc = f"Deliverables did not meet the required quality score of {v.required_score:.0f}%."
        else:
            etype = "verification_review"
            title = "Verification → HUMAN REVIEW Required"
            desc = "Verification could not make a confident determination. Escalated to human review."
        ts = v.completed_at or v.created_at
        events.append(_activity(
            etype, title, desc, ts,
            task_id=task.id,
            related_entity_type="verification", related_entity_id=v.id,
            status=v.decision,
        ))

    # 8. Human Review
    human_reviews = db.query(HumanReview).filter(HumanReview.task_id == task.id).order_by(HumanReview.id.asc()).all()
    for hr in human_reviews:
        ts = hr.resolved_at or hr.started_at or hr.created_at
        events.append(_activity(
            "human_review", f"Human Review — {hr.status.upper()}",
            f"Review {hr.review_code or hr.id}: {hr.status}. Decision: {hr.decision or 'Pending'}.",
            ts,
            task_id=task.id,
            related_entity_type="human_review", related_entity_id=hr.id,
            related_entity_code=hr.review_code,
            status=hr.status,
        ))

    # 9. Disputes
    disputes = db.query(Dispute).filter(Dispute.task_id == task.id).order_by(Dispute.id.asc()).all()
    for d in disputes:
        events.append(_activity(
            "dispute_opened", f"Dispute Raised — {(d.dispute_code or str(d.id))}",
            f"Worker raised a formal dispute: '{d.reason.replace('_', ' ')}'.",
            d.created_at,
            task_id=task.id, agent_id=d.worker_agent_id,
            related_entity_type="dispute", related_entity_id=d.id,
            related_entity_code=d.dispute_code,
            status=d.status,
        ))

    # 10. Arbitration
    if disputes:
        dispute_ids = [d.id for d in disputes]
        arbitrations = db.query(Arbitration).filter(Arbitration.dispute_id.in_(dispute_ids)).order_by(Arbitration.id.asc()).all()
        for arb in arbitrations:
            if arb.decision:
                decision_label = arb.decision.replace("_", " ").title()
                ts = arb.resolved_at or arb.created_at
                events.append(_activity(
                    "arbitration_decision", f"AI Arbitration Ruling — {decision_label}",
                    f"Arbitrator #{arb.arbitrator_agent_id} ruled: {decision_label} ({arb.confidence_score:.1f}% confidence). {(arb.reasoning_summary or '')[:100]}",
                    ts,
                    task_id=task.id,
                    related_entity_type="arbitration", related_entity_id=arb.id,
                    related_entity_code=arb.arbitration_code,
                    status=arb.decision,
                ))

    # 11. Settlement
    settlement = db.query(Settlement).filter(Settlement.task_id == task.id).order_by(Settlement.id.desc()).first()
    if settlement:
        if settlement.status == "completed":
            events.append(_activity(
                "settlement_completed", f"Settlement Completed — {settlement.amount} AP",
                f"AP Credits transferred to worker agent #{settlement.worker_agent_id}. Settlement {settlement.settlement_code}.",
                settlement.completed_at or settlement.updated_at,
                task_id=task.id, agent_id=settlement.worker_agent_id,
                related_entity_type="settlement", related_entity_id=settlement.id,
                related_entity_code=settlement.settlement_code,
                amount=settlement.amount, status="completed",
            ))
        elif settlement.status in ("blocked", "failed"):
            events.append(_activity(
                "settlement_blocked", f"Settlement Blocked — {settlement.amount} AP",
                f"AP Credits NOT released. Settlement {settlement.settlement_code} is {settlement.status}. Reason: {settlement.failure_reason or 'Verification FAIL or active dispute.'}",
                settlement.updated_at or settlement.created_at,
                task_id=task.id,
                related_entity_type="settlement", related_entity_id=settlement.id,
                related_entity_code=settlement.settlement_code,
                amount=settlement.amount, status=settlement.status,
            ))

    # 12. Reputation events
    if task.assigned_agent_id:
        rep_events = db.query(ReputationEvent).filter(
            ReputationEvent.task_id == task.id,
            ReputationEvent.agent_id == task.assigned_agent_id,
        ).order_by(ReputationEvent.id.asc()).all()
        for re in rep_events:
            sign = "+" if re.score_delta >= 0 else ""
            events.append(_activity(
                "reputation_updated", f"Reputation Updated — {sign}{re.score_delta:+.1f} pts",
                f"Agent #{re.agent_id} reputation: {re.previous_score:.1f} → {re.new_score:.1f}. Reason: {re.reason[:80]}.",
                re.created_at,
                task_id=task.id, agent_id=re.agent_id,
                related_entity_type="reputation_event", related_entity_id=re.id,
                related_entity_code=re.event_code,
                amount=re.score_delta, status=re.event_type,
            ))

    # Sort by timestamp chronologically
    events.sort(key=lambda e: e["created_at"] or "")
    return events


# ─────────────────────────────────────────────────────────────────────────────
# Public API functions
# ─────────────────────────────────────────────────────────────────────────────

def get_task_activity(
    db: Session,
    task_id: int,
) -> List[dict]:
    """Full lifecycle timeline for a single task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return []
    return _events_for_task(db, task)


def get_global_activity(
    db: Session,
    event_type: Optional[str] = None,
    task_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    limit: int = 100,
) -> List[dict]:
    """
    Global activity feed: most recent events across all tasks.
    Filters by event_type, task_id, or agent_id if provided.
    """
    # Fetch tasks in chronological order (most recent first)
    task_query = db.query(Task).order_by(Task.id.desc())
    if task_id:
        task_query = task_query.filter(Task.id == task_id)
    tasks = task_query.limit(50).all()

    all_events: List[dict] = []
    for task in tasks:
        events = _events_for_task(db, task)
        all_events.extend(events)

    # Apply filters
    if event_type:
        all_events = [e for e in all_events if e["event_type"] == event_type]
    if agent_id:
        all_events = [e for e in all_events if e.get("agent_id") == agent_id]
    if task_id:
        all_events = [e for e in all_events if e.get("task_id") == task_id]

    # Sort descending (most recent first) and limit
    all_events.sort(key=lambda e: e["created_at"] or "", reverse=True)
    return all_events[:limit]


def get_agent_activity(
    db: Session,
    agent_id: int,
    limit: int = 100,
) -> List[dict]:
    """Recent activity events where the given agent was involved."""
    # Find tasks this agent was assigned to
    tasks_as_worker = db.query(Task).filter(Task.assigned_agent_id == agent_id).order_by(Task.id.desc()).limit(30).all()
    # Find tasks where agent submitted bids
    bid_task_ids = [b.task_id for b in db.query(Bid.task_id).filter(Bid.agent_id == agent_id).distinct().all()]
    bid_tasks = db.query(Task).filter(Task.id.in_(bid_task_ids), ~Task.id.in_([t.id for t in tasks_as_worker])).order_by(Task.id.desc()).limit(15).all()

    all_events: List[dict] = []
    seen_task_ids: set = set()
    for task in tasks_as_worker + bid_tasks:
        if task.id in seen_task_ids:
            continue
        seen_task_ids.add(task.id)
        events = _events_for_task(db, task)
        # Filter to events relevant to this agent
        agent_events = [
            e for e in events
            if e.get("agent_id") == agent_id or e.get("task_id") is not None
        ]
        all_events.extend(agent_events)

    all_events.sort(key=lambda e: e["created_at"] or "", reverse=True)
    return all_events[:limit]


def get_wallet_transactions(
    db: Session,
    wallet_id: Optional[int] = None,
    limit: int = 100,
) -> List[dict]:
    """
    Real AP Credit movements from the LedgerEntry table.
    Only real financial transactions (escrow_lock, settlement_debit, settlement_credit).
    """
    query = db.query(LedgerEntry)
    if wallet_id:
        query = query.filter(LedgerEntry.wallet_id == wallet_id)
    entries = query.order_by(LedgerEntry.created_at.desc()).limit(limit).all()

    transactions = []
    for le in entries:
        # Determine direction for display
        if le.entry_type == "settlement_credit":
            direction = "credit"
            status = "completed"
        elif le.entry_type == "settlement_debit":
            direction = "debit"
            status = "completed"
        elif le.entry_type == "escrow_lock":
            direction = "lock"
            status = "locked"
        else:
            direction = "other"
            status = "completed"

        # Fetch settlement reference
        settlement_code = None
        task_id = le.task_id
        if le.settlement_id:
            s = db.query(Settlement.settlement_code, Settlement.task_id).filter(Settlement.id == le.settlement_id).first()
            if s:
                settlement_code = s.settlement_code
                task_id = task_id or s.task_id

        # Fetch escrow reference
        escrow_code = None
        if le.escrow_id:
            e = db.query(Escrow.escrow_code).filter(Escrow.id == le.escrow_id).first()
            if e:
                escrow_code = e.escrow_code

        # Fetch task title
        task_title = None
        if task_id:
            t = db.query(Task.title, Task.task_code).filter(Task.id == task_id).first()
            if t:
                task_title = t.title

        transactions.append({
            "id": le.id,
            "entry_code": le.entry_code,
            "entry_type": le.entry_type,
            "direction": direction,
            "amount": le.amount,
            "balance_type": le.balance_type,
            "description": le.description,
            "status": status,
            "wallet_id": le.wallet_id,
            "settlement_id": le.settlement_id,
            "settlement_code": settlement_code,
            "escrow_id": le.escrow_id,
            "escrow_code": escrow_code,
            "task_id": task_id,
            "task_title": task_title,
            "created_at": le.created_at.isoformat() if le.created_at else None,
        })

    return transactions
