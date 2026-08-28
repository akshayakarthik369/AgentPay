"""
Phase 9 — Comprehensive test suite for ResultSubmission, packaging, integrity, and audit.

Tests:
  - Full submission creation from completed execution
  - Submission code format (RS-NNNN)
  - All snapshot fields populated
  - Integrity hash generation and verification
  - Tamper detection
  - Snapshot independence (live changes don't affect frozen snapshot)
  - Duplicate submission → 409 Conflict
  - Incomplete execution rejected (running, failed)
  - Locked submission immutability
  - GET endpoints: by id, by code, task, agent, pending-verification
  - Integrity endpoint
  - Audit log events in correct order
  - Phase 5-8 regression (chain: task→match→bid→select→execute→complete→submit)
"""
import json
import sys
import os
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import app
from database import SessionLocal, engine, Base
from app.models.task import Task
from app.models.agent import Agent
from app.models.bid import Bid
from app.models.task_execution import TaskExecution, ExecutionLog
from app.models.result_submission import ResultSubmission, SubmissionAuditLog
from app.services import submission_service as svc

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)


@pytest.fixture(scope="function")
def db():
    session = SessionLocal()
    yield session
    session.close()


def _future(days=7):
    return (datetime.utcnow() + timedelta(days=days)).isoformat()


def _create_full_chain(client: TestClient) -> dict:
    """Helper: task → agent → bid → select → start → run."""
    # Create task
    task_resp = client.post("/api/tasks", json={
        "title": "Phase 9 Submission Test Task",
        "description": "Test task for result submission packaging and audit.",
        "category": "Research",
        "required_capability": "Research",
        "reward": 120.0,
        "deadline": _future(10),
        "minimum_reputation": 0,
        "minimum_quality_score": 0,
    })
    assert task_resp.status_code == 201, task_resp.text
    task = task_resp.json()

    # Create agent
    agent_resp = client.post("/api/agents", json={
        "name": f"Submission Tester {task['id']}",
        "agent_type": "worker",
        "description": "Agent for Phase 9 tests",
        "capabilities": ["Research", "Investigation"],
        "status": "available",
    })
    assert agent_resp.status_code == 201, agent_resp.text
    agent = agent_resp.json()

    # Place bid — route is POST /api/bids with task_id in body
    bid_resp = client.post("/api/bids", json={
        "task_id": task["id"],
        "agent_id": agent["id"],
        "bid_amount": 100.0,
        "estimated_completion_minutes": 30,
        "proposal": "I will research this thoroughly.",
    })
    assert bid_resp.status_code == 201, bid_resp.text
    bid = bid_resp.json()

    # Select winner — route is POST /api/tasks/{task_id}/select-bid/{bid_id}
    sel_resp = client.post(f"/api/tasks/{task['id']}/select-bid/{bid['id']}")
    assert sel_resp.status_code == 200, sel_resp.text

    # Start execution
    start_resp = client.post(f"/api/tasks/{task['id']}/execution/start")
    assert start_resp.status_code == 201, start_resp.text
    execution = start_resp.json()

    # Run executor
    run_resp = client.post(f"/api/executions/{execution['id']}/run")
    assert run_resp.status_code == 200, run_resp.text
    run_data = run_resp.json()
    assert run_data["status"] == "completed", f"Expected completed, got {run_data['status']}"

    return {
        "task": task,
        "agent": agent,
        "bid": bid,
        "execution": run_data,
    }


# ===========================================================================
# 1. Submission Creation
# ===========================================================================

class TestSubmissionCreation:
    def test_submit_creates_result_submission(self, client):
        """POST /api/executions/{id}/submit returns submission_id and submission_code."""
        chain = _create_full_chain(client)
        exec_id = chain["execution"]["id"]

        resp = client.post(f"/api/executions/{exec_id}/submit")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["submission_id"] is not None
        assert data["submission_code"] is not None
        assert data["submission_code"].startswith("RS-")
        assert data["execution_status"] == "submitted"
        assert data["task_status"] == "submitted"

    def test_submission_code_format(self, client):
        """Submission code must be RS-NNNN."""
        chain = _create_full_chain(client)
        resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        code = resp.json()["submission_code"]
        assert code.startswith("RS-")
        numeric_part = code.split("-")[1]
        assert numeric_part.isdigit()
        assert int(numeric_part) >= 1001

    def test_submission_detail_has_all_snapshots(self, client):
        """GET /api/submissions/{id} returns all 4 frozen snapshots."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        assert detail["task_snapshot"] is not None
        assert detail["agent_snapshot"] is not None
        assert detail["bid_snapshot"] is not None
        assert detail["execution_snapshot"] is not None

    def test_task_snapshot_fields(self, client):
        """Task snapshot contains expected fields."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        ts = detail["task_snapshot"]
        assert "task_code" in ts
        assert "title" in ts
        assert "required_capability" in ts
        assert "reward" in ts
        assert ts["title"] == chain["task"]["title"]

    def test_agent_snapshot_fields(self, client):
        """Agent snapshot contains reputation_score at submission time."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        a_snap = detail["agent_snapshot"]
        assert "agent_code" in a_snap
        assert "name" in a_snap
        assert "reputation_score" in a_snap
        assert "capabilities" in a_snap

    def test_bid_snapshot_fields(self, client):
        """Bid snapshot contains bid_amount and match_score_snapshot."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        b_snap = detail["bid_snapshot"]
        assert "bid_code" in b_snap
        assert "bid_amount" in b_snap
        assert "match_score_snapshot" in b_snap

    def test_execution_snapshot_fields(self, client):
        """Execution snapshot contains provider and progress."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        e_snap = detail["execution_snapshot"]
        assert "execution_code" in e_snap
        assert "provider" in e_snap
        assert "status_at_submission" in e_snap

    def test_output_text_present(self, client):
        """output_text is populated from the completed execution."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        assert detail["output_text"] is not None
        assert len(detail["output_text"]) > 10

    def test_structured_output_present(self, client):
        """structured_output is parsed JSON (not raw string)."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        so = detail["structured_output"]
        assert so is not None
        assert isinstance(so, dict)

    def test_evidence_present(self, client):
        """evidence field exists and contains source info."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        ev = detail["evidence"]
        assert ev is not None
        assert "source" in ev or "derived_from" in ev

    def test_provenance_no_external_sources(self, client):
        """Provenance correctly reports no external data was used."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        prov = detail["provenance"]
        assert prov is not None
        assert prov.get("external_dataset_used") == False
        assert prov.get("external_sources_used") == False

    def test_self_assessment_present(self, client):
        """self_assessment contains confidence and independently_verified=False."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        sa = detail["self_assessment"]
        assert sa is not None
        assert "confidence" in sa
        assert sa.get("independently_verified") == False
        assert sa.get("assessment_type") == "worker_self_assessment"

    def test_limitations_present(self, client):
        """limitations is a non-empty list."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        lims = detail["limitations"]
        assert isinstance(lims, list)
        assert len(lims) > 0

    def test_result_summary_present(self, client):
        """result_summary is a non-empty string."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        assert detail["result_summary"]
        assert len(detail["result_summary"]) > 5


# ===========================================================================
# 2. Integrity
# ===========================================================================

class TestIntegrity:
    def test_integrity_hash_sha256_prefix(self, client):
        """integrity_hash starts with 'sha256:'."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        assert detail["integrity_hash"].startswith("sha256:")

    def test_integrity_endpoint_valid(self, client):
        """GET /api/submissions/{id}/integrity returns valid=True after creation."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        integ = client.get(f"/api/submissions/{sub_id}/integrity").json()
        assert integ["valid"] == True
        assert integ["algorithm"] == "SHA-256"
        assert integ["verification_ready"] == True

    def test_tamper_detection(self, db):
        """Modifying stored output_text causes integrity verification to fail."""
        # Create a submission directly in DB for tamper test
        task = Task(
            title="Tamper Test Task",
            description="For tamper detection test",
            category="Data Analysis",
            required_capability="Data Analysis",
            reward=50.0,
            deadline=datetime.utcnow() + timedelta(days=5),
        )
        db.add(task)
        db.flush()

        agent = Agent(
            name=f"Tamper Agent {task.id}",
            agent_type="worker",
            capabilities=["Data Analysis"],
        )
        db.add(agent)
        db.flush()

        bid = Bid(
            task_id=task.id,
            agent_id=agent.id,
            bid_amount=40.0,
            estimated_completion_minutes=20,
            proposal="Tamper test bid",
            match_score_snapshot=0.8,
            reputation_snapshot=80,
            selection_score=0.85,
            status="accepted",
        )
        db.add(bid)
        db.flush()

        execution = TaskExecution(
            task_id=task.id,
            agent_id=agent.id,
            bid_id=bid.id,
            status="completed",
            progress=100,
            output_text="Original output for tamper test.",
            structured_output=json.dumps({"summary": "Original summary", "findings": []}),
            execution_metadata=json.dumps({"provider": "local_deterministic", "executor_type": "data"}),
            started_at=datetime.utcnow() - timedelta(minutes=5),
            completed_at=datetime.utcnow(),
        )
        db.add(execution)
        db.commit()

        # Assign for submission
        task.assigned_agent_id = agent.id
        task.selected_bid_id = bid.id
        task.status = "assigned"
        db.commit()

        # Create submission
        submission = svc.create_submission_from_execution(db, execution.id)

        # Verify integrity is valid before tamper
        result_before = svc.verify_submission_integrity(submission)
        assert result_before["valid"] == True

        # Tamper: modify output_text directly
        original_output = submission.output_text
        submission.output_text = "TAMPERED OUTPUT — this should break the hash."
        db.commit()

        # Re-verify: must be invalid
        db.refresh(submission)
        result_after = svc.verify_submission_integrity(submission)
        assert result_after["valid"] == False

        # Restore for cleanup
        submission.output_text = original_output
        db.commit()

    def test_snapshot_independence_task(self, client, db):
        """Changing live task fields does not affect frozen task_snapshot."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        # Get original snapshot title
        detail = client.get(f"/api/submissions/{sub_id}").json()
        original_title = detail["task_snapshot"]["title"]

        # Modify live task title directly in DB
        task = db.query(Task).filter(Task.id == chain["task"]["id"]).first()
        task.title = "CHANGED TITLE — should not affect snapshot"
        db.commit()

        # Snapshot must still have original title
        detail2 = client.get(f"/api/submissions/{sub_id}").json()
        assert detail2["task_snapshot"]["title"] == original_title

    def test_snapshot_independence_agent(self, client, db):
        """Changing live agent reputation does not affect frozen agent_snapshot."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        snap_reputation = detail["agent_snapshot"]["reputation_score"]

        # Change live agent reputation
        agent = db.query(Agent).filter(Agent.id == chain["agent"]["id"]).first()
        agent.reputation_score = 999
        db.commit()

        # Snapshot must still have original value
        detail2 = client.get(f"/api/submissions/{sub_id}").json()
        assert detail2["agent_snapshot"]["reputation_score"] == snap_reputation


# ===========================================================================
# 3. Guards and Locking
# ===========================================================================

class TestGuardsAndLocking:
    def test_duplicate_submission_returns_409(self, client):
        """Submitting the same completed execution twice returns 409."""
        chain = _create_full_chain(client)
        exec_id = chain["execution"]["id"]

        # First submission
        resp1 = client.post(f"/api/executions/{exec_id}/submit")
        assert resp1.status_code == 200

        # Second attempt
        resp2 = client.post(f"/api/executions/{exec_id}/submit")
        assert resp2.status_code == 409

    def test_submit_running_execution_rejected(self, client):
        """Cannot submit an execution that is still running."""
        chain = _create_full_chain(client)
        exec_id = chain["execution"]["id"]

        # Manually set execution back to running (simulate)
        db = SessionLocal()
        try:
            exc = db.query(TaskExecution).filter(TaskExecution.id == exec_id).first()
            exc.status = "running"
            db.commit()
        finally:
            db.close()

        resp = client.post(f"/api/executions/{exec_id}/submit")
        assert resp.status_code == 400
        assert "completed" in resp.json()["detail"].lower()

    def test_submit_failed_execution_rejected(self, client):
        """Cannot submit an execution that has failed."""
        chain = _create_full_chain(client)
        exec_id = chain["execution"]["id"]

        # Manually set execution to failed
        db = SessionLocal()
        try:
            exc = db.query(TaskExecution).filter(TaskExecution.id == exec_id).first()
            exc.status = "failed"
            db.commit()
        finally:
            db.close()

        resp = client.post(f"/api/executions/{exec_id}/submit")
        assert resp.status_code == 400

    def test_submission_is_locked_after_creation(self, client):
        """Submission must have is_locked=True and status='locked'."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        assert detail["is_locked"] == True
        assert detail["status"] == "locked"

    def test_verification_ready_true(self, client):
        """verification_ready must be True for a properly locked submission."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        detail = client.get(f"/api/submissions/{sub_id}").json()
        assert detail["verification_ready"] == True


# ===========================================================================
# 4. Query Endpoints
# ===========================================================================

class TestQueryEndpoints:
    def test_get_submission_by_id(self, client):
        """GET /api/submissions/{id} returns 200 with full detail."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        resp = client.get(f"/api/submissions/{sub_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == sub_id

    def test_get_submission_by_id_not_found(self, client):
        """GET /api/submissions/999999 returns 404."""
        resp = client.get("/api/submissions/999999")
        assert resp.status_code == 404

    def test_get_submission_by_code(self, client):
        """GET /api/submissions/code/RS-NNNN returns submission."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        data = sub_resp.json()
        code = data["submission_code"]
        sub_id = data["submission_id"]

        resp = client.get(f"/api/submissions/code/{code}")
        assert resp.status_code == 200
        assert resp.json()["id"] == sub_id

    def test_get_task_submission(self, client):
        """GET /api/tasks/{task_id}/submission returns submission for task."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        resp = client.get(f"/api/tasks/{chain['task']['id']}/submission")
        assert resp.status_code == 200
        assert resp.json()["id"] == sub_id
        assert resp.json()["task_id"] == chain["task"]["id"]

    def test_get_task_submission_not_found(self, client):
        """GET /api/tasks/{id}/submission returns 404 if no submission."""
        # Create a task but don't submit anything
        task_resp = client.post("/api/tasks", json={
            "title": "No Submission Task",
            "description": "This task has no submission",
            "category": "Research",
            "required_capability": "Research",
            "reward": 50.0,
            "deadline": _future(5),
        })
        task_id = task_resp.json()["id"]
        resp = client.get(f"/api/tasks/{task_id}/submission")
        assert resp.status_code == 404

    def test_get_agent_submissions(self, client):
        """GET /api/agents/{id}/submissions returns list including this submission."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        resp = client.get(f"/api/agents/{chain['agent']['id']}/submissions")
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert sub_id in ids

    def test_pending_verification_list(self, client):
        """GET /api/submissions/pending-verification returns locked submissions."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        resp = client.get("/api/submissions/pending-verification")
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()]
        assert sub_id in ids

    def test_pending_verification_all_locked(self, client):
        """All items in pending-verification must have verification_ready=True."""
        resp = client.get("/api/submissions/pending-verification")
        for item in resp.json():
            assert item["verification_ready"] == True


# ===========================================================================
# 5. Audit Log
# ===========================================================================

class TestAuditLog:
    def test_audit_log_exists(self, client):
        """GET /api/submissions/{id}/audit returns non-empty list."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        resp = client.get(f"/api/submissions/{sub_id}/audit")
        assert resp.status_code == 200
        assert len(resp.json()) >= 4

    def test_audit_events_order_and_content(self, client):
        """Audit log must contain the 4 expected events in order."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        logs = client.get(f"/api/submissions/{sub_id}/audit").json()
        actions = [l["action"] for l in logs]

        assert "submission_created" in actions
        assert "snapshots_frozen" in actions
        assert "integrity_hash_generated" in actions
        assert "submission_locked" in actions

        # Check ordering: created first, locked last
        idx_created = actions.index("submission_created")
        idx_locked = actions.index("submission_locked")
        assert idx_created < idx_locked

    def test_audit_actor_types(self, client):
        """submission_created uses worker_agent; others use system."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        logs = client.get(f"/api/submissions/{sub_id}/audit").json()
        by_action = {l["action"]: l for l in logs}

        assert by_action["submission_created"]["actor_type"] == "worker_agent"
        assert by_action["snapshots_frozen"]["actor_type"] == "system"
        assert by_action["integrity_hash_generated"]["actor_type"] == "system"
        assert by_action["submission_locked"]["actor_type"] == "system"


# ===========================================================================
# 6. Regression — complete Phase 5-8 chain
# ===========================================================================

class TestEndToEndChain:
    def test_full_chain_task_to_submission(self, client):
        """Full chain: create task → bid → select → start → run → submit."""
        chain = _create_full_chain(client)

        # Submit the completed execution
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        assert sub_resp.status_code == 200, sub_resp.text

        # Verify task is 'submitted'
        task_resp = client.get(f"/api/tasks/{chain['task']['id']}")
        assert task_resp.status_code == 200
        assert task_resp.json()["status"] == "submitted"

        # Verify execution is 'submitted'
        exec_resp = client.get(f"/api/executions/{chain['execution']['id']}")
        assert exec_resp.status_code == 200
        assert exec_resp.json()["status"] == "submitted"


    def test_agent_submissions_after_submission(self, client):
        """Agent has at least one submission after completing chain."""
        chain = _create_full_chain(client)
        client.post(f"/api/executions/{chain['execution']['id']}/submit")

        subs = client.get(f"/api/agents/{chain['agent']['id']}/submissions").json()
        assert len(subs) >= 1
        assert subs[0]["status"] == "locked"

    def test_submission_has_no_reputation_change(self, client, db):
        """Agent reputation_score must not change after submission (Phase 10 only)."""
        chain = _create_full_chain(client)
        agent_before = client.get(f"/api/agents/{chain['agent']['id']}").json()
        rep_before = agent_before["reputation_score"]

        client.post(f"/api/executions/{chain['execution']['id']}/submit")

        agent_after = client.get(f"/api/agents/{chain['agent']['id']}").json()
        assert agent_after["reputation_score"] == rep_before

    def test_submission_has_no_payment(self, client):
        """Agent wallet_balance must not change after submission (Phase 10+ only)."""
        chain = _create_full_chain(client)
        agent_before = client.get(f"/api/agents/{chain['agent']['id']}").json()
        wallet_before = agent_before["wallet_balance"]

        client.post(f"/api/executions/{chain['execution']['id']}/submit")

        agent_after = client.get(f"/api/agents/{chain['agent']['id']}").json()
        assert agent_after["wallet_balance"] == wallet_before

    def test_agent_remains_busy_after_submission(self, client):
        """Worker agent must remain 'busy' after submission (not reset to available)."""
        chain = _create_full_chain(client)
        client.post(f"/api/executions/{chain['execution']['id']}/submit")

        agent = client.get(f"/api/agents/{chain['agent']['id']}").json()
        assert agent["status"] == "busy"

    def test_task_endpoint_returns_submitted_status(self, client):
        """GET /api/tasks/{id} shows 'submitted' after result package created."""
        chain = _create_full_chain(client)
        client.post(f"/api/executions/{chain['execution']['id']}/submit")

        task = client.get(f"/api/tasks/{chain['task']['id']}").json()
        assert task["status"] == "submitted"

    def test_task_submission_endpoint_returns_detail(self, client):
        """GET /api/tasks/{id}/submission returns full submission detail."""
        chain = _create_full_chain(client)
        sub_resp = client.post(f"/api/executions/{chain['execution']['id']}/submit")
        sub_id = sub_resp.json()["submission_id"]

        resp = client.get(f"/api/tasks/{chain['task']['id']}/submission")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["id"] == sub_id
        assert detail["verification_ready"] == True
        assert detail["integrity_hash"].startswith("sha256:")
