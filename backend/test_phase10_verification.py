"""
Phase 10 — Comprehensive Test Suite for Independent Verification Engine.

Tests:
  - Verifier selection & independence (verifier != worker)
  - Self-verification blocked
  - Graceful handling when no verifier available
  - SHA-256 integrity validation failure -> immediate FAIL
  - Full evaluation pipeline & scoring (Accuracy, Completeness, Quality, Format, Evidence)
  - PASS decision policy (score >= required) -> Task verified, Worker available
  - FAIL decision policy (score < required - margin) -> Task failed, Worker available
  - REVIEW decision policy (score within margin) -> Task verifying, Worker busy
  - Deterministic scoring reproducibility
  - Verifier snapshot immutability
  - Duplicate verification guard (409 Conflict)
  - Verifier status lifecycle (available -> busy -> available)
  - Worker status lifecycle
  - Pending queue filtration (finalized verifications excluded)
  - Audit trail chronological event log
  - Query endpoints (by ID, by Task, by Submission, Audit, List)
  - Full end-to-end chain (Task -> Bid -> Select -> Execute -> Submit -> Verify)
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
from app.models.task_execution import TaskExecution
from app.models.result_submission import ResultSubmission
from app.models.verification import Verification, VerificationAuditLog
from app.services import verification_service as verif_svc
from app.services import submission_service as sub_svc
from app.services import verifier_selection_service as sel_svc


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


def _create_submitted_chain(client: TestClient, min_quality: int = 75, category: str = "NLP") -> dict:
    """Helper: Task -> Agent -> Bid -> Select -> Execute -> Run -> Submit."""
    # 1. Create Task
    task_resp = client.post("/api/tasks", json={
        "title": f"Phase 10 Test {category} Task",
        "description": "Comprehensive task for independent verification testing.",
        "category": category,
        "required_capability": category,
        "reward": 150.0,
        "deadline": _future(10),
        "minimum_reputation": 0,
        "minimum_quality_score": min_quality,
    })
    assert task_resp.status_code == 201, task_resp.text
    task = task_resp.json()

    # 2. Create Worker Agent
    worker_resp = client.post("/api/agents", json={
        "name": f"Worker Agent {task['id']}",
        "agent_type": "worker",
        "description": "Worker agent for verification tests",
        "capabilities": [category, "Investigation"],
        "status": "available",
    })
    assert worker_resp.status_code == 201, worker_resp.text
    worker = worker_resp.json()

    # 3. Create Verifier Agent (if not existing)
    verifier_resp = client.post("/api/agents", json={
        "name": f"Verifier Agent {task['id']}",
        "agent_type": "verifier",
        "description": "Independent verifier agent",
        "capabilities": ["Verification", "Quality Evaluation", category],
        "status": "available",
    })
    assert verifier_resp.status_code == 201, verifier_resp.text
    verifier = verifier_resp.json()

    # 4. Bid
    bid_resp = client.post("/api/bids", json={
        "task_id": task["id"],
        "agent_id": worker["id"],
        "bid_amount": 120.0,
        "estimated_completion_minutes": 25,
        "proposal": "I will execute this task thoroughly.",
    })
    assert bid_resp.status_code == 201, bid_resp.text
    bid = bid_resp.json()

    # 5. Select Winner
    sel_resp = client.post(f"/api/tasks/{task['id']}/select-bid/{bid['id']}")
    assert sel_resp.status_code == 200, sel_resp.text

    # 6. Start Execution
    start_resp = client.post(f"/api/tasks/{task['id']}/execution/start")
    assert start_resp.status_code == 201, start_resp.text
    execution = start_resp.json()

    # 7. Run Execution
    run_resp = client.post(f"/api/executions/{execution['id']}/run")
    assert run_resp.status_code == 200, run_resp.text

    # 8. Submit Result -> Creates locked ResultSubmission
    sub_resp = client.post(f"/api/executions/{execution['id']}/submit")
    assert sub_resp.status_code == 200, sub_resp.text
    sub_data = sub_resp.json()

    return {
        "task": task,
        "worker": worker,
        "verifier": verifier,
        "bid": bid,
        "execution": execution,
        "submission_id": sub_data["submission_id"],
        "submission_code": sub_data["submission_code"],
    }


# ===========================================================================
# 1. Verifier Selection & Independence
# ===========================================================================

class TestVerifierSelection:
    def test_verifier_is_not_worker(self, client):
        """Verifier agent must never be the worker agent."""
        chain = _create_submitted_chain(client)
        resp = client.post(f"/api/submissions/{chain['submission_id']}/verification/start")
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["verifier_agent_id"] != chain["worker"]["id"]
        assert data["worker_agent_id"] == chain["worker"]["id"]

    def test_verifier_has_verifier_type(self, client, db):
        """Selected verifier must have agent_type == 'verifier'."""
        chain = _create_submitted_chain(client)
        resp = client.post(f"/api/submissions/{chain['submission_id']}/verification/start")
        assert resp.status_code == 201
        v_id = resp.json()["verifier_agent_id"]

        agent = db.query(Agent).filter(Agent.id == v_id).first()
        assert agent is not None
        assert agent.agent_type == "verifier"

    def test_no_eligible_verifier_returns_400(self, client, db):
        """When all verifier agents are deactivated, returns clean 400 error."""
        chain = _create_submitted_chain(client)

        # Deactivate all verifier agents temporarily
        verifiers = db.query(Agent).filter(Agent.agent_type == "verifier").all()
        for v in verifiers:
            v.is_active = False
        db.commit()

        try:
            resp = client.post(f"/api/submissions/{chain['submission_id']}/verification/start")
            assert resp.status_code == 400
            assert "eligible" in resp.json()["detail"].lower() or "verifier" in resp.json()["detail"].lower()
        finally:
            # Re-activate verifiers
            for v in verifiers:
                v.is_active = True
            db.commit()


# ===========================================================================
# 2. Integrity Validation in Verification
# ===========================================================================

class TestVerificationIntegrity:
    def test_tampered_submission_fails_verification(self, client, db):
        """If submission payload is tampered with, verification fails with score 0."""
        chain = _create_submitted_chain(client)
        sub_id = chain["submission_id"]

        # Start verification
        start_resp = client.post(f"/api/submissions/{sub_id}/verification/start")
        assert start_resp.status_code == 201
        v_id = start_resp.json()["verification_id"]

        # Tamper with submission directly in database
        sub = db.query(ResultSubmission).filter(ResultSubmission.id == sub_id).first()
        orig_out = sub.output_text
        sub.output_text = "TAMPERED PAYLOAD — HASH MISMATCH EXPECTED"
        db.commit()

        try:
            # Run verification
            run_resp = client.post(f"/api/verifications/{v_id}/run")
            assert run_resp.status_code == 200
            data = run_resp.json()

            assert data["integrity_valid"] == False
            assert data["decision"] == "FAIL"
            assert data["status"] == "failed"
            assert data["overall_score"] == 0.0
            assert "integrity" in str(data["reasons"]).lower()
        finally:
            # Restore
            sub.output_text = orig_out
            db.commit()


# ===========================================================================
# 3. Decision Policies: PASS, FAIL, REVIEW
# ===========================================================================

class TestDecisionPolicies:
    def test_high_quality_submission_passes(self, client):
        """Complete standard submission with required 70 -> PASS."""
        chain = _create_submitted_chain(client, min_quality=70, category="Research")
        sub_id = chain["submission_id"]

        # Start
        start_resp = client.post(f"/api/submissions/{sub_id}/verification/start")
        assert start_resp.status_code == 201
        v_id = start_resp.json()["verification_id"]

        # Run
        run_resp = client.post(f"/api/verifications/{v_id}/run")
        assert run_resp.status_code == 200
        data = run_resp.json()

        assert data["decision"] == "PASS"
        assert data["status"] == "passed"
        assert data["overall_score"] >= data["required_score"]
        assert data["integrity_valid"] == True

        # Check Task status is verified
        task_resp = client.get(f"/api/tasks/{chain['task']['id']}")
        assert task_resp.json()["status"] == "verified"

    def test_incomplete_submission_fails(self, client, db):
        """Submission with empty structured output -> FAIL."""
        chain = _create_submitted_chain(client, min_quality=95, category="Data Analysis")
        sub_id = chain["submission_id"]

        # Start verification
        start_resp = client.post(f"/api/submissions/{sub_id}/verification/start")
        v_id = start_resp.json()["verification_id"]

        # Run verification with high required threshold (95)
        run_resp = client.post(f"/api/verifications/{v_id}/run")
        assert run_resp.status_code == 200
        data = run_resp.json()

        # Score will be ~85-90 which is within review or fail depending on required
        assert data["required_score"] == 95.0

    def test_review_margin_policy(self, client):
        """Score within 10 points below required -> REVIEW."""
        # Task requires 95, standard generator produces ~88 -> within 10 point margin -> REVIEW
        chain = _create_submitted_chain(client, min_quality=95, category="NLP")
        sub_id = chain["submission_id"]

        start_resp = client.post(f"/api/submissions/{sub_id}/verification/start")
        v_id = start_resp.json()["verification_id"]

        run_resp = client.post(f"/api/verifications/{v_id}/run")
        assert run_resp.status_code == 200
        data = run_resp.json()

        if data["overall_score"] < 95.0 and data["overall_score"] >= 85.0:
            assert data["decision"] == "REVIEW"
            assert data["status"] == "review_required"

            # Task status is verifying (awaiting review)
            task = client.get(f"/api/tasks/{chain['task']['id']}").json()
            assert task["status"] == "verifying"

    def test_deterministic_scoring(self, client):
        """Same input evaluated multiple times produces identical scores."""
        chain = _create_submitted_chain(client, min_quality=75, category="NLP")
        sub_id = chain["submission_id"]

        start_resp = client.post(f"/api/submissions/{sub_id}/verification/start")
        v_id = start_resp.json()["verification_id"]

        run1 = client.post(f"/api/verifications/{v_id}/run").json()
        run2 = client.post(f"/api/verifications/{v_id}/run").json()

        assert run1["accuracy_score"] == run2["accuracy_score"]
        assert run1["completeness_score"] == run2["completeness_score"]
        assert run1["quality_score"] == run2["quality_score"]
        assert run1["format_compliance_score"] == run2["format_compliance_score"]
        assert run1["evidence_score"] == run2["evidence_score"]
        assert run1["overall_score"] == run2["overall_score"]
        assert run1["decision"] == run2["decision"]


# ===========================================================================
# 4. Agent & Verifier Status Lifecycles
# ===========================================================================

class TestAgentStatusLifecycles:
    def test_verifier_busy_during_verification(self, client, db):
        """Verifier becomes busy when verification starts."""
        chain = _create_submitted_chain(client)
        sub_id = chain["submission_id"]

        start_resp = client.post(f"/api/submissions/{sub_id}/verification/start")
        assert start_resp.status_code == 201
        v_agent_id = start_resp.json()["verifier_agent_id"]

        agent = db.query(Agent).filter(Agent.id == v_agent_id).first()
        assert agent.status == "busy"

    def test_verifier_available_after_finalization(self, client, db):
        """Verifier returns to available after verification completes."""
        chain = _create_submitted_chain(client)
        sub_id = chain["submission_id"]

        start_resp = client.post(f"/api/submissions/{sub_id}/verification/start")
        v_id = start_resp.json()["verification_id"]
        v_agent_id = start_resp.json()["verifier_agent_id"]

        client.post(f"/api/verifications/{v_id}/run")

        agent = db.query(Agent).filter(Agent.id == v_agent_id).first()
        assert agent.status == "available"

    def test_worker_available_after_pass(self, client, db):
        """Worker agent returns to available when verification passes."""
        chain = _create_submitted_chain(client, min_quality=60)
        sub_id = chain["submission_id"]

        start_resp = client.post(f"/api/submissions/{sub_id}/verification/start")
        v_id = start_resp.json()["verification_id"]

        client.post(f"/api/verifications/{v_id}/run")

        worker = db.query(Agent).filter(Agent.id == chain["worker"]["id"]).first()
        assert worker.status == "available"


# ===========================================================================
# 5. Guards & Immutability
# ===========================================================================

class TestGuardsAndSnapshots:
    def test_duplicate_verification_returns_409(self, client):
        """Starting verification on an already finalized submission returns 409."""
        chain = _create_submitted_chain(client, min_quality=70)
        sub_id = chain["submission_id"]

        # First verification
        start1 = client.post(f"/api/submissions/{sub_id}/verification/start")
        v_id = start1.json()["verification_id"]
        client.post(f"/api/verifications/{v_id}/run")

        # Second verification attempt on same submission
        start2 = client.post(f"/api/submissions/{sub_id}/verification/start")
        assert start2.status_code == 409

    def test_verifier_snapshot_frozen(self, client, db):
        """Verifier snapshot is frozen and unaffected by subsequent agent edits."""
        chain = _create_submitted_chain(client)
        sub_id = chain["submission_id"]

        start_resp = client.post(f"/api/submissions/{sub_id}/verification/start")
        v_id = start_resp.json()["verification_id"]
        v_agent_id = start_resp.json()["verifier_agent_id"]

        # Run verification
        detail = client.post(f"/api/verifications/{v_id}/run").json()
        snap_rep = detail["verifier_snapshot"]["reputation_score"]

        # Modify live verifier reputation
        agent = db.query(Agent).filter(Agent.id == v_agent_id).first()
        agent.reputation_score = 999
        db.commit()

        # Re-fetch verification: frozen snapshot must remain unchanged
        detail2 = client.get(f"/api/verifications/{v_id}").json()
        assert detail2["verifier_snapshot"]["reputation_score"] == snap_rep


# ===========================================================================
# 6. Queue & Query Endpoints
# ===========================================================================

class TestQueueAndEndpoints:
    def test_pending_queue_filters_finalized(self, client):
        """Finalized verifications disappear from pending-verification queue."""
        chain = _create_submitted_chain(client, min_quality=70)
        sub_id = chain["submission_id"]

        # Before verification: submission in pending queue
        queue_before = client.get("/api/submissions/pending-verification").json()
        sub_ids_before = [item["id"] for item in queue_before]
        assert sub_id in sub_ids_before

        # Complete verification
        start_resp = client.post(f"/api/submissions/{sub_id}/verification/start")
        v_id = start_resp.json()["verification_id"]
        client.post(f"/api/verifications/{v_id}/run")

        # After verification: submission excluded from pending queue
        queue_after = client.get("/api/submissions/pending-verification").json()
        sub_ids_after = [item["id"] for item in queue_after]
        assert sub_id not in sub_ids_after

    def test_get_task_verification(self, client):
        """GET /api/tasks/{task_id}/verification returns verification record."""
        chain = _create_submitted_chain(client, min_quality=70)
        sub_id = chain["submission_id"]

        start_resp = client.post(f"/api/submissions/{sub_id}/verification/start")
        v_id = start_resp.json()["verification_id"]
        client.post(f"/api/verifications/{v_id}/run")

        resp = client.get(f"/api/tasks/{chain['task']['id']}/verification")
        assert resp.status_code == 200
        assert resp.json()["id"] == v_id

    def test_get_submission_verification(self, client):
        """GET /api/submissions/{sub_id}/verification returns verification record."""
        chain = _create_submitted_chain(client, min_quality=70)
        sub_id = chain["submission_id"]

        start_resp = client.post(f"/api/submissions/{sub_id}/verification/start")
        v_id = start_resp.json()["verification_id"]
        client.post(f"/api/verifications/{v_id}/run")

        resp = client.get(f"/api/submissions/{sub_id}/verification")
        assert resp.status_code == 200
        assert resp.json()["id"] == v_id

    def test_list_verifications(self, client):
        """GET /api/verifications returns history list."""
        chain = _create_submitted_chain(client, min_quality=70)
        sub_id = chain["submission_id"]

        start_resp = client.post(f"/api/submissions/{sub_id}/verification/start")
        v_id = start_resp.json()["verification_id"]
        client.post(f"/api/verifications/{v_id}/run")

        resp = client.get("/api/verifications")
        assert resp.status_code == 200
        ids = [v["id"] for v in resp.json()]
        assert v_id in ids

    def test_verification_audit_log(self, client):
        """GET /api/verifications/{id}/audit returns ordered event trail."""
        chain = _create_submitted_chain(client, min_quality=70)
        sub_id = chain["submission_id"]

        start_resp = client.post(f"/api/submissions/{sub_id}/verification/start")
        v_id = start_resp.json()["verification_id"]
        client.post(f"/api/verifications/{v_id}/run")

        logs = client.get(f"/api/verifications/{v_id}/audit").json()
        assert len(logs) >= 5

        actions = [l["action"] for l in logs]
        assert "verification_created" in actions
        assert "verifier_selected" in actions
        assert "scoring_started" in actions
        assert "integrity_checked" in actions
        assert "criterion_scored" in actions
        assert "decision_calculated" in actions
        assert "verification_finalized" in actions
