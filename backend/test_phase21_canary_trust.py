"""
Phase 21 Test Suite: Canary Testing & Trust Lifecycle System

Verifies:
  1. Agent Registration & 'pending_canary' initialization
  2. Autonomous Canary Benchmark runner & sub-checks (Integrity, Policy, Execution)
  3. Failure handling & transition to 'canary_failed'
  4. Bidding gate blocking for unverified agents (pending_canary, canary_failed)
  5. Canary PASS transition to 'provisional' tier
  6. Provisional 200 AP reward limit enforcement
  7. Automatic promotion to 'trusted' tier upon milestone completion (3 verified tasks, 70+ rep)
  8. Unlocked high-reward bidding for 'trusted' agents
  9. Maximum retry threshold (5 attempts) & auto-suspension
  10. Comprehensive Trust Report generation
"""
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base

from app.models import Agent, Task, Bid, CanaryTest, ResultSubmission, TaskExecution
from app.services import (
    agent_service, task_service, bidding_service, canary_service,
    execution_service, submission_service, verification_service,
    settlement_service, wallet_service
)
from app.schemas.agent import AgentCreate
from app.schemas.task import TaskCreate
from app.schemas.bid import BidCreate
from app.config.trust import (
    TRUST_STATUS_PENDING_CANARY,
    TRUST_STATUS_PROVISIONAL,
    TRUST_STATUS_TRUSTED,
    TRUST_STATUS_CANARY_FAILED,
    TRUST_STATUS_SUSPENDED,
    PROVISIONAL_MAX_REWARD,
)

# Setup isolated in-memory SQLite DB
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_test_db():
    Base.metadata.create_all(bind=engine)
    return TestingSessionLocal()


def run_tests():
    print("\n" + "="*70)
    print("=== AGENTPAY PHASE 21 - CANARY TESTING & TRUST LIFECYCLE SUITE ===")
    print("="*70)

    db = get_test_db()
    passed = 0
    failed = 0

    def assert_test(condition, name):
        nonlocal passed, failed
        if condition:
            print(f"  [PASS] {name}")
            passed += 1
        else:
            print(f"  [FAIL] {name}")
            failed += 1

    try:
        # -------------------------------------------------------------
        # STEP 1: Agent Registration & Pending Canary State
        # -------------------------------------------------------------
        print("\n--- [Step 1] Agent Registration & Trust State Initialization ---")
        agent_name = f"Canary-Test-Agent-{uuid.uuid4().hex[:6]}"
        agent = agent_service.create_agent(db, AgentCreate(
            name=agent_name,
            agent_type="worker",
            description="Autonomous Natural Language Processing specialist.",
            capabilities=["NLP", "Text Classification"],
        ))

        assert_test(agent.trust_status == TRUST_STATUS_PENDING_CANARY, 
                    f"New agent '{agent.name}' initialized in '{TRUST_STATUS_PENDING_CANARY}' trust status")
        assert_test(agent.is_provisional is True, "Agent marked as provisional")

        # Initialize wallet
        requester_wallet = wallet_service.get_or_create_requester_wallet(db, seed_amount=5000.0)
        worker_wallet = wallet_service.get_or_create_agent_wallet(db, agent_id=agent.id)

        # -------------------------------------------------------------
        # STEP 2: Block Unverified Agent from Bidding
        # -------------------------------------------------------------
        print("\n--- [Step 2] Enforcement: Unverified Agent Blocked from Tasks ---")
        task_small = task_service.create_task(db, TaskCreate(
            title="Small Sentiment Task",
            description="Analyze 50 reviews.",
            category="NLP",
            required_capability="NLP",
            reward=100.0,
            deadline="2026-12-31T23:59:59Z",
        ))

        blocked_pending = False
        try:
            bidding_service.create_bid(db, BidCreate(
                task_id=task_small.id,
                agent_id=agent.id,
                bid_amount=100.0,
                estimated_completion_minutes=30,
                proposal="Test proposal before canary."
            ))
        except Exception as e:
            blocked_pending = True
            print(f"  Expected Blocked Bid: {e}")

        assert_test(blocked_pending, "Pending canary agent blocked from submitting bids")

        # -------------------------------------------------------------
        # STEP 3: Run Canary Benchmark (Simulated Failure First)
        # -------------------------------------------------------------
        print("\n--- [Step 3] Run Canary Benchmark: Failure Flow ---")
        test_fail = canary_service.run_canary_test(db, agent_id=agent.id, force_fail=True)
        db.refresh(agent)

        assert_test(test_fail.status == "failed" and test_fail.score < 80.0, 
                    f"Canary test CT-XXXX recorded as failed (Score: {test_fail.score})")
        assert_test(test_fail.canary_code is not None and test_fail.canary_code.startswith("CT-"),
                    f"Canary test auto-assigned code: {test_fail.canary_code}")
        assert_test(agent.trust_status == TRUST_STATUS_CANARY_FAILED, 
                    f"Agent trust status transitioned to '{TRUST_STATUS_CANARY_FAILED}'")
        assert_test(agent.status == "offline", "Failed agent set to offline")

        # -------------------------------------------------------------
        # STEP 4: Retest Canary Benchmark (Pass Flow)
        # -------------------------------------------------------------
        print("\n--- [Step 4] Run Canary Benchmark: Retry & Pass Flow ---")
        test_pass = canary_service.run_canary_test(db, agent_id=agent.id, force_pass=True)
        db.refresh(agent)

        assert_test(test_pass.status == "passed" and test_pass.score >= 80.0, 
                    f"Canary test passed on attempt #{test_pass.attempt_number} (Score: {test_pass.score})")
        assert_test(agent.trust_status == TRUST_STATUS_PROVISIONAL, 
                    f"Agent promoted to '{TRUST_STATUS_PROVISIONAL}' tier")
        assert_test(agent.status == "available", "Passed agent set to available")
        assert_test(agent.reputation_score >= 55.0, f"Provisional baseline reputation set ({agent.reputation_score:.1f})")

        # -------------------------------------------------------------
        # STEP 5: Provisional Safeguards (200 AP Reward Ceiling)
        # -------------------------------------------------------------
        print("\n--- [Step 5] Provisional Tier Safeguards (Max 200 AP) ---")
        
        # 5a. Small task (100 AP <= 200 AP) -> Allowed
        bid_small = bidding_service.create_bid(db, BidCreate(
            task_id=task_small.id,
            agent_id=agent.id,
            bid_amount=100.0,
            estimated_completion_minutes=25,
            proposal="Provisional worker proposal."
        ))
        assert_test(bid_small.status == "pending", "Provisional agent successfully bid on <= 200 AP task")

        # 5b. Large task (350 AP > 200 AP) -> Blocked
        task_large = task_service.create_task(db, TaskCreate(
            title="High Budget Enterprise Analysis",
            description="Massive dataset analysis.",
            category="NLP",
            required_capability="NLP",
            reward=350.0,
            deadline="2026-12-31T23:59:59Z",
        ))

        blocked_provisional_large = False
        try:
            bidding_service.create_bid(db, BidCreate(
                task_id=task_large.id,
                agent_id=agent.id,
                bid_amount=350.0,
                estimated_completion_minutes=60,
                proposal="High budget bid."
            ))
        except Exception as e:
            blocked_provisional_large = True
            print(f"  Expected Blocked Large Bid: {e}")

        assert_test(blocked_provisional_large, "Provisional agent blocked from bidding on > 200 AP task")

        # -------------------------------------------------------------
        # STEP 6: Complete Verified Tasks & Promotion to Trusted Tier
        # -------------------------------------------------------------
        print("\n--- [Step 6] Completing 3 Verified Tasks & Promotion to Trusted ---")
        
        # Setup verifier agent
        verifier = agent_service.create_agent(db, AgentCreate(
            name=f"Canary-Verifier-{uuid.uuid4().hex[:6]}",
            agent_type="verifier",
            capabilities=["Verification", "Quality Evaluation", "NLP"],
            trust_status="trusted"
        ))
        wallet_service.get_or_create_agent_wallet(db, agent_id=verifier.id)

        # Complete task 1
        bidding_service.select_winning_bid(db, task_small.id, bid_small.id)
        exec1 = execution_service.start_execution(db, task_small.id)
        execution_service.run_execution(db, exec1.id)
        sub1 = submission_service.create_submission_from_execution(db, exec1.id)
        ver1 = verification_service.create_verification_for_submission(db, sub1.id)
        verification_service.run_verification(db, ver1.id)
        db.refresh(agent)

        # Create & complete task 2
        task_m2 = task_service.create_task(db, TaskCreate(
            title="Task 2 Milestone", description="Second task.", category="NLP", required_capability="NLP", reward=120.0, deadline="2026-12-31T23:59:59Z"
        ))
        bid_m2 = bidding_service.create_bid(db, BidCreate(task_id=task_m2.id, agent_id=agent.id, bid_amount=120.0, estimated_completion_minutes=20, proposal="Milestone task 2 completion proposal."))
        bidding_service.select_winning_bid(db, task_m2.id, bid_m2.id)
        exec2 = execution_service.start_execution(db, task_m2.id)
        execution_service.run_execution(db, exec2.id)
        sub2 = submission_service.create_submission_from_execution(db, exec2.id)
        ver2 = verification_service.create_verification_for_submission(db, sub2.id)
        verification_service.run_verification(db, ver2.id)
        db.refresh(agent)

        # Create & complete task 3
        task_m3 = task_service.create_task(db, TaskCreate(
            title="Task 3 Milestone", description="Third task.", category="NLP", required_capability="NLP", reward=150.0, deadline="2026-12-31T23:59:59Z"
        ))
        bid_m3 = bidding_service.create_bid(db, BidCreate(task_id=task_m3.id, agent_id=agent.id, bid_amount=150.0, estimated_completion_minutes=20, proposal="Milestone task 3 completion proposal."))
        bidding_service.select_winning_bid(db, task_m3.id, bid_m3.id)
        exec3 = execution_service.start_execution(db, task_m3.id)
        execution_service.run_execution(db, exec3.id)
        sub3 = submission_service.create_submission_from_execution(db, exec3.id)
        ver3 = verification_service.create_verification_for_submission(db, sub3.id)
        verification_service.run_verification(db, ver3.id)
        db.refresh(agent)

        assert_test(agent.total_verified_tasks >= 3, f"Agent completed {agent.total_verified_tasks} independently verified tasks")
        assert_test(agent.reputation_score >= 70.0, f"Agent reputation increased to {agent.reputation_score:.1f}")

        # Check and promote
        promo = canary_service.check_and_promote_agent(db, agent.id)
        db.refresh(agent)

        assert_test(agent.trust_status == TRUST_STATUS_TRUSTED, f"Agent successfully elevated to '{TRUST_STATUS_TRUSTED}' tier")
        assert_test(agent.is_provisional is False, "Agent provisional flag cleared (is_provisional = False)")

        # -------------------------------------------------------------
        # STEP 7: High-Reward Bidding Unlocked for Trusted Agent
        # -------------------------------------------------------------
        print("\n--- [Step 7] High-Reward Bidding Unlocked for Trusted Agent ---")
        agent.status = "available"
        db.commit()

        bid_large_unlocked = bidding_service.create_bid(db, BidCreate(
            task_id=task_large.id,
            agent_id=agent.id,
            bid_amount=350.0,
            estimated_completion_minutes=45,
            proposal="Trusted agent enterprise proposal."
        ))
        assert_test(bid_large_unlocked.status == "pending", "Trusted agent successfully placed bid on 350 AP high-value task")

        # -------------------------------------------------------------
        # STEP 8: Max Retry Limit & Auto-Suspension
        # -------------------------------------------------------------
        print("\n--- [Step 8] Max Canary Retries (5 Attempts) & Auto-Suspension ---")
        bad_agent = agent_service.create_agent(db, AgentCreate(
            name=f"Flawed-Agent-{uuid.uuid4().hex[:6]}",
            agent_type="worker",
            capabilities=["Security"],
        ))

        for i in range(1, 6):
            res = canary_service.run_canary_test(db, bad_agent.id, force_fail=True)
            db.refresh(bad_agent)
            print(f"  Attempt #{i}: status={res.status}, agent_trust={bad_agent.trust_status}")

        assert_test(bad_agent.trust_status == TRUST_STATUS_SUSPENDED, "Agent auto-suspended after 5 failed canary attempts")
        assert_test(bad_agent.is_suspended is True, "Agent is_suspended flag set to True")

        # Attempting a 6th test should be rejected
        blocked_6th = False
        try:
            canary_service.run_canary_test(db, bad_agent.id, force_pass=True)
        except Exception:
            blocked_6th = True

        assert_test(blocked_6th, "6th canary attempt strictly rejected with 403 Forbidden")

        # -------------------------------------------------------------
        # STEP 9: Comprehensive Trust Report
        # -------------------------------------------------------------
        print("\n--- [Step 9] Trust Audit Report Generation ---")
        report = canary_service.get_agent_trust_report(db, agent.id)
        
        assert_test(report["trust_status"] == TRUST_STATUS_TRUSTED, "Trust report reflects Trusted tier")
        assert_test(report["canary_passed"] is True, "Trust report confirms Canary PASS")
        assert_test(report["max_allowed_reward"] is None, "Trust report confirms uncapped rewards for Trusted tier")
        assert_test(len(report["recent_canary_tests"]) >= 2, f"Trust report contains {len(report['recent_canary_tests'])} canary audit logs")

        print("\n" + "="*70)
        print(f"SUMMARY: {passed} PASSED, {failed} FAILED")
        print("="*70)

        return 0 if failed == 0 else 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(run_tests())
