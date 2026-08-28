"""
Execution API router — 8 endpoints covering the full execution lifecycle.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from app.models.task_execution import TaskExecution
from app.models.task import Task
from app.models.agent import Agent
from app.schemas.execution import (
    ExecutionStartResponse,
    ExecutionResponse,
    ExecutionDetailResponse,
    ExecutionLogsResponse,
    ExecutionLogResponse,
    ExecutionSubmitResponse,
    AgentAssignedTasksResponse,
    AgentAssignedTaskItem,
    ExecutionTaskSummary,
    ExecutionAgentSummary,
    ExecutionBidSummary,
)
from app.services import execution_service
from app.services import submission_service
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api", tags=["Executions"])


# ---------------------------------------------------------------------------
# Task-scoped endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/tasks/{task_id}/execution/start",
    status_code=201,
    response_model=ExecutionStartResponse,
    summary="Start execution for an assigned task"
)
def start_task_execution(task_id: int, db: Session = Depends(get_db)):
    """
    Create and begin a new TaskExecution for a task in 'assigned' status.
    Transitions task → 'executing'.
    """
    execution = execution_service.start_execution(db, task_id)
    return ExecutionStartResponse(
        id=execution.id,
        execution_code=execution.execution_code,
        task_id=execution.task_id,
        agent_id=execution.agent_id,
        bid_id=execution.bid_id,
        status=execution.status,
        progress=execution.progress,
        started_at=execution.started_at,
        created_at=execution.created_at,
        message=f"Execution {execution.execution_code} created successfully. Call /run to execute.",
    )


@router.get(
    "/tasks/{task_id}/execution",
    response_model=ExecutionDetailResponse,
    summary="Get current execution for a task"
)
def get_task_execution(task_id: int, db: Session = Depends(get_db)):
    """Return the latest execution for a task (404 if none exists)."""
    exc = execution_service.get_task_execution(db, task_id)
    if not exc:
        raise HTTPException(status_code=404, detail=f"No execution found for task {task_id}")
    return _build_detail(exc, db)


# ---------------------------------------------------------------------------
# Execution-scoped endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/executions/{execution_id}/run",
    response_model=ExecutionDetailResponse,
    summary="Run the executor for an execution"
)
def run_execution(execution_id: int, db: Session = Depends(get_db)):
    """
    Synchronously run the appropriate executor for this execution.
    On success: status → 'completed', progress=100, output stored.
    On failure: status → 'failed', error_message stored.
    """
    exc = execution_service.run_execution(db, execution_id)
    return _build_detail(exc, db)


@router.post(
    "/executions/{execution_id}/submit",
    response_model=ExecutionSubmitResponse,
    summary="Submit a completed execution — creates immutable ResultSubmission"
)
def submit_execution(execution_id: int, db: Session = Depends(get_db)):
    """
    Phase 9 upgrade: instead of only changing status, creates a full
    immutable ResultSubmission package with frozen snapshots and SHA-256
    integrity hash.

    Returns 409 if already submitted.
    Returns 400 if execution is not completed.
    """
    try:
        submission = submission_service.create_submission_from_execution(db, execution_id)
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("DUPLICATE_SUBMISSION:"):
            # Parse: DUPLICATE_SUBMISSION:{id}:{code}
            parts = msg.split(":")
            existing_id = int(parts[1]) if len(parts) > 1 else None
            existing_code = parts[2] if len(parts) > 2 else None
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "Already submitted",
                    "submission_id": existing_id,
                    "submission_code": existing_code,
                },
            )
        raise HTTPException(status_code=400, detail=msg)

    # Reload execution after service committed
    exc_obj = db.query(TaskExecution).filter(TaskExecution.id == execution_id).first()
    task = db.query(Task).filter(Task.id == exc_obj.task_id).first() if exc_obj else None

    return ExecutionSubmitResponse(
        message=(
            f"Execution {exc_obj.execution_code if exc_obj else execution_id} submitted. "
            f"ResultSubmission {submission.submission_code} created and locked."
        ),
        execution_id=execution_id,
        execution_code=exc_obj.execution_code if exc_obj else None,
        execution_status=exc_obj.status if exc_obj else "submitted",
        task_id=submission.task_id,
        task_code=task.task_code if task else None,
        task_status=task.status if task else "submitted",
        submitted_at=submission.submitted_at,
        submission_id=submission.id,
        submission_code=submission.submission_code,
    )



@router.post(
    "/executions/{execution_id}/retry",
    response_model=ExecutionDetailResponse,
    summary="Retry a failed execution (max 2 retries)"
)
def retry_execution(execution_id: int, db: Session = Depends(get_db)):
    """Retry a 'failed' execution up to 2 times."""
    exc = execution_service.retry_execution(db, execution_id)
    return _build_detail(exc, db)


@router.get(
    "/executions/{execution_id}",
    response_model=ExecutionDetailResponse,
    summary="Get execution detail"
)
def get_execution(execution_id: int, db: Session = Depends(get_db)):
    """Return full execution details with nested task, agent, and bid summaries."""
    exc = execution_service.get_execution(db, execution_id)
    if not exc:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    return _build_detail(exc, db)


@router.get(
    "/executions/{execution_id}/logs",
    response_model=ExecutionLogsResponse,
    summary="Get ordered execution logs"
)
def get_execution_logs(execution_id: int, db: Session = Depends(get_db)):
    """Return all log entries for an execution in chronological order."""
    exc = execution_service.get_execution(db, execution_id)
    if not exc:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")

    logs = execution_service.get_execution_logs(db, execution_id)
    return ExecutionLogsResponse(
        execution_id=exc.id,
        execution_code=exc.execution_code,
        logs=[ExecutionLogResponse.model_validate(l) for l in logs],
        total_logs=len(logs),
    )


# ---------------------------------------------------------------------------
# Agent-scoped endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/agents/{agent_id}/assigned-tasks",
    response_model=AgentAssignedTasksResponse,
    summary="Get assigned work list for an agent"
)
def get_agent_assigned_tasks(agent_id: int, db: Session = Depends(get_db)):
    """Return tasks in assigned/executing/submitted states for an agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    items_data = execution_service.get_agent_assigned_tasks(db, agent_id)
    items = [AgentAssignedTaskItem(**d) for d in items_data]

    return AgentAssignedTasksResponse(
        agent_id=agent.id,
        agent_code=agent.agent_code,
        tasks=items,
        total=len(items),
    )


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _build_detail(exc: TaskExecution, db: Session) -> ExecutionDetailResponse:
    """Construct a full ExecutionDetailResponse with nested objects."""
    task = db.query(Task).filter(Task.id == exc.task_id).first()
    agent = db.query(Agent).filter(Agent.id == exc.agent_id).first()
    from app.models.bid import Bid
    bid = db.query(Bid).filter(Bid.id == exc.bid_id).first()

    task_summary = None
    if task:
        task_summary = ExecutionTaskSummary(
            id=task.id,
            task_code=task.task_code,
            title=task.title,
            description=task.description,
            category=task.category,
            required_capability=task.required_capability,
            reward=task.reward,
            status=task.status,
        )

    agent_summary = None
    if agent:
        agent_summary = ExecutionAgentSummary(
            id=agent.id,
            agent_code=agent.agent_code,
            name=agent.name,
            agent_type=agent.agent_type,
            reputation_score=agent.reputation_score,
        )

    bid_summary = None
    if bid:
        bid_summary = ExecutionBidSummary(
            id=bid.id,
            bid_code=bid.bid_code,
            bid_amount=bid.bid_amount,
            estimated_completion_minutes=bid.estimated_completion_minutes,
            proposal=bid.proposal,
            selection_score=bid.selection_score,
        )

    return ExecutionDetailResponse(
        id=exc.id,
        execution_code=exc.execution_code,
        task_id=exc.task_id,
        agent_id=exc.agent_id,
        bid_id=exc.bid_id,
        status=exc.status,
        progress=exc.progress,
        attempt_number=exc.attempt_number,
        output_text=exc.output_text,
        structured_output=exc.structured_output,
        execution_metadata=exc.execution_metadata,
        error_message=exc.error_message,
        started_at=exc.started_at,
        completed_at=exc.completed_at,
        submitted_at=exc.submitted_at,
        created_at=exc.created_at,
        updated_at=exc.updated_at,
        task=task_summary,
        agent=agent_summary,
        bid=bid_summary,
    )
