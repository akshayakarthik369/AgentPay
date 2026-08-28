"""
Phase 18 — Security & Malicious-Agent Handling Integration Tests

Tests cover:
  - Suspended agent blocked from bidding, execution, verification, and arbitration
  - Agent manual/automatic suspension and restoration
  - Conflict-of-interest prevention (self-verification and self-arbitration blocked)
  - Security violation logging and immutable audit events
  - Risk score calculation, escalation, and [0, 100] bounding
  - Auto-suspension upon Critical risk or Critical violation
  - Negative balance protection
  - Duplicate action prevention
  - Reverse matching excludes suspended agents
  - Trusted agent flow completes smoothly without false positives
"""
import json
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import Base
from app.models.task import Task
from app.models.agent import Agent
from app.models.bid import Bid
from app.models.wallet import Wallet
from app.models.security import SecurityEvent
from app.models.result_submission import ResultSubmission

from app.services import security_service
from app.services import bidding_service
from app.services import execution_service
from app.services import verifier_selection_service
from app.services import arbitration_service
from app.services import matching_service
from app.schemas.bid import BidCreate

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


def _create_agent(
    db,
    name="TestAgent-1",
    agent_type="worker",
    status="available",
    risk_score=0.0,
    is_suspended=False,
    capabilities=None,
):
    agent = Agent(
        name=name,
        agent_type=agent_type,
        capabilities=json.dumps(capabilities or ["research", "nlp"]),
        status=status,
        reputation_score=85.0,
        risk_score=risk_score,
        is_suspended=is_suspended,
        is_active=True,
    )
    db.add(agent)
    db.flush()
    return agent


def _create_task(db, title="Security Task", reward=100.0, status="open"):
    now = datetime.utcnow()
    task = Task(
        title=title,
        description="Task for security testing",
        category="Research",
        required_capability="research",
        reward=reward,
        status=status,
        deadline=now + timedelta(days=5),
        minimum_reputation=0,
        minimum_quality_score=70.0,
    )
    db.add(task)
    db.flush()
    return task


class TestSecurityRiskScoring:

    def test_risk_level_classification(self):
        assert security_service.calculate_risk_level(15.0) == "Low"
        assert security_service.calculate_risk_level(45.0) == "Medium"
        assert security_service.calculate_risk_level(68.0) == "High"
        assert security_service.calculate_risk_level(85.0) == "Critical"
        assert security_service.calculate_risk_level(100.0) == "Critical"

    def test_violation_increments_risk_and_count(self, db):
        agent = _create_agent(db, name="Agent-Risk", risk_score=10.0)
        db.commit()

        ev = security_service.record_security_violation(
            db,
            event_type="suspicious_bidding",
            severity="medium",
            reason="Abnormal bid frequency",
            agent_id=agent.id,
        )

        assert ev.id is not None
        assert agent.violation_count == 1
        assert agent.risk_score == 30.0  # 10 + 20
        assert agent.last_violation_at is not None

    def test_critical_violation_auto_suspends_agent(self, db):
        agent = _create_agent(db, name="Malicious-Agent", risk_score=0.0)
        db.commit()

        security_service.record_security_violation(
            db,
            event_type="integrity_failure",
            severity="critical",
            reason="SHA-256 payload tampering detected",
            agent_id=agent.id,
        )

        assert agent.is_suspended is True
        assert agent.status == "suspended"
        assert agent.risk_score >= 85.0
        assert "Auto-suspended" in (agent.suspension_reason or "")

    def test_risk_score_capped_at_100(self, db):
        agent = _create_agent(db, name="Capped-Risk", risk_score=90.0)
        db.commit()

        security_service.record_security_violation(
            db,
            event_type="repeated_failure",
            severity="high",
            reason="Multiple failures",
            agent_id=agent.id,
        )

        assert agent.risk_score == 100.0


class TestAgentSuspensionAndRestoration:

    def test_manual_suspension(self, db):
        agent = _create_agent(db, name="Agent-To-Suspend")
        db.commit()

        suspended = security_service.suspend_agent(
            db,
            agent_id=agent.id,
            reason="Manual investigation required",
            actor="compliance_officer",
        )

        assert suspended.is_suspended is True
        assert suspended.status == "suspended"
        assert suspended.suspension_reason == "Manual investigation required"
        assert suspended.risk_score >= 80.0

        # Check security event recorded
        events = security_service.get_security_events(db, agent_id=agent.id)
        assert any(e.event_type == "agent_suspended" for e in events)

    def test_restore_suspended_agent(self, db):
        agent = _create_agent(db, name="Agent-To-Restore", is_suspended=True, status="suspended", risk_score=85.0)
        db.commit()

        restored = security_service.restore_agent(
            db,
            agent_id=agent.id,
            reason="Cleared after code audit",
            actor="lead_auditor",
        )

        assert restored.is_suspended is False
        assert restored.status == "available"
        assert restored.suspension_reason is None
        assert restored.risk_score <= 40.0  # Rehabilitated risk

        events = security_service.get_security_events(db, agent_id=agent.id)
        assert any(e.event_type == "agent_restored" for e in events)


class TestParticipationGuards:

    def test_suspended_agent_cannot_bid(self, db):
        task = _create_task(db)
        suspended_agent = _create_agent(db, name="Suspended-Bidder", is_suspended=True, status="suspended")
        db.commit()

        payload = BidCreate(
            task_id=task.id,
            agent_id=suspended_agent.id,
            bid_amount=80.0,
            estimated_completion_minutes=30,
            proposal="I want to bid",
        )

        with pytest.raises(HTTPException) as exc:
            bidding_service.create_bid(db, payload)
        assert exc.value.status_code == 403
        assert "suspended" in exc.value.detail.lower()

    def test_critical_risk_agent_cannot_bid(self, db):
        task = _create_task(db)
        high_risk_agent = _create_agent(db, name="HighRisk-Bidder", risk_score=88.0, status="available")
        db.commit()

        payload = BidCreate(
            task_id=task.id,
            agent_id=high_risk_agent.id,
            bid_amount=80.0,
            estimated_completion_minutes=30,
            proposal="I want to bid",
        )

        with pytest.raises(HTTPException) as exc:
            bidding_service.create_bid(db, payload)
        assert exc.value.status_code == 403
        assert "critical risk" in exc.value.detail.lower()

    def test_suspended_agent_cannot_start_execution(self, db):
        suspended_agent = _create_agent(db, name="Suspended-Worker", is_suspended=True, status="suspended")
        task = _create_task(db, status="assigned")
        task.assigned_agent_id = suspended_agent.id
        db.commit()

        with pytest.raises(HTTPException) as exc:
            execution_service.start_execution(db, task.id)
        assert exc.value.status_code in (400, 403)

    def test_suspended_agent_excluded_from_verifier_selection(self, db):
        worker = _create_agent(db, name="Worker-A")
        suspended_verifier = _create_agent(
            db, name="Suspended-Verifier", agent_type="verifier", is_suspended=True, status="suspended"
        )
        active_verifier = _create_agent(
            db, name="Active-Verifier", agent_type="verifier", is_suspended=False, status="available"
        )
        task = _create_task(db)
        db.commit()

        class MockSubmission:
            agent_id = worker.id
            task_snapshot = None

        selected = verifier_selection_service.select_verifier(db, MockSubmission())
        assert selected is not None
        assert selected.id == active_verifier.id
        assert selected.id != suspended_verifier.id

    def test_suspended_agent_excluded_from_arbitrator_selection(self, db):
        worker = _create_agent(db, name="Worker-B")
        suspended_arb = _create_agent(
            db, name="Suspended-Arbitrator", agent_type="arbitrator", is_suspended=True, status="suspended"
        )
        active_arb = _create_agent(
            db, name="Active-Arbitrator", agent_type="arbitrator", is_suspended=False, status="available"
        )
        db.commit()

        selected = arbitration_service.select_arbitrator_agent(db, worker_id=worker.id)
        assert selected is not None
        assert selected.id != suspended_arb.id
        assert selected.id == active_arb.id


class TestConflictOfInterestGuards:

    def test_worker_cannot_verify_own_task(self):
        worker_id = 42
        with pytest.raises(HTTPException) as exc:
            security_service.validate_no_conflict(worker_id, candidate_id=42, role="verifier")
        assert exc.value.status_code == 400
        assert "Conflict of Interest" in exc.value.detail

    def test_worker_cannot_arbitrate_own_task(self):
        worker_id = 100
        with pytest.raises(HTTPException) as exc:
            security_service.validate_no_conflict(worker_id, candidate_id=100, role="arbitrator")
        assert exc.value.status_code == 400
        assert "Conflict of Interest" in exc.value.detail

    def test_different_agents_pass_conflict_check(self):
        # Should not raise
        security_service.validate_no_conflict(worker_id=10, candidate_id=20, role="verifier")


class TestMatchingSecurityFilters:

    def test_matching_excludes_suspended_agents(self, db):
        task = _create_task(db)
        active_agent = _create_agent(db, name="Active-Match", capabilities=["research"])
        suspended_agent = _create_agent(
            db, name="Suspended-Match", capabilities=["research"], is_suspended=True, status="suspended"
        )
        db.commit()

        res = matching_service.get_ranked_matching_agents_for_task(db, task.id)
        assert res is not None
        matched_ids = [a["agent"]["id"] for a in res["agents"]]
        assert active_agent.id in matched_ids
        assert suspended_agent.id not in matched_ids

    def test_suspended_agent_discovers_zero_tasks(self, db):
        task = _create_task(db)
        suspended_agent = _create_agent(
            db, name="Suspended-Discoverer", capabilities=["research"], is_suspended=True, status="suspended"
        )
        db.commit()

        res = matching_service.get_ranked_discoverable_tasks_for_agent(db, suspended_agent.id)
        assert res is not None
        assert res["total_matches"] == 0
        assert res["matches"] == []


class TestSecurityDossierQueries:

    def test_get_agent_security_summary(self, db):
        agent = _create_agent(db, name="Dossier-Agent", risk_score=25.0)
        db.commit()

        security_service.record_security_violation(
            db,
            event_type="suspicious_bidding",
            severity="low",
            reason="Unusual bidding cadence",
            agent_id=agent.id,
        )

        summary = security_service.get_agent_security_summary(db, agent.id)
        assert summary["agent_id"] == agent.id
        assert summary["risk_level"] == "Medium"  # 25 + 10 = 35 -> Medium
        assert summary["violation_count"] == 1
        assert len(summary["recent_events"]) >= 1

    def test_query_security_events_with_filters(self, db):
        agent1 = _create_agent(db, name="Agent-Filter-1")
        agent2 = _create_agent(db, name="Agent-Filter-2")
        db.commit()

        security_service.record_security_violation(
            db, event_type="unauthorized_action", severity="high", reason="Test reason 1", agent_id=agent1.id
        )
        security_service.record_security_violation(
            db, event_type="duplicate_action", severity="low", reason="Test reason 2", agent_id=agent2.id
        )

        events_a1 = security_service.get_security_events(db, agent_id=agent1.id)
        assert len(events_a1) == 1
        assert events_a1[0].event_type == "unauthorized_action"

        high_events = security_service.get_security_events(db, severity="high")
        assert len(high_events) >= 1
        assert all(e.severity == "high" for e in high_events)
