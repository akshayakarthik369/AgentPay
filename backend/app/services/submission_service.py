"""
Phase 9 — Submission Service.

Handles the full lifecycle of result submission packaging:
  - Building frozen snapshots of task / agent / bid / execution
  - Evidence & provenance assembly
  - Self-assessment extraction
  - Limitations derivation
  - SHA-256 integrity fingerprinting
  - Duplicate / locking enforcement
  - Audit logging
  - Query helpers

Does NOT perform quality verification (Phase 10).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.task import Task
from app.models.agent import Agent
from app.models.bid import Bid
from app.models.task_execution import TaskExecution
from app.models.result_submission import ResultSubmission, SubmissionAuditLog


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_json(value: Any) -> Any:
    """Recursively coerce datetimes / floats to JSON-safe types."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _safe_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_json(i) for i in value]
    return value


def _canonical_json(obj: Any) -> str:
    """Serialize deterministically: sorted keys, no extra whitespace."""
    return json.dumps(_safe_json(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _parse_json_field(raw: Optional[str]) -> Any:
    """Parse a stored JSON string; return {} / [] on failure."""
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


# ── Snapshot builders ─────────────────────────────────────────────────────────

def build_task_snapshot(task: Task) -> Dict:
    """Freeze task context at submission time."""
    return {
        "id": task.id,
        "task_code": task.task_code,
        "title": task.title,
        "description": task.description,
        "category": task.category,
        "required_capability": task.required_capability,
        "reward": task.reward,
        "minimum_reputation": task.minimum_reputation,
        "minimum_quality_score": task.minimum_quality_score,
        "deadline": task.deadline.isoformat() if task.deadline else None,
        "assigned_agent_id": task.assigned_agent_id,
        "selected_bid_id": task.selected_bid_id,
        "status_at_submission": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


def build_agent_snapshot(agent: Agent) -> Dict:
    """Freeze agent identity and metrics at submission time."""
    return {
        "id": agent.id,
        "agent_code": agent.agent_code,
        "name": agent.name,
        "agent_type": agent.agent_type,
        "capabilities": agent.capabilities or [],
        "reputation_score": agent.reputation_score,
        "tasks_completed": agent.tasks_completed,
        "tasks_failed": agent.tasks_failed,
        "success_rate": agent.success_rate,
        "average_verification_score": agent.average_verification_score,
        "status_at_submission": agent.status,
    }


def build_bid_snapshot(bid: Bid) -> Dict:
    """Freeze winning bid details at submission time."""
    return {
        "id": bid.id,
        "bid_code": bid.bid_code,
        "bid_amount": bid.bid_amount,
        "estimated_completion_minutes": bid.estimated_completion_minutes,
        "proposal": bid.proposal,
        "match_score_snapshot": bid.match_score_snapshot,
        "reputation_snapshot": bid.reputation_snapshot,
        "selection_score": bid.selection_score,
        "status": bid.status,
        "accepted_at": bid.accepted_at.isoformat() if bid.accepted_at else None,
    }


def build_execution_snapshot(execution: TaskExecution) -> Dict:
    """Freeze execution metadata (no stack traces, no secrets)."""
    meta = _parse_json_field(execution.execution_metadata) if isinstance(execution.execution_metadata, str) else (execution.execution_metadata or {})
    # Strip any error/trace keys
    safe_meta = {k: v for k, v in (meta or {}).items() if k not in ("traceback", "stack_trace", "raw_error")}
    return {
        "id": execution.id,
        "execution_code": execution.execution_code,
        "provider": safe_meta.get("provider", "local_deterministic"),
        "executor_type": safe_meta.get("executor_type", "unknown"),
        "capability_used": safe_meta.get("capability_used"),
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "status_at_submission": execution.status,
        "progress": execution.progress,
        "attempt_number": execution.attempt_number,
    }


# ── Evidence & self-assessment builders ──────────────────────────────────────

def build_evidence(structured_output: Dict, category: str) -> Dict:
    """Extract auditable evidence from the structured executor output."""
    cat = (category or "").lower()
    base = {
        "source": "task_specification",
        "external_dataset_used": False,
        "external_sources_used": False,
        "evidence_type": "demo_evidence",
        "derived_from": "task_specification",
    }

    if "nlp" in cat or "sentiment" in cat:
        base["findings"] = structured_output.get("themes", [])
        base["sentiment_distribution"] = structured_output.get("sentiment_distribution", {})
        base["processed_objective"] = structured_output.get("summary", "")
    elif "research" in cat or "investigat" in cat:
        base["findings"] = structured_output.get("findings", [])
        base["methodology"] = structured_output.get("methodology", "Task specification analysis")
        base["source_notes"] = "No external web research was performed; output derived from task specification."
    elif "data" in cat or "analytic" in cat:
        base["computed_metrics"] = structured_output.get("key_metrics", {})
        base["observations"] = structured_output.get("observations", [])
        base["dataset_note"] = "No external dataset was provided; synthetic metrics generated from task context."
    elif "code" in cat or "review" in cat:
        base["issues_found"] = structured_output.get("issues", [])
        base["affected_areas"] = structured_output.get("categories_checked", [])
        base["quality_score"] = structured_output.get("quality_score", None)
    elif "content" in cat or "creat" in cat:
        base["sections_produced"] = structured_output.get("sections", [])
        base["word_count"] = structured_output.get("word_count", None)
        base["tone"] = structured_output.get("tone", None)
    else:
        base["steps_performed"] = structured_output.get("steps_performed", [])
        base["general_findings"] = structured_output.get("findings", [])

    return base


def build_provenance(execution: TaskExecution) -> Dict:
    """Record where the result came from (no fabrication)."""
    meta = _parse_json_field(execution.execution_metadata) if isinstance(execution.execution_metadata, str) else (execution.execution_metadata or {})
    return {
        "input_source": "task_specification",
        "external_dataset_used": False,
        "external_sources_used": False,
        "execution_provider": meta.get("provider", "local_deterministic"),
        "executor_type": meta.get("executor_type", "unknown"),
        "capability_used": meta.get("capability_used"),
        "execution_id": execution.id,
        "execution_code": execution.execution_code,
    }


def build_self_assessment(structured_output: Dict) -> Dict:
    """
    Extract the deterministic self-assessment generated by the executor.
    This is WORKER self-assessment only — NOT independent verification.
    """
    sa = structured_output.get("self_assessment", {})
    return {
        "confidence": sa.get("confidence", structured_output.get("confidence", 80)),
        "completeness": sa.get("completeness", 85),
        "format_compliance": sa.get("format_compliance", 100),
        "known_limitations": sa.get("known_limitations", []),
        "assessment_type": "worker_self_assessment",
        "independently_verified": False,
        "note": "These scores were produced by the worker execution and have not yet been independently verified.",
    }


def build_limitations(structured_output: Dict, category: str) -> List[str]:
    """Build a list of explicit limitations based on task context."""
    base: List[str] = [
        "Output generated from task specification; no external live data was accessed.",
        "Execution performed by local deterministic provider; no real LLM calls were made in this phase.",
    ]

    sa = structured_output.get("self_assessment", {})
    known = sa.get("known_limitations", [])
    if isinstance(known, list):
        base.extend([k for k in known if k not in base])

    cat = (category or "").lower()
    if "data" in cat or "analytic" in cat:
        base.append("No external dataset was supplied; synthetic metrics used.")
    elif "research" in cat or "investigat" in cat:
        base.append("External web research was not performed; findings derived from task description.")
    elif "code" in cat or "review" in cat:
        base.append("No live codebase was provided; analysis derived from task description.")

    return list(dict.fromkeys(base))  # deduplicate, preserve order


def derive_result_summary(structured_output: Dict, category: str) -> str:
    """Produce a concise one-sentence result summary without calling an LLM."""
    summary = structured_output.get("summary", "")
    if summary:
        return summary[:300]
    cat = (category or "").lower()
    if "nlp" in cat or "sentiment" in cat:
        return "Completed sentiment analysis with structured findings and confidence metadata."
    if "research" in cat or "investigat" in cat:
        return "Completed research task with structured findings derived from task specification."
    if "data" in cat or "analytic" in cat:
        return "Completed data analysis with computed metrics and structured observations."
    if "code" in cat or "review" in cat:
        return "Completed code review with issue identification and quality scoring."
    if "content" in cat or "creat" in cat:
        return "Completed content creation task with structured sections and word count."
    return "Completed task execution with structured output and self-assessment."


# ── Integrity fingerprinting ──────────────────────────────────────────────────

def generate_integrity_hash(
    task_snapshot: Dict,
    agent_snapshot: Dict,
    bid_snapshot: Dict,
    execution_snapshot: Dict,
    output_text: str,
    structured_output: Dict,
    version: int,
) -> str:
    """
    Generate a deterministic SHA-256 fingerprint over the canonical payload.
    Same unchanged content → same hash.
    """
    canonical = _canonical_json({
        "task_snapshot": task_snapshot,
        "agent_snapshot": agent_snapshot,
        "bid_snapshot": bid_snapshot,
        "execution_snapshot": execution_snapshot,
        "output_text": output_text or "",
        "structured_output": structured_output,
        "version": version,
    })
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def verify_submission_integrity(submission: ResultSubmission) -> Dict:
    """
    Recompute the hash from stored snapshots and compare.
    Returns data-integrity status only — NOT quality verification.
    """
    if not submission.integrity_hash:
        return {"valid": False, "reason": "No integrity hash stored."}

    try:
        task_snap = _parse_json_field(submission.task_snapshot)
        agent_snap = _parse_json_field(submission.agent_snapshot)
        bid_snap = _parse_json_field(submission.bid_snapshot)
        exec_snap = _parse_json_field(submission.execution_snapshot)
        structured = _parse_json_field(submission.structured_output)

        expected = generate_integrity_hash(
            task_snap, agent_snap, bid_snap, exec_snap,
            submission.output_text or "",
            structured,
            submission.version,
        )
        valid = expected == submission.integrity_hash
        return {
            "valid": valid,
            "expected": expected,
            "stored": submission.integrity_hash,
            "algorithm": "SHA-256",
        }
    except Exception as exc:
        return {"valid": False, "reason": str(exc)}


# ── Audit helpers ─────────────────────────────────────────────────────────────

def _add_audit(db: Session, submission_id: int, action: str, message: str,
               actor_type: str = "system", actor_id: Optional[str] = None) -> None:
    log = SubmissionAuditLog(
        submission_id=submission_id,
        action=action,
        actor_type=actor_type,
        actor_id=actor_id,
        message=message,
    )
    db.add(log)
    db.flush()


# ── Master orchestrator ───────────────────────────────────────────────────────

def create_submission_from_execution(db: Session, execution_id: int) -> ResultSubmission:
    """
    Build and lock an immutable ResultSubmission from a completed execution.

    Raises:
        ValueError   — precondition failures (wrong status, missing data)
        IntegrityError — duplicate submission (handled upstream as 409)
    """
    # 1. Load execution
    execution: Optional[TaskExecution] = db.query(TaskExecution).filter(
        TaskExecution.id == execution_id
    ).first()
    if not execution:
        raise ValueError(f"Execution {execution_id} not found.")

    # 2. Guard: already submitted? (check BEFORE status so we return 409 not 400)
    existing = db.query(ResultSubmission).filter(
        ResultSubmission.execution_id == execution_id
    ).first()
    if existing:
        # Use a special marker so the router can return 409
        raise ValueError(f"DUPLICATE_SUBMISSION:{existing.id}:{existing.submission_code}")

    # 3. Now check execution is in the right state
    if execution.status != "completed":
        raise ValueError(
            f"Only completed executions can be submitted. "
            f"Current status: {execution.status!r}."
        )


    # 3. Load related entities
    task: Task = execution.task
    agent: Agent = execution.agent
    bid: Bid = execution.bid

    if not task or not agent or not bid:
        raise ValueError("Execution is missing linked task, agent, or bid.")

    # 4. Parse stored structured output
    structured = _parse_json_field(execution.structured_output) if isinstance(execution.structured_output, str) else (execution.structured_output or {})
    meta = _parse_json_field(execution.execution_metadata) if isinstance(execution.execution_metadata, str) else (execution.execution_metadata or {})

    # 5. Build snapshots
    task_snap = build_task_snapshot(task)
    agent_snap = build_agent_snapshot(agent)
    bid_snap = build_bid_snapshot(bid)
    exec_snap = build_execution_snapshot(execution)

    # 6. Build evidence, provenance, self-assessment, limitations
    evidence = build_evidence(structured, task.category)
    provenance = build_provenance(execution)
    self_assessment = build_self_assessment(structured)
    limitations = build_limitations(structured, task.category)
    result_summary = derive_result_summary(structured, task.category)

    # 7. Confidence score (0–100)
    confidence_score = None
    raw_conf = structured.get("confidence") or self_assessment.get("confidence")
    if raw_conf is not None:
        try:
            c = float(raw_conf)
            confidence_score = int(c * 100) if c <= 1.0 else int(c)
        except (TypeError, ValueError):
            pass

    # 8. Submission metadata
    now = datetime.utcnow()
    duration_secs = None
    if execution.started_at and execution.completed_at:
        duration_secs = int((execution.completed_at - execution.started_at).total_seconds())

    submission_metadata = {
        "executor_type": meta.get("executor_type", "unknown"),
        "provider": meta.get("provider", "local_deterministic"),
        "capability_used": meta.get("capability_used"),
        "execution_duration_seconds": duration_secs,
        "result_format": "structured_json",
        "content_type": "text/plain",
        "generated_at": now.isoformat(),
        "application_version": "agentpay-phase9",
    }

    # 9. Generate integrity hash
    integrity_hash = generate_integrity_hash(
        task_snap, agent_snap, bid_snap, exec_snap,
        execution.output_text or "",
        structured,
        1,
    )

    # 10. Create the submission (locked immediately)
    submission = ResultSubmission(
        task_id=task.id,
        execution_id=execution.id,
        agent_id=agent.id,
        bid_id=bid.id,
        version=1,
        status="locked",
        is_locked=True,
        output_text=execution.output_text,
        structured_output=json.dumps(structured),
        result_summary=result_summary,
        content_type="text/plain",
        evidence=json.dumps(evidence),
        provenance=json.dumps(provenance),
        task_snapshot=json.dumps(task_snap),
        agent_snapshot=json.dumps(agent_snap),
        bid_snapshot=json.dumps(bid_snap),
        execution_snapshot=json.dumps(exec_snap),
        submission_metadata=json.dumps(submission_metadata),
        self_assessment=json.dumps(self_assessment),
        limitations=json.dumps(limitations),
        confidence_score=confidence_score,
        integrity_hash=integrity_hash,
        submitted_at=now,
    )
    db.add(submission)
    db.flush()  # get id so audit logs can ref it

    # 11. Write audit trail
    agent_code = agent.agent_code or str(agent.id)
    _add_audit(db, submission.id, "submission_created",
               f"Result submission package initiated for execution {execution.execution_code}.",
               actor_type="worker_agent", actor_id=agent_code)
    _add_audit(db, submission.id, "snapshots_frozen",
               "Task, agent, bid, and execution snapshots frozen at submission time.",
               actor_type="system")
    _add_audit(db, submission.id, "integrity_hash_generated",
               f"SHA-256 integrity fingerprint generated: {integrity_hash[:20]}...",
               actor_type="system")
    _add_audit(db, submission.id, "submission_locked",
               "Submission locked. Content is now immutable and verifier-ready.",
               actor_type="system")

    # 12. Transition execution & task
    execution.status = "submitted"
    execution.submitted_at = now
    task.status = "submitted"

    db.commit()
    db.refresh(submission)
    return submission


# ── Query helpers ─────────────────────────────────────────────────────────────

def get_submission(db: Session, submission_id: int) -> Optional[ResultSubmission]:
    return db.query(ResultSubmission).filter(ResultSubmission.id == submission_id).first()


def get_submission_by_code(db: Session, code: str) -> Optional[ResultSubmission]:
    return db.query(ResultSubmission).filter(ResultSubmission.submission_code == code).first()


def get_task_submission(db: Session, task_id: int) -> Optional[ResultSubmission]:
    return db.query(ResultSubmission).filter(ResultSubmission.task_id == task_id).first()


def get_agent_submissions(db: Session, agent_id: int) -> List[ResultSubmission]:
    return (
        db.query(ResultSubmission)
        .filter(ResultSubmission.agent_id == agent_id)
        .order_by(ResultSubmission.submitted_at.desc())
        .all()
    )


def get_pending_verification(db: Session) -> List[ResultSubmission]:
    """
    Return locked submissions that are verifier-ready.
    Excludes submissions that already have a finalized verification (passed/failed/review_required).
    """
    from sqlalchemy import select
    from app.models.verification import Verification
    
    # Submissions with completed verification
    finalized_sub_ids = (
        select(Verification.submission_id)
        .filter(Verification.status.in_(["passed", "failed", "review_required"]))
    )

    return (
        db.query(ResultSubmission)
        .filter(
            ResultSubmission.is_locked == True,
            ResultSubmission.status.in_(["submitted", "locked"]),
            ~ResultSubmission.id.in_(finalized_sub_ids),
        )
        .order_by(ResultSubmission.submitted_at.desc())
        .all()
    )




def get_submission_audit(db: Session, submission_id: int) -> List[SubmissionAuditLog]:
    return (
        db.query(SubmissionAuditLog)
        .filter(SubmissionAuditLog.submission_id == submission_id)
        .order_by(SubmissionAuditLog.created_at)
        .all()
    )
