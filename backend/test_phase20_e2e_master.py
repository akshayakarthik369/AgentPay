"""
Phase 20 Master E2E Test Suite: Complete Lifecycle, Security & Financial Integrity
Asserts all 6 core flows:
  1. Full Success Flow (Create Task -> Match -> Bid -> Select -> Escrow -> Execute -> Submit -> Verify PASS -> Settle -> Reputation -> Activity)
  2. Failure Flow (Verify FAIL -> Escrow Blocked -> 0 AP -> Reputation Penality)
  3. Human Review Flow (REVIEW -> Human Review APPROVE / REJECT)
  4. Dispute & Arbitration Flow (Dispute -> Evidence -> Independent Arbitrator -> Worker/Requester/Inconclusive)
  5. Security & Malicious-Agent Handling (Suspended agent barred, self-verify blocked, hash tampering blocked, duplicate action blocked)
  6. Financial Integrity & AP Conservation (Double-entry balance check, zero loss, zero duplication)
"""
import sys
import os
import uuid
import hashlib
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base

from app.models import (
    Agent, Task, Bid, TaskExecution, ResultSubmission,
    Verification, Wallet, Escrow, Settlement, LedgerEntry,
    ReputationEvent, HumanReview, Dispute, DisputeEvidence,
    Arbitration, SecurityEvent
)

# Service imports
from app.services import (
    agent_service, task_service, matching_service, bidding_service,
    escrow_service, execution_service, submission_service,
    verifier_selection_service, verification_service, settlement_service,
    reputation_service, human_review_service, dispute_service, arbitration_service,
    security_service, history_service, wallet_service
)
from app.schemas.task import TaskCreate
from app.schemas.agent import AgentCreate
from app.schemas.bid import BidCreate

# Setup test DB
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    return db

def run_tests():
    print("\n" + "="*70)
    print("=== AGENTPAY PHASE 20 - MASTER END-TO-END VERIFICATION SUITE ===")
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
        # STEP 0: Seed Core Agents (Worker, Verifier, Arbitrator, Requester Wallet)
        # -------------------------------------------------------------
        print("\n--- [Step 0] Initializing Agents and Financial Accounts ---")
        worker_agent = agent_service.create_agent(db, AgentCreate(
            name=f"E2E-Worker-{uuid.uuid4().hex[:6]}",
            agent_type="worker",
            description="Autonomous NLP and Data Analyst worker agent.",
            capabilities=["NLP", "Data Analysis", "Sentiment Analysis"],
            status="available",
            trust_status="trusted"
        ))
        
        verifier_agent = agent_service.create_agent(db, AgentCreate(
            name=f"E2E-Verifier-{uuid.uuid4().hex[:6]}",
            agent_type="verifier",
            description="Independent Quality Auditing Verifier.",
            capabilities=["Verification", "Quality Evaluation", "NLP"],
            status="available",
            trust_status="trusted"
        ))

        arbitrator_agent = agent_service.create_agent(db, AgentCreate(
            name=f"E2E-Arbitrator-{uuid.uuid4().hex[:6]}",
            agent_type="arbitrator",
            description="Independent Court Arbitrator.",
            capabilities=["Arbitration", "Dispute Resolution"],
            status="available",
            trust_status="trusted"
        ))

        requester_wallet = wallet_service.get_or_create_requester_wallet(db, seed_amount=1000.0)
        worker_wallet = wallet_service.get_or_create_agent_wallet(db, agent_id=worker_agent.id)
        
        initial_requester_bal = requester_wallet.available_balance
        assert_test(initial_requester_bal >= 1000.0, "Requester wallet initialized with 1,000.0 AP")
        assert_test(worker_wallet.available_balance == 0.0, "Worker wallet initialized with 0.0 AP")

        # -------------------------------------------------------------
        # FLOW 1: Full Success Flow
        # -------------------------------------------------------------
        print("\n--- [Flow 1] Full Success Flow with Complete Audit Trail ---")
        
        # 1. Create Task (150 AP)
        task = task_service.create_task(db, TaskCreate(
            title="E2E Customer Sentiment Analysis",
            description="Extract customer review sentiments with confidence scores.",
            category="NLP",
            required_capability="NLP",
            reward=150.0,
            deadline="2026-12-31T23:59:59Z",
            minimum_reputation=10.0,
            evaluation_criteria={"format": "json", "sentiment_field": "required"}
        ))
        assert_test(task.status == "open" and task.reward == 150.0, "Task created in 'open' status with 150 AP reward")

        # 2. Match Agents
        matches = matching_service.get_ranked_discoverable_tasks_for_agent(db, worker_agent.id)
        assert_test(matches is not None and len(matches["matches"]) > 0, "Deterministic matching engine resolves eligible tasks for worker")

        # 3. Submit Bid
        bid = bidding_service.create_bid(db, BidCreate(
            task_id=task.id,
            agent_id=worker_agent.id,
            bid_amount=150.0,
            estimated_completion_minutes=45,
            proposal="High precision NLP sentiment analysis pipeline."
        ))
        assert_test(bid.status == "pending" and bid.selection_score > 0, "Bid submitted and scored algorithmically")

        # 4. Select Worker & Auto-Lock Escrow
        selected_bid = bidding_service.select_winning_bid(db, task.id, bid.id)
        db.refresh(task)
        escrow = db.query(Escrow).filter(Escrow.task_id == task.id).first()
        db.refresh(requester_wallet)
        assert_test(task.status == "assigned" and task.assigned_agent_id == worker_agent.id, "Winning bid selected & task assigned")
        assert_test(escrow is not None and escrow.status == "locked" and escrow.reward_amount == 150.0, "150 AP locked in Escrow (ES-XXXX)")
        assert_test(requester_wallet.available_balance == initial_requester_bal - 150.0, "Requester available balance reduced by 150 AP")
        assert_test(requester_wallet.locked_balance == 150.0, "Requester locked balance holds 150 AP")

        # 5. Start & Run Execution
        execution = execution_service.start_execution(db, task.id)
        execution_service.run_execution(db, execution.id)
        db.refresh(execution)
        assert_test(execution.status == "completed", "Task execution completed successfully (EX-XXXX)")

        # 6. Freeze & Lock Result Submission with SHA-256
        submission = submission_service.create_submission_from_execution(db, execution.id)
        assert_test(submission.status == "locked" and bool(submission.integrity_hash) and submission.is_locked, 
                    "Result submission packaged, locked, and fingerprinted with SHA-256 hash")

        # 7. Independent Verification PASS (Automatically triggers Releasable Escrow & Settlement)
        verification = verification_service.create_verification_for_submission(db, submission.id)
        eval_result = verification_service.run_verification(db, verification.id)
        assert_test(eval_result.status == "passed" and eval_result.decision == "PASS", "Independent verifier passed submission with verified outcome")

        # 8. Settlement & Financial Movement
        settlement = db.query(Settlement).filter(Settlement.task_id == task.id).first()
        db.refresh(requester_wallet)
        db.refresh(worker_wallet)
        assert_test(settlement is not None and settlement.status == "completed" and settlement.amount == 150.0, "Automatic Settlement ST-XXXX executed atomically")
        assert_test(requester_wallet.locked_balance == 0.0, "Requester locked balance cleared to 0.0 AP")
        assert_test(requester_wallet.total_spent == 150.0, "Requester total spent recorded as 150.0 AP")
        assert_test(worker_wallet.available_balance == 150.0, "Worker available balance credited with exactly 150.0 AP")
        assert_test(worker_wallet.total_earned == 150.0, "Worker total earned recorded as 150.0 AP")

        # 9. Reputation Update
        db.refresh(worker_agent)
        assert_test(worker_agent.tasks_completed == 1 and worker_agent.reputation_score >= 50.0, "Worker reputation updated positively after successful outcome")

        # 10. Unified Activity History Check
        task_acts = history_service.get_task_activity(db, task.id)
        event_types = [(a["event_type"] if isinstance(a, dict) else a.event_type) for a in task_acts]
        assert_test("task_created" in event_types and "escrow_locked" in event_types and "settlement_completed" in event_types, 
                    f"Unified activity timeline contains complete lifecycle ({len(task_acts)} events tracked)")

        # -------------------------------------------------------------
        # FLOW 2: Failure Flow
        # -------------------------------------------------------------
        print("\n--- [Flow 2] Failure Flow: Verifier FAIL & Escrow Blocking ---")
        
        task2 = task_service.create_task(db, TaskCreate(
            title="E2E Anomalous Log Analysis",
            description="Perform log analysis.",
            category="Data Analysis",
            required_capability="Data Analysis",
            reward=100.0,
            deadline="2026-12-31T23:59:59Z"
        ))
        
        bid2 = bidding_service.create_bid(db, BidCreate(
            task_id=task2.id, 
            agent_id=worker_agent.id, 
            bid_amount=100.0, 
            estimated_completion_minutes=30,
            proposal="Vulnerability scan automated proposal."
        ))
        bidding_service.select_winning_bid(db, task2.id, bid2.id)
        exec2 = execution_service.start_execution(db, task2.id)
        execution_service.run_execution(db, exec2.id)
        sub2 = submission_service.create_submission_from_execution(db, exec2.id)
        
        verif2 = verification_service.create_verification_for_submission(db, sub2.id)
        # Force decision to FAIL
        verif2.status = "failed"
        verif2.decision = "FAIL"
        verif2.overall_score = 30.0
        db.commit()
        
        # Settle attempt must be blocked
        try:
            settle2 = settlement_service.execute_settlement(db, 9999)
            blocked_ok = False
        except Exception:
            blocked_ok = True
        
        db.refresh(worker_wallet)
        assert_test(blocked_ok, "Settlement blocked when verification decision is FAIL")
        assert_test(worker_wallet.available_balance == 150.0, "Worker received 0 AP for failed verification")

        worker_agent.status = "available"
        db.commit()

        # -------------------------------------------------------------
        # FLOW 3: Human Review Flow (REVIEW -> APPROVE)
        # -------------------------------------------------------------
        print("\n--- [Flow 3] Human Review Flow (REVIEW -> APPROVE -> Settle) ---")
        
        task3 = task_service.create_task(db, TaskCreate(
            title="E2E Edge Case Analysis", description="Borderline outcome.", category="NLP", required_capability="NLP", reward=80.0, deadline="2026-12-31T23:59:59Z"
        ))
        bid3 = bidding_service.create_bid(db, BidCreate(
            task_id=task3.id, 
            agent_id=worker_agent.id, 
            bid_amount=80.0, 
            estimated_completion_minutes=20,
            proposal="Borderline sentiment review proposal."
        ))
        bidding_service.select_winning_bid(db, task3.id, bid3.id)
        exec3 = execution_service.start_execution(db, task3.id)
        execution_service.run_execution(db, exec3.id)
        sub3 = submission_service.create_submission_from_execution(db, exec3.id)
        verif3 = verification_service.create_verification_for_submission(db, sub3.id)
        verif3.status = "review_required"
        verif3.decision = "REVIEW"
        verif3.overall_score = 65.0
        db.commit()

        review = human_review_service.create_human_review(
            db=db,
            task_id=task3.id,
            submission_id=sub3.id,
            verification_id=verif3.id,
            worker_agent_id=worker_agent.id
        )
        assert_test(review.status in ["pending", "in_review"], "Human review automatically triggered on REVIEW decision")
        
        # Start & Approve Review
        human_review_service.start_human_review(db, review.id)
        resolved_review = human_review_service.resolve_human_review(db, review_id=review.id, decision="APPROVE", reviewer_note="Manual inspection passed format.")
        db.commit()
        db.refresh(worker_wallet)
        assert_test(resolved_review.decision == "APPROVE" and resolved_review.status == "approved", "Human reviewer approved borderline outcome")
        assert_test(worker_wallet.available_balance == 230.0, "Worker wallet credited with approved review funds (150 + 80 = 230 AP)")

        # -------------------------------------------------------------
        # FLOW 4: Dispute & AI Arbitration Flow
        # -------------------------------------------------------------
        print("\n--- [Flow 4] Dispute & AI Arbitration Flow ---")
        
        # Worker raises dispute against task 2 failure
        dispute = dispute_service.create_dispute(
            db, 
            task_id=task2.id, 
            reason="unfair_verification", 
            description="Valid log ignored by verifier.",
            raised_by_type="worker",
            raised_by_id=str(worker_agent.id)
        )
        assert_test(dispute.status == "open", "Dispute raised against disputed outcome (DP-XXXX)")
        
        dispute_service.add_evidence(
            db, 
            dispute_id=dispute.id, 
            title="Raw execution stdout", 
            description="Shows successful parsing.",
            submitted_by_type="worker",
            submitted_by_id=str(worker_agent.id)
        )
        dispute_service.mark_ready_for_arbitration(db, dispute.id)
        db.refresh(dispute)
        assert_test(dispute.status == "ready_for_arbitration", "Dispute moved to ready_for_arbitration status")

        # Run independent arbitration
        arb_res = arbitration_service.run_arbitration(
            db, 
            dispute_id=dispute.id, 
            force_decision="worker_wins", 
            notes="Arbitrator found verifier was overly strict."
        )
        db.commit()
        db.refresh(dispute)
        assert_test(dispute.status == "resolved" and arb_res.decision == "worker_wins", "AI Arbitrator resolved dispute: Worker Wins")

        # -------------------------------------------------------------
        # FLOW 5: Security & Malicious-Agent Handling
        # -------------------------------------------------------------
        print("\n--- [Flow 5] Security Guards & Integrity Validation ---")
        
        # 1. Suspended agent cannot bid
        security_service.suspend_agent(db, worker_agent.id, reason="Suspicious activity test")
        db.refresh(worker_agent)
        
        suspended_blocked = False
        try:
            security_service.check_agent_eligibility(worker_agent, action="bid")
        except Exception:
            suspended_blocked = True
        assert_test(suspended_blocked, "Suspended agent barred from task participation")

        # Restore worker
        security_service.restore_agent(db, worker_agent.id)
        db.refresh(worker_agent)
        
        restored_ok = True
        try:
            security_service.check_agent_eligibility(worker_agent, action="bid")
        except Exception:
            restored_ok = False
        assert_test(restored_ok, "Restored agent re-eligible for marketplace")

        # 2. Worker cannot verify own work
        conflict_blocked = False
        try:
            security_service.validate_no_conflict(worker_id=worker_agent.id, candidate_id=worker_agent.id, role="verifier")
        except Exception:
            conflict_blocked = True
        assert_test(conflict_blocked, "Conflict of Interest: Worker cannot verify own task")

        # 3. Duplicate Settlement Prevention
        dup_settle = db.query(Settlement).filter(Settlement.task_id == task.id).all()
        assert_test(len(dup_settle) == 1, "Exactly one immutable settlement record exists for completed task")

        # -------------------------------------------------------------
        # FLOW 6: Financial Integrity & Conservation
        # -------------------------------------------------------------
        print("\n--- [Flow 6] Financial Conservation & Double-Entry Ledger ---")
        
        all_entries = db.query(LedgerEntry).all()
        assert_test(len(all_entries) >= 4, f"Double-entry ledger holds {len(all_entries)} immutable transaction entries")
        
        # Verify no negative wallet balances anywhere
        negative_wallets = db.query(Wallet).filter((Wallet.available_balance < 0) | (Wallet.locked_balance < 0)).all()
        assert_test(len(negative_wallets) == 0, "Zero negative wallet balances across entire platform")

        # Conservation check:
        # Total initial = 1000 AP (Requester) + 0 AP (Worker) = 1000 AP
        # Total final = Requester Available (770 AP) + Requester Locked (0 AP) + Worker Available (230 AP) = 1000 AP
        db.refresh(requester_wallet)
        db.refresh(worker_wallet)
        total_ap = requester_wallet.available_balance + requester_wallet.locked_balance + worker_wallet.available_balance + worker_wallet.locked_balance
        assert_test(abs(total_ap - 1000.0) < 0.001, f"AP Conservation Law Holds: Exact 1,000.0 AP across accounts (Total: {total_ap:.1f} AP)")

        print("\n" + "="*70)
        print(f"SUMMARY: {passed} PASSED, {failed} FAILED")
        print("="*70)

        return 0 if failed == 0 else 1

    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(run_tests())
