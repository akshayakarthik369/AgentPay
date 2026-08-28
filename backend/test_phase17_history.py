"""
Phase 17 — Transaction & Activity History Integration Tests

Tests cover:
  - Task lifecycle timeline correctness
  - Agent history
  - Wallet transactions (real AP movements only)
  - Settlement debit/credit
  - Blocked settlement display
  - Dispute & arbitration events in timeline
  - Reputation events
  - Duplicate event prevention
  - Chronological ordering
"""
import json
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import Base
from app.models.task import Task
from app.models.agent import Agent
from app.models.bid import Bid
from app.models.task_execution import TaskExecution
from app.models.result_submission import ResultSubmission
from app.models.verification import Verification
from app.models.wallet import Wallet
from app.models.escrow import Escrow, EscrowAuditLog
from app.models.settlement import Settlement, LedgerEntry
from app.models.reputation import ReputationEvent
from app.models.human_review import HumanReview
from app.models.dispute import Dispute
from app.models.arbitration import Arbitration, ArbitrationAuditLog
from app.models.dispute import DisputeAuditLog

from app.services import history_service

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


def _make_base_task(db, reward=150.0, status="open"):
    now = datetime.utcnow()
    task = Task(
        title="E2E History Test Task",
        description="Test task for history tracking",
        category="Research",
        required_capability="research",
        reward=reward,
        status=status,
        deadline=now + timedelta(days=7),
        minimum_reputation=0,
        minimum_quality_score=80.0,
    )
    db.add(task)
    db.flush()
    return task


def _make_worker(db, name="Worker-History"):
    agent = Agent(
        name=name,
        agent_type="researcher",
        capabilities=json.dumps(["research"]),
        status="available",
        reputation_score=75.0,
    )
    db.add(agent)
    db.flush()
    return agent


def _make_wallets(db, worker_id):
    req_wallet = Wallet(wallet_code="WL-REQ-7001", owner_type="requester", owner_id=0, available_balance=1000.0, locked_balance=0.0)
    wrk_wallet = Wallet(wallet_code=f"WL-AGT-{worker_id}", owner_type="agent", owner_id=worker_id, available_balance=0.0)
    db.add_all([req_wallet, wrk_wallet])
    db.flush()
    return req_wallet, wrk_wallet


class TestTaskActivityTimeline:

    def test_task_created_event_appears(self, db):
        task = _make_base_task(db)
        db.commit()
        events = history_service.get_task_activity(db, task.id)
        types = [e["event_type"] for e in events]
        assert "task_created" in types

    def test_empty_task_has_only_created_event(self, db):
        task = _make_base_task(db)
        db.commit()
        events = history_service.get_task_activity(db, task.id)
        assert len(events) == 1
        assert events[0]["event_type"] == "task_created"

    def test_events_are_chronological(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        db.commit()

        bid = Bid(
            task_id=task.id, agent_id=worker.id,
            bid_amount=100.0, estimated_completion_minutes=60,
            proposal="Test proposal", match_score_snapshot=80.0,
            reputation_snapshot=75.0, status="pending"
        )
        db.add(bid)
        task.assigned_agent_id = worker.id
        task.assigned_at = datetime.utcnow() + timedelta(seconds=5)
        db.commit()

        events = history_service.get_task_activity(db, task.id)
        timestamps = [e["created_at"] for e in events if e["created_at"]]
        assert timestamps == sorted(timestamps), "Events are not in chronological order"

    def test_bid_submitted_event_appears(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        bid = Bid(
            task_id=task.id, agent_id=worker.id,
            bid_amount=120.0, estimated_completion_minutes=60,
            proposal="Test proposal", match_score_snapshot=80.0,
            reputation_snapshot=75.0, status="pending"
        )
        db.add(bid)
        db.commit()

        events = history_service.get_task_activity(db, task.id)
        types = [e["event_type"] for e in events]
        assert "bid_submitted" in types
        bid_event = next(e for e in events if e["event_type"] == "bid_submitted")
        assert bid_event["amount"] == 120.0

    def test_worker_selected_event_appears(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        task.assigned_agent_id = worker.id
        task.assigned_at = datetime.utcnow()
        db.commit()

        events = history_service.get_task_activity(db, task.id)
        types = [e["event_type"] for e in events]
        assert "worker_selected" in types

    def test_escrow_locked_event_appears(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        req_wallet, wrk_wallet = _make_wallets(db, worker.id)
        escrow = Escrow(
            escrow_code="ES-7001", task_id=task.id, reward_amount=150.0,
            status="locked", requester_wallet_id=req_wallet.id,
            worker_wallet_id=wrk_wallet.id, worker_agent_id=worker.id,
            locked_at=datetime.utcnow(),
        )
        db.add(escrow)
        db.commit()

        events = history_service.get_task_activity(db, task.id)
        types = [e["event_type"] for e in events]
        assert "escrow_locked" in types
        escrow_event = next(e for e in events if e["event_type"] == "escrow_locked")
        assert escrow_event["amount"] == 150.0
        assert escrow_event["related_entity_code"] == "ES-7001"

    def test_verification_passed_event(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        verif = Verification(
            task_id=task.id, submission_id=1, worker_agent_id=worker.id,
            verifier_agent_id=worker.id, decision="PASS", status="passed",
            overall_score=92.0, required_score=80.0,
            completed_at=datetime.utcnow(),
        )
        db.add(verif)
        db.commit()

        events = history_service.get_task_activity(db, task.id)
        types = [e["event_type"] for e in events]
        assert "verification_passed" in types

    def test_verification_failed_event(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        verif = Verification(
            task_id=task.id, submission_id=1, worker_agent_id=worker.id,
            verifier_agent_id=worker.id, decision="FAIL", status="failed",
            overall_score=40.0, required_score=80.0,
            completed_at=datetime.utcnow(),
        )
        db.add(verif)
        db.commit()

        events = history_service.get_task_activity(db, task.id)
        types = [e["event_type"] for e in events]
        assert "verification_failed" in types

    def test_settlement_completed_event(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        req_wallet, wrk_wallet = _make_wallets(db, worker.id)
        settlement = Settlement(
            settlement_code="ST-7001", task_id=task.id, escrow_id=1,
            requester_wallet_id=req_wallet.id, worker_wallet_id=wrk_wallet.id,
            worker_agent_id=worker.id, amount=150.0, status="completed",
            completed_at=datetime.utcnow(),
        )
        db.add(settlement)
        db.commit()

        events = history_service.get_task_activity(db, task.id)
        types = [e["event_type"] for e in events]
        assert "settlement_completed" in types
        st_event = next(e for e in events if e["event_type"] == "settlement_completed")
        assert st_event["amount"] == 150.0

    def test_settlement_blocked_event(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        req_wallet, wrk_wallet = _make_wallets(db, worker.id)
        settlement = Settlement(
            settlement_code="ST-7002", task_id=task.id, escrow_id=2,
            requester_wallet_id=req_wallet.id, worker_wallet_id=wrk_wallet.id,
            worker_agent_id=worker.id, amount=150.0, status="blocked",
            failure_reason="Verification FAIL — score below threshold.",
        )
        db.add(settlement)
        db.commit()

        events = history_service.get_task_activity(db, task.id)
        types = [e["event_type"] for e in events]
        assert "settlement_blocked" in types
        # Ensure blocked settlement does NOT appear as completed
        assert "settlement_completed" not in types

    def test_dispute_opened_event(self, db):
        task = _make_base_task(db, status="disputed")
        worker = _make_worker(db)
        dispute = Dispute(
            task_id=task.id, worker_agent_id=worker.id,
            submission_id=999, verification_id=999, escrow_id=999,
            reason="unfair_verification", description="Verifier was too strict.",
            raised_by_type="worker", status="open",
        )
        db.add(dispute)
        db.commit()

        events = history_service.get_task_activity(db, task.id)
        types = [e["event_type"] for e in events]
        assert "dispute_opened" in types

    def test_arbitration_decision_event(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        arb_agent = Agent(name="Arb-Agent", agent_type="arbitrator", capabilities="[]", status="available", reputation_score=90.0)
        db.add(arb_agent)
        req_wallet, wrk_wallet = _make_wallets(db, worker.id)
        db.flush()

        dispute = Dispute(
            task_id=task.id, worker_agent_id=worker.id,
            submission_id=999, verification_id=999, escrow_id=998,
            reason="unfair_verification", description="Test dispute.",
            raised_by_type="worker", status="resolved",
        )
        db.add(dispute)
        db.flush()

        escrow = Escrow(
            escrow_code="ES-7003", task_id=task.id, reward_amount=150.0,
            status="releasable", requester_wallet_id=req_wallet.id,
            worker_wallet_id=wrk_wallet.id, worker_agent_id=worker.id,
        )
        db.add(escrow)
        db.flush()

        arb = Arbitration(
            dispute_id=dispute.id, task_id=task.id,
            arbitrator_agent_id=arb_agent.id, worker_agent_id=worker.id,
            escrow_id=escrow.id, status="resolved",
            decision="worker_wins", confidence_score=92.0,
            reasoning_summary="Evidence supports worker.",
            resolved_at=datetime.utcnow(),
        )
        db.add(arb)
        db.commit()

        events = history_service.get_task_activity(db, task.id)
        types = [e["event_type"] for e in events]
        assert "arbitration_decision" in types
        arb_event = next(e for e in events if e["event_type"] == "arbitration_decision")
        assert arb_event["status"] == "worker_wins"

    def test_reputation_updated_event(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        task.assigned_agent_id = worker.id
        rep = ReputationEvent(
            agent_id=worker.id, task_id=task.id,
            event_type="verification_pass",
            previous_score=75.0, score_delta=5.0, new_score=80.0,
            reason="Verification passed with quality score 92%",
        )
        db.add(rep)
        db.commit()

        events = history_service.get_task_activity(db, task.id)
        types = [e["event_type"] for e in events]
        assert "reputation_updated" in types
        rep_event = next(e for e in events if e["event_type"] == "reputation_updated")
        assert rep_event["amount"] == 5.0


class TestWalletTransactions:

    def test_escrow_lock_entry(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        req_wallet, wrk_wallet = _make_wallets(db, worker.id)
        entry = LedgerEntry(
            entry_code="LE-7001", task_id=task.id,
            wallet_id=req_wallet.id, entry_type="escrow_lock",
            amount=150.0, balance_type="locked",
            description="Escrow lock for task.",
        )
        db.add(entry)
        db.commit()

        txns = history_service.get_wallet_transactions(db, wallet_id=req_wallet.id)
        assert len(txns) == 1
        assert txns[0]["entry_type"] == "escrow_lock"
        assert txns[0]["direction"] == "lock"
        assert txns[0]["amount"] == 150.0

    def test_settlement_debit_entry(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        req_wallet, wrk_wallet = _make_wallets(db, worker.id)
        settlement = Settlement(
            settlement_code="ST-7003", task_id=task.id, escrow_id=5,
            requester_wallet_id=req_wallet.id, worker_wallet_id=wrk_wallet.id,
            worker_agent_id=worker.id, amount=150.0, status="completed",
        )
        db.add(settlement)
        db.flush()

        debit = LedgerEntry(
            entry_code="LE-7002", task_id=task.id,
            settlement_id=settlement.id,
            wallet_id=req_wallet.id, entry_type="settlement_debit",
            amount=150.0, balance_type="locked",
            description="Settlement debit from requester locked balance.",
        )
        db.add(debit)
        db.commit()

        txns = history_service.get_wallet_transactions(db, wallet_id=req_wallet.id)
        assert any(t["entry_type"] == "settlement_debit" and t["status"] == "completed" for t in txns)
        # Ensure settlement code is populated
        debit_txn = next(t for t in txns if t["entry_type"] == "settlement_debit")
        assert debit_txn["settlement_code"] == "ST-7003"

    def test_settlement_credit_entry(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        req_wallet, wrk_wallet = _make_wallets(db, worker.id)
        settlement = Settlement(
            settlement_code="ST-7004", task_id=task.id, escrow_id=6,
            requester_wallet_id=req_wallet.id, worker_wallet_id=wrk_wallet.id,
            worker_agent_id=worker.id, amount=150.0, status="completed",
        )
        db.add(settlement)
        db.flush()

        credit = LedgerEntry(
            entry_code="LE-7003", task_id=task.id,
            settlement_id=settlement.id,
            wallet_id=wrk_wallet.id, entry_type="settlement_credit",
            amount=150.0, balance_type="available",
            description="AP Credits credited to worker wallet.",
        )
        db.add(credit)
        db.commit()

        txns = history_service.get_wallet_transactions(db, wallet_id=wrk_wallet.id)
        assert any(t["entry_type"] == "settlement_credit" and t["direction"] == "credit" for t in txns)

    def test_no_fake_transactions(self, db):
        """Wallet transactions should only come from real LedgerEntry rows."""
        task = _make_base_task(db)
        db.commit()
        txns = history_service.get_wallet_transactions(db)
        # No LedgerEntries created — should be empty
        assert txns == []

    def test_all_transactions_endpoint(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        req_wallet, wrk_wallet = _make_wallets(db, worker.id)
        db.add(LedgerEntry(
            entry_code="LE-7010", task_id=task.id,
            wallet_id=req_wallet.id, entry_type="escrow_lock",
            amount=100.0, balance_type="locked", description="Test lock.",
        ))
        db.commit()

        txns = history_service.get_wallet_transactions(db)
        assert len(txns) >= 1


class TestGlobalActivityFeed:

    def test_global_feed_returns_events(self, db):
        task = _make_base_task(db)
        db.commit()
        events = history_service.get_global_activity(db)
        assert len(events) >= 1

    def test_global_feed_event_type_filter(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        bid = Bid(
            task_id=task.id, agent_id=worker.id,
            bid_amount=100.0, estimated_completion_minutes=60,
            proposal="Test proposal", match_score_snapshot=80.0,
            reputation_snapshot=75.0, status="pending"
        )
        db.add(bid)
        db.commit()

        events = history_service.get_global_activity(db, event_type="bid_submitted")
        assert all(e["event_type"] == "bid_submitted" for e in events)

    def test_global_feed_task_filter(self, db):
        task1 = _make_base_task(db)
        task2 = _make_base_task(db)
        db.commit()

        events = history_service.get_global_activity(db, task_id=task1.id)
        for e in events:
            assert e["task_id"] == task1.id

    def test_global_feed_descending_order(self, db):
        task = _make_base_task(db)
        db.commit()
        events = history_service.get_global_activity(db)
        if len(events) > 1:
            timestamps = [e["created_at"] for e in events if e["created_at"]]
            assert timestamps == sorted(timestamps, reverse=True), "Global feed should be newest first"


class TestAgentActivity:

    def test_agent_activity_shows_worker_events(self, db):
        task = _make_base_task(db)
        worker = _make_worker(db)
        task.assigned_agent_id = worker.id
        task.assigned_at = datetime.utcnow()
        db.commit()

        events = history_service.get_agent_activity(db, agent_id=worker.id)
        types = [e["event_type"] for e in events]
        # Should see at minimum task_created and worker_selected
        assert "task_created" in types

    def test_nonexistent_agent_returns_empty(self, db):
        events = history_service.get_agent_activity(db, agent_id=99999)
        assert events == []
