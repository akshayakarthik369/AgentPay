"""
Execution Service — orchestrates the full task execution lifecycle:
start → run → submit | retry | cancel
"""
from __future__ import annotations
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.task import Task
from app.models.agent import Agent
from app.models.bid import Bid
from app.models.task_execution import TaskExecution, ExecutionLog
from app.execution.providers import LocalDeterministicProvider

MAX_RETRIES = 2


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _add_log(db: Session, execution_id: int, level: str, step: str, message: str) -> None:
    """Append a single log entry for an execution (committed in caller's transaction)."""
    log = ExecutionLog(
        execution_id=execution_id,
        level=level,
        step=step,
        message=message,
    )
    db.add(log)


def _set_progress(db: Session, execution: TaskExecution, progress: int) -> None:
    """Update execution progress in-place (not committed — caller commits)."""
    execution.progress = progress
    execution.updated_at = datetime.utcnow()


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def start_execution(db: Session, task_id: int) -> TaskExecution:
    """
    Create a new TaskExecution for an assigned task.

    Validations:
    - Task exists and status == 'assigned'
    - Task has assigned_agent_id and selected_bid_id
    - Agent exists and status == 'busy'
    - Accepted bid exists
    - No other active (running/pending) execution already exists
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    if task.status != "assigned":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start execution: task status is '{task.status}' (must be 'assigned')"
        )

    if not task.assigned_agent_id or not task.selected_bid_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot start execution: task is missing assigned_agent_id or selected_bid_id"
        )

    agent = db.query(Agent).filter(Agent.id == task.assigned_agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Assigned agent not found")

    from app.services import security_service
    security_service.check_agent_eligibility(agent, "execute tasks")

    if agent.status != "busy":
        raise HTTPException(
            status_code=400,
            detail=f"Agent '{agent.name}' status is '{agent.status}' — expected 'busy' for assigned task"
        )

    bid = db.query(Bid).filter(Bid.id == task.selected_bid_id, Bid.status == "accepted").first()
    if not bid:
        raise HTTPException(status_code=400, detail="No accepted bid found for this task")

    # Prevent duplicate active executions
    existing = db.query(TaskExecution).filter(
        TaskExecution.task_id == task_id,
        TaskExecution.status.in_(["pending", "running"]),
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"An active execution ({existing.execution_code}) already exists for this task"
        )

    # Build input snapshot (frozen context)
    snapshot = {
        "task_code": task.task_code,
        "title": task.title,
        "description": task.description,
        "category": task.category,
        "required_capability": task.required_capability,
        "reward": task.reward,
        "minimum_quality_score": task.minimum_quality_score,
        "agent": {
            "id": agent.id,
            "agent_code": agent.agent_code,
            "name": agent.name,
            "capabilities": agent.capabilities,
            "reputation_score": agent.reputation_score,
        },
        "bid": {
            "id": bid.id,
            "bid_code": bid.bid_code,
            "bid_amount": bid.bid_amount,
            "proposal": bid.proposal,
            "estimated_completion_minutes": bid.estimated_completion_minutes,
        },
    }

    now = datetime.utcnow()
    execution = TaskExecution(
        task_id=task.id,
        agent_id=agent.id,
        bid_id=bid.id,
        status="running",
        progress=0,
        attempt_number=1,
        input_snapshot=json.dumps(snapshot),
        started_at=now,
    )
    db.add(execution)

    # Transition task to 'executing'
    task.status = "executing"
    task.updated_at = now

    db.commit()
    db.refresh(execution)

    # Initial log (after commit so execution_id is available)
    _add_log(db, execution.id, "info", "start", f"Execution {execution.execution_code} started for task {task.task_code}")
    db.commit()

    return execution


def run_execution(db: Session, execution_id: int) -> TaskExecution:
    """
    Run the execution engine for a pending/running execution.
    Synchronous — blocks until complete.
    """
    execution = db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    if execution.status not in ("pending", "running"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot run execution with status '{execution.status}' (must be pending/running)"
        )

    # Load frozen snapshot
    snapshot: Dict[str, Any] = {}
    if execution.input_snapshot:
        try:
            snapshot = json.loads(execution.input_snapshot)
        except Exception:
            pass

    task_title = snapshot.get("title", "")
    task_description = snapshot.get("description", "")
    category = snapshot.get("category", "")
    required_capability = snapshot.get("required_capability", "")
    agent_data = snapshot.get("agent", {})
    agent_name = agent_data.get("name", "Unknown Agent")
    agent_capabilities = agent_data.get("capabilities", [])
    bid_data = snapshot.get("bid", {})
    bid_proposal = bid_data.get("proposal", "")

    now = datetime.utcnow()

    # log_fn and progress_fn flush immediately to DB
    def log_fn(level: str, step: str, message: str) -> None:
        _add_log(db, execution.id, level, step, message)
        db.commit()

    def progress_fn(pct: int) -> None:
        execution.progress = pct
        execution.updated_at = datetime.utcnow()
        db.commit()

    provider = LocalDeterministicProvider()
    result = provider.run(
        task_title=task_title,
        task_description=task_description,
        category=category,
        required_capability=required_capability,
        agent_name=agent_name,
        agent_capabilities=agent_capabilities,
        bid_proposal=bid_proposal,
        log_fn=log_fn,
        progress_fn=progress_fn,
    )

    now = datetime.utcnow()

    if result.success:
        execution.status = "completed"
        execution.output_text = result.output_text
        execution.structured_output = json.dumps(result.structured_output)
        execution.execution_metadata = json.dumps(result.metadata)
        execution.progress = 100
        execution.completed_at = now
        execution.error_message = None
    else:
        execution.status = "failed"
        execution.error_message = result.error_message
        execution.execution_metadata = json.dumps(result.metadata)
        execution.completed_at = now

        # Also mark the task as failed
        task = db.query(Task).filter(Task.id == execution.task_id).first()
        if task:
            task.status = "failed"
            task.updated_at = now

    execution.updated_at = now
    db.commit()
    db.refresh(execution)
    return execution


def retry_execution(db: Session, execution_id: int) -> TaskExecution:
    """Retry a failed execution. Maximum MAX_RETRIES attempts total."""
    execution = db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    if execution.status != "failed":
        raise HTTPException(
            status_code=400,
            detail=f"Can only retry failed executions (current status: '{execution.status}')"
        )

    if execution.attempt_number >= MAX_RETRIES + 1:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum retry limit ({MAX_RETRIES}) reached for execution {execution.execution_code}"
        )

    now = datetime.utcnow()
    execution.status = "running"
    execution.error_message = None
    execution.progress = 0
    execution.attempt_number += 1
    execution.started_at = now
    execution.completed_at = None
    execution.updated_at = now

    # Restore task to executing
    task = db.query(Task).filter(Task.id == execution.task_id).first()
    if task:
        task.status = "executing"
        task.updated_at = now

    db.commit()

    _add_log(db, execution.id, "info", "retry", f"Retry attempt {execution.attempt_number} initiated")
    db.commit()

    return run_execution(db, execution_id)


def submit_execution(db: Session, execution_id: int) -> TaskExecution:
    """Submit a completed execution result for (future) verification."""
    execution = db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    if execution.status == "submitted":
        raise HTTPException(
            status_code=409,
            detail=f"Execution {execution.execution_code} has already been submitted"
        )

    if execution.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Can only submit completed executions (current status: '{execution.status}')"
        )

    now = datetime.utcnow()
    execution.status = "submitted"
    execution.submitted_at = now
    execution.updated_at = now

    # Transition task to submitted
    task = db.query(Task).filter(Task.id == execution.task_id).first()
    if task:
        task.status = "submitted"
        task.updated_at = now

    db.commit()

    _add_log(db, execution.id, "info", "submitted", "Execution result submitted for verification")
    db.commit()

    db.refresh(execution)
    return execution


def get_execution(db: Session, execution_id: int) -> Optional[TaskExecution]:
    """Fetch a single execution by ID."""
    return db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()


def get_task_execution(db: Session, task_id: int) -> Optional[TaskExecution]:
    """Fetch the most recent execution for a task."""
    return (
        db.query(TaskExecution)
        .filter(TaskExecution.task_id == task_id)
        .order_by(TaskExecution.id.desc())
        .first()
    )


def get_execution_logs(db: Session, execution_id: int) -> List[ExecutionLog]:
    """Fetch ordered logs for an execution."""
    return (
        db.query(ExecutionLog)
        .filter(ExecutionLog.execution_id == execution_id)
        .order_by(ExecutionLog.created_at)
        .all()
    )


def get_agent_assigned_tasks(db: Session, agent_id: int) -> List[Dict[str, Any]]:
    """Return tasks assigned to this agent in active execution states."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        return []

    tasks = (
        db.query(Task)
        .filter(
            Task.assigned_agent_id == agent_id,
            Task.status.in_(["assigned", "executing", "submitted", "failed"]),
        )
        .order_by(Task.assigned_at.desc())
        .all()
    )

    items = []
    for t in tasks:
        # Get latest execution for this task
        exc = (
            db.query(TaskExecution)
            .filter(TaskExecution.task_id == t.id)
            .order_by(TaskExecution.id.desc())
            .first()
        )
        # Get accepted bid
        bid = db.query(Bid).filter(Bid.id == t.selected_bid_id).first() if t.selected_bid_id else None

        items.append({
            "task_id": t.id,
            "task_code": t.task_code,
            "title": t.title,
            "category": t.category,
            "required_capability": t.required_capability,
            "reward": t.reward,
            "deadline": t.deadline,
            "task_status": t.status,
            "bid_id": bid.id if bid else None,
            "bid_code": bid.bid_code if bid else None,
            "bid_amount": bid.bid_amount if bid else None,
            "execution_id": exc.id if exc else None,
            "execution_code": exc.execution_code if exc else None,
            "execution_status": exc.status if exc else None,
            "execution_progress": exc.progress if exc else None,
            "assigned_at": t.assigned_at,
        })

    return items
