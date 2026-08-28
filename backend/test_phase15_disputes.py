"""
Phase 15 — Dispute Resolution System Integration Tests
Tests cover:
  - Valid dispute creation on FAIL verification
  - Valid dispute creation on REJECT human review
  - Invalid outcome rejection (PASS / completed settlement)
  - Duplicate active dispute protection (409 Conflict)
  - Evidence submission and immutability
  - Mark ready for arbitration state transition
  - Dispute cancellation (reverts task status to failed)
  - Settlement eligibility blocked during active dispute
  - Financial safety: No AP Credits released
  - Query, listing, and audit log retrieval
"""
import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

# Path bootstrap
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from database import Base
from app.models.task import Task
from app.models.agent import Agent
from app.models.bid import Bid
from app.models.task_execution import TaskExecution, ExecutionLog
from app.models.result_submission import ResultSubmission, SubmissionAuditLog
from app.models.verification import Verification, VerificationAuditLog
from app.models.wallet import Wallet
from app.models.escrow import Escrow, EscrowAuditLog
from app.models.settlement import Settlement, SettlementAuditLog, LedgerEntry
from app.models.reputation import ReputationEvent
from app.models.human_review import HumanReview, HumanReviewAuditLog
from app.models.dispute import Dispute, DisputeEvidence, DisputeAuditLog

from app.services import dispute_service
from app.services import settlement_service

# In-memory SQLite for tests
TEST_DB_URL = "sqlite://"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=test_engine)

@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture()
def db():
    session = TestSession()
    try:
        yield session
    finally:
        session.close()

# Helpers
def _make_entities(db, verif_decision="FAIL", escrow_status="blocked", task_status="failed"):
    deadline = datetime.utcnow() + timedelta(days=7)
    task = Task(
        title="Dispute Test Task",
        description="Task to test Phase 15 disputes",
        category="Research",
        required_capability="research",
        reward=150.0,
        status=task_status,
        deadline=deadline,
        minimum_reputation=0,
        minimum_quality_score=85.0,
    )
    db.add(task)
    db.flush()

    worker = Agent(
        name="Worker-Dispute",
        agent_type="researcher",
        capabilities=json.dumps(["research"]),
        status="available",
        reputation_score=70.0,
    )
    verifier = Agent(
        name="Verifier-Dispute",
        agent_type="quality_checker",
        capabilities=json.dumps(["verification"]),
        status="available",
        reputation_score=85.0,
    )
    db.add_all([worker, verifier])
    db.flush()

    task.assigned_agent_id = worker.id

    req_wallet = Wallet(wallet_code="WL-REQ-1001", owner_type="requester", owner_id=0, available_balance=500.0, locked_balance=150.0)
    wrk_wallet = Wallet(wallet_code=f"WL-AGT-{worker.id}", owner_type="agent", owner_id=worker.id, available_balance=0.0)
    db.add_all([req_wallet, wrk_wallet])
    db.flush()

    verif = Verification(
        task_id=task.id,
        submission_id=1,
        worker_agent_id=worker.id,
        verifier_agent_id=verifier.id,
        decision=verif_decision,
        status="failed" if verif_decision == "FAIL" else ("passed" if verif_decision == "PASS" else "review_required"),
        overall_score=45.0 if verif_decision == "FAIL" else 90.0,
        required_score=85.0,
    )
    db.add(verif)
    db.flush()

    escrow = Escrow(
        escrow_code=f"ES-{1000 + task.id}",
        task_id=task.id,
        reward_amount=150.0,
        status=escrow_status,
        requester_wallet_id=req_wallet.id,
        worker_wallet_id=wrk_wallet.id,
        worker_agent_id=worker.id,
        verification_id=verif.id,
    )
    db.add(escrow)
    db.commit()

    return {
        "task": task,
        "worker": worker,
        "verifier": verifier,
        "verif": verif,
        "escrow": escrow,
        "req_wallet": req_wallet,
        "wrk_wallet": wrk_wallet,
    }


class TestCreateDispute:

    def test_creates_dispute_on_failed_verification(self, db):
        e = _make_entities(db, verif_decision="FAIL", escrow_status="blocked")
        dispute = dispute_service.create_dispute(
            db=db,
            task_id=e["task"].id,
            reason="unfair_verification",
            description="The verifier ignored the supplementary data appendix.",
            raised_by_type="worker",
            raised_by_id=str(e["worker"].id),
            initial_evidence_title="Appendix A",
            initial_evidence_description="Complete benchmark dataset provided.",
        )
        assert dispute.id is not None
        assert dispute.dispute_code.startswith("DP-")
        assert dispute.status == "open"
        assert dispute.task_id == e["task"].id
        assert dispute.worker_agent_id == e["worker"].id
        assert dispute.reason == "unfair_verification"

        # Check task transitioned to disputed
        db.refresh(e["task"])
        assert e["task"].status == "disputed"

        # Check escrow remains blocked
        db.refresh(e["escrow"])
        assert e["escrow"].status == "blocked"

        # Check evidence was recorded
        evidence_list = dispute_service.get_dispute_evidence_list(db, dispute.id)
        assert len(evidence_list) == 1
        assert evidence_list[0].title == "Appendix A"

        # Check audit trail
        logs = dispute_service.get_dispute_audit_logs(db, dispute.id)
        actions = [log.action for log in logs]
        assert "dispute_created" in actions
        assert "evidence_added" in actions

    def test_creates_dispute_on_rejected_human_review(self, db):
        e = _make_entities(db, verif_decision="REVIEW", escrow_status="blocked", task_status="verifying")
        review = HumanReview(
            task_id=e["task"].id,
            submission_id=1,
            verification_id=e["verif"].id,
            worker_agent_id=e["worker"].id,
            status="rejected",
            decision="REJECT",
            reviewer_note="Insufficient source citations.",
        )
        db.add(review)
        db.commit()

        dispute = dispute_service.create_dispute(
            db=db,
            task_id=e["task"].id,
            reason="rubric_misinterpretation",
            description="Citations were present in the bibliography section.",
        )
        assert dispute.id is not None
        assert dispute.status == "open"

    def test_rejects_dispute_for_successful_pass_outcome(self, db):
        e = _make_entities(db, verif_decision="PASS", escrow_status="released", task_status="completed")
        with pytest.raises(HTTPException) as exc:
            dispute_service.create_dispute(
                db=db,
                task_id=e["task"].id,
                reason="unfair_verification",
                description="Should fail",
            )
        assert exc.value.status_code == 400

    def test_rejects_dispute_for_completed_settlement(self, db):
        e = _make_entities(db, verif_decision="PASS", escrow_status="released", task_status="completed")
        settlement = Settlement(
            settlement_code="ST-1099",
            task_id=e["task"].id,
            escrow_id=e["escrow"].id,
            worker_agent_id=e["worker"].id,
            requester_wallet_id=e["req_wallet"].id,
            worker_wallet_id=e["wrk_wallet"].id,
            amount=150.0,
            status="completed",
        )
        db.add(settlement)
        db.commit()

        with pytest.raises(HTTPException) as exc:
            dispute_service.create_dispute(
                db=db,
                task_id=e["task"].id,
                reason="unfair_verification",
                description="Should fail",
            )
        assert exc.value.status_code == 400

    def test_rejects_duplicate_active_dispute(self, db):
        e = _make_entities(db, verif_decision="FAIL")
        dispute_service.create_dispute(
            db=db,
            task_id=e["task"].id,
            reason="first_dispute",
            description="First dispute details.",
        )
        db.commit()

        # Second creation should raise 409 Conflict
        with pytest.raises(HTTPException) as exc:
            dispute_service.create_dispute(
                db=db,
                task_id=e["task"].id,
                reason="second_dispute",
                description="Second dispute details.",
            )
        assert exc.value.status_code == 409


class TestEvidenceManagement:

    def test_append_evidence_to_open_dispute(self, db):
        e = _make_entities(db, verif_decision="FAIL")
        dispute = dispute_service.create_dispute(
            db=db,
            task_id=e["task"].id,
            reason="technical_error",
            description="Connection timed out during submission.",
        )
        db.commit()

        evidence = dispute_service.add_evidence(
            db=db,
            dispute_id=dispute.id,
            title="Server Access Logs",
            description="Log extract showing HTTP 200 responses from API.",
            evidence_data=json.dumps({"timestamp": "2026-08-28T12:00:00Z", "latency_ms": 120}),
            submitted_by_type="worker",
            submitted_by_id=str(e["worker"].id),
        )
        db.commit()

        assert evidence.id is not None
        assert evidence.title == "Server Access Logs"
        assert evidence.dispute_id == dispute.id

        items = dispute_service.get_dispute_evidence_list(db, dispute.id)
        assert len(items) == 1
        assert items[0].title == "Server Access Logs"

    def test_rejects_empty_evidence_title(self, db):
        e = _make_entities(db, verif_decision="FAIL")
        dispute = dispute_service.create_dispute(
            db=db,
            task_id=e["task"].id,
            reason="test_reason",
            description="test_description",
        )
        db.commit()

        with pytest.raises(HTTPException) as exc:
            dispute_service.add_evidence(
                db=db,
                dispute_id=dispute.id,
                title="",
                description="Valid description",
            )
        assert exc.value.status_code == 400

    def test_cannot_add_evidence_to_cancelled_dispute(self, db):
        e = _make_entities(db, verif_decision="FAIL")
        dispute = dispute_service.create_dispute(
            db=db,
            task_id=e["task"].id,
            reason="test_reason",
            description="test_description",
        )
        db.commit()

        dispute_service.cancel_dispute(db, dispute.id)
        db.commit()

        with pytest.raises(HTTPException) as exc:
            dispute_service.add_evidence(
                db=db,
                dispute_id=dispute.id,
                title="Late Evidence",
                description="Should fail",
            )
        assert exc.value.status_code == 400


class TestDisputeStateTransitions:

    def test_mark_ready_for_arbitration(self, db):
        e = _make_entities(db, verif_decision="FAIL")
        dispute = dispute_service.create_dispute(
            db=db,
            task_id=e["task"].id,
            reason="evidence_ignored",
            description="Evidence was not inspected.",
        )
        db.commit()

        updated = dispute_service.mark_ready_for_arbitration(db, dispute.id)
        db.commit()

        assert updated.status == "ready_for_arbitration"
        logs = dispute_service.get_dispute_audit_logs(db, dispute.id)
        assert any(log.action == "ready_for_arbitration" for log in logs)

    def test_cancel_dispute_reverts_task_status(self, db):
        e = _make_entities(db, verif_decision="FAIL")
        dispute = dispute_service.create_dispute(
            db=db,
            task_id=e["task"].id,
            reason="dispute_to_cancel",
            description="User decides to withdraw.",
        )
        db.commit()
        assert e["task"].status == "disputed"

        cancelled = dispute_service.cancel_dispute(db, dispute.id)
        db.commit()

        assert cancelled.status == "cancelled"
        assert cancelled.cancelled_at is not None

        db.refresh(e["task"])
        assert e["task"].status == "failed"

        logs = dispute_service.get_dispute_audit_logs(db, dispute.id)
        assert any(log.action == "dispute_cancelled" for log in logs)

    def test_cannot_cancel_already_cancelled_dispute(self, db):
        e = _make_entities(db, verif_decision="FAIL")
        dispute = dispute_service.create_dispute(
            db=db,
            task_id=e["task"].id,
            reason="double_cancel",
            description="Test",
        )
        db.commit()

        dispute_service.cancel_dispute(db, dispute.id)
        db.commit()

        with pytest.raises(HTTPException) as exc:
            dispute_service.cancel_dispute(db, dispute.id)
        assert exc.value.status_code == 400


class TestSettlementGuardsAndFinancialSafety:

    def test_settlement_blocked_when_dispute_is_active(self, db):
        e = _make_entities(db, verif_decision="FAIL", escrow_status="releasable")
        dispute = dispute_service.create_dispute(
            db=db,
            task_id=e["task"].id,
            reason="pause_settlement_test",
            description="Ensuring settlement is paused during dispute.",
        )
        db.commit()

        eligibility = settlement_service.check_settlement_eligibility(db, e["escrow"].id)
        assert eligibility["eligible"] is False
        assert "Active dispute" in eligibility["reason"]
        assert "paused" in eligibility["reason"]

    def test_financial_safety_no_ap_credits_transferred(self, db):
        e = _make_entities(db, verif_decision="FAIL")
        initial_req_balance = e["req_wallet"].available_balance
        initial_req_locked = e["req_wallet"].locked_balance
        initial_wrk_balance = e["wrk_wallet"].available_balance

        dispute = dispute_service.create_dispute(
            db=db,
            task_id=e["task"].id,
            reason="financial_safety_check",
            description="Testing balance conservation.",
        )
        db.commit()

        dispute_service.add_evidence(db, dispute.id, "Evidence 1", "Details")
        dispute_service.mark_ready_for_arbitration(db, dispute.id)
        db.commit()

        db.refresh(e["req_wallet"])
        db.refresh(e["wrk_wallet"])
        assert e["req_wallet"].available_balance == initial_req_balance
        assert e["req_wallet"].locked_balance == initial_req_locked
        assert e["wrk_wallet"].available_balance == initial_wrk_balance


class TestDisputeListingAndQueries:

    def test_list_disputes_with_filter(self, db):
        e = _make_entities(db, verif_decision="FAIL")
        d1 = dispute_service.create_dispute(db, e["task"].id, "r1", "d1")
        db.commit()

        all_disputes = dispute_service.list_disputes(db)
        assert len(all_disputes) >= 1

        open_disputes = dispute_service.list_disputes(db, status_filter="open")
        assert len(open_disputes) >= 1
        assert all(d.status == "open" for d in open_disputes)

        resolved_disputes = dispute_service.list_disputes(db, status_filter="resolved")
        assert len(resolved_disputes) == 0

    def test_get_dispute_by_task(self, db):
        e = _make_entities(db, verif_decision="FAIL")
        d = dispute_service.create_dispute(db, e["task"].id, "task_query", "desc")
        db.commit()

        found = dispute_service.get_dispute_by_task(db, e["task"].id)
        assert found is not None
        assert found.id == d.id
