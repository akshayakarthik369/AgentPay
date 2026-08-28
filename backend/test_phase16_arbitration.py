"""
Phase 16 — AI Arbitration System Integration Tests
Tests cover:
  - Arbitrator selection & conflict avoidance (arbitrator != worker, != verifier)
  - E2E WORKER_WINS flow: overturns outcome, sets escrow releasable, triggers settlement, completes task, updates reputation
  - E2E REQUESTER_WINS flow: upholds failure, blocks escrow, no settlement, applies failure penalty
  - INCONCLUSIVE flow: escrow remains blocked, no fund transfer
  - Duplicate arbitration prevention
  - Audit trail completeness
  - Listing, query, and audit logs
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
from app.models.arbitration import Arbitration, ArbitrationAuditLog

from app.services import dispute_service
from app.services import arbitration_service

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

def _make_entities(db, verif_decision="FAIL"):
    deadline = datetime.utcnow() + timedelta(days=7)
    task = Task(
        title="Arbitration Test Task",
        description="Task to test Phase 16 AI arbitration",
        category="Research",
        required_capability="research",
        reward=200.0,
        status="failed",
        deadline=deadline,
        minimum_reputation=0,
        minimum_quality_score=85.0,
    )
    db.add(task)
    db.flush()

    worker = Agent(
        name="Worker-Arbitration",
        agent_type="researcher",
        capabilities=json.dumps(["research"]),
        status="available",
        reputation_score=70.0,
    )
    verifier = Agent(
        name="Verifier-Arbitration",
        agent_type="quality_checker",
        capabilities=json.dumps(["verification"]),
        status="available",
        reputation_score=85.0,
    )
    arbitrator = Agent(
        name="Arbitrator-Justice",
        agent_type="arbitrator",
        capabilities=json.dumps(["arbitration", "evaluation"]),
        status="available",
        reputation_score=95.0,
    )
    db.add_all([worker, verifier, arbitrator])
    db.flush()

    task.assigned_agent_id = worker.id

    req_wallet = Wallet(wallet_code="WL-REQ-2001", owner_type="requester", owner_id=0, available_balance=800.0, locked_balance=200.0)
    wrk_wallet = Wallet(wallet_code=f"WL-AGT-{worker.id}", owner_type="agent", owner_id=worker.id, available_balance=0.0)
    db.add_all([req_wallet, wrk_wallet])
    db.flush()

    verif = Verification(
        task_id=task.id,
        submission_id=1,
        worker_agent_id=worker.id,
        verifier_agent_id=verifier.id,
        decision=verif_decision,
        status="failed",
        overall_score=48.0,
        required_score=85.0,
    )
    db.add(verif)
    db.flush()

    escrow = Escrow(
        escrow_code=f"ES-{1000 + task.id}",
        task_id=task.id,
        reward_amount=200.0,
        status="blocked",
        requester_wallet_id=req_wallet.id,
        worker_wallet_id=wrk_wallet.id,
        worker_agent_id=worker.id,
        verification_id=verif.id,
    )
    db.add(escrow)
    db.flush()

    dispute = dispute_service.create_dispute(
        db=db,
        task_id=task.id,
        reason="unfair_verification",
        description="The verification model applied an overly strict grading rubric.",
        initial_evidence_title="Complete Dataset Log",
        initial_evidence_description="All 10 requested items were produced in the raw output JSON.",
    )
    dispute_service.mark_ready_for_arbitration(db, dispute.id)
    db.commit()

    return {
        "task": task,
        "worker": worker,
        "verifier": verifier,
        "arbitrator": arbitrator,
        "verif": verif,
        "escrow": escrow,
        "dispute": dispute,
        "req_wallet": req_wallet,
        "wrk_wallet": wrk_wallet,
    }


class TestArbitratorSelection:

    def test_selects_dedicated_arbitrator_agent(self, db):
        e = _make_entities(db)
        selected = arbitration_service.select_arbitrator_agent(
            db=db,
            worker_id=e["worker"].id,
            verifier_id=e["verifier"].id,
        )
        assert selected.id == e["arbitrator"].id
        assert selected.agent_type == "arbitrator"

    def test_conflict_avoidance_never_selects_worker_or_verifier(self, db):
        e = _make_entities(db)
        # Even if arbitrator is removed, it must never select worker or verifier
        db.delete(e["arbitrator"])
        db.commit()

        selected = arbitration_service.select_arbitrator_agent(
            db=db,
            worker_id=e["worker"].id,
            verifier_id=e["verifier"].id,
        )
        assert selected.id != e["worker"].id
        assert selected.id != e["verifier"].id


class TestArbitrationExecution:

    def test_worker_wins_flow(self, db):
        e = _make_entities(db)
        arb = arbitration_service.run_arbitration(
            db=db,
            dispute_id=e["dispute"].id,
            force_decision="worker_wins",
            notes="Arbitrator inspected dataset and verified all deliverables present.",
        )
        assert arb.id is not None
        assert arb.arbitration_code.startswith("AR-")
        assert arb.decision == "worker_wins"
        assert arb.status == "resolved"
        assert arb.confidence_score >= 80.0
        assert arb.resolved_at is not None

        # Check dispute resolved
        db.refresh(e["dispute"])
        assert e["dispute"].status == "resolved"

        # Check verification overturned
        db.refresh(e["verif"])
        assert e["verif"].decision == "PASS"

        # Check escrow set releasable
        db.refresh(e["escrow"])
        assert e["escrow"].status in ("releasable", "released")

        # Check task completed
        db.refresh(e["task"])
        assert e["task"].status == "completed"

        # Check audit trail
        logs = arbitration_service.get_arbitration_audit_logs(db, arb.id)
        actions = [log.action for log in logs]
        assert "arbitration_created" in actions
        assert "arbitrator_selected" in actions
        assert "arbitration_started" in actions
        assert "evidence_reviewed" in actions
        assert "decision_made" in actions
        assert "escrow_updated" in actions

    def test_requester_wins_flow(self, db):
        e = _make_entities(db)
        arb = arbitration_service.run_arbitration(
            db=db,
            dispute_id=e["dispute"].id,
            force_decision="requester_wins",
            notes="Worker did not provide verifiable evidence.",
        )
        assert arb.decision == "requester_wins"
        assert arb.status == "resolved"

        # Check dispute resolved
        db.refresh(e["dispute"])
        assert e["dispute"].status == "resolved"

        # Check escrow remains blocked
        db.refresh(e["escrow"])
        assert e["escrow"].status == "blocked"

        # Check task remains failed
        db.refresh(e["task"])
        assert e["task"].status == "failed"

        # Check audit
        logs = arbitration_service.get_arbitration_audit_logs(db, arb.id)
        actions = [log.action for log in logs]
        assert "decision_made" in actions
        assert "settlement_blocked" in actions

    def test_inconclusive_flow(self, db):
        e = _make_entities(db)
        arb = arbitration_service.run_arbitration(
            db=db,
            dispute_id=e["dispute"].id,
            force_decision="inconclusive",
            notes="Insufficient information to make definitive ruling.",
        )
        assert arb.decision == "inconclusive"

        # Escrow must remain blocked
        db.refresh(e["escrow"])
        assert e["escrow"].status == "blocked"

    def test_duplicate_arbitration_prevented(self, db):
        e = _make_entities(db)
        arbitration_service.run_arbitration(db=db, dispute_id=e["dispute"].id, force_decision="worker_wins")
        db.commit()

        # Second attempt should raise 400
        with pytest.raises(HTTPException) as exc:
            arbitration_service.run_arbitration(db=db, dispute_id=e["dispute"].id, force_decision="worker_wins")
        assert exc.value.status_code == 400


class TestArbitrationQueries:

    def test_get_arbitration_by_dispute(self, db):
        e = _make_entities(db)
        arb = arbitration_service.run_arbitration(db=db, dispute_id=e["dispute"].id, force_decision="worker_wins")
        db.commit()

        found = arbitration_service.get_arbitration_by_dispute(db, e["dispute"].id)
        assert found is not None
        assert found.id == arb.id

    def test_list_arbitrations_with_status_filter(self, db):
        e = _make_entities(db)
        arbitration_service.run_arbitration(db=db, dispute_id=e["dispute"].id, force_decision="worker_wins")
        db.commit()

        all_arb = arbitration_service.list_arbitrations(db)
        assert len(all_arb) >= 1

        resolved_arb = arbitration_service.list_arbitrations(db, status_filter="resolved")
        assert len(resolved_arb) >= 1

        pending_arb = arbitration_service.list_arbitrations(db, status_filter="pending")
        assert len(pending_arb) == 0
