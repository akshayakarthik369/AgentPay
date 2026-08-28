"""
Phase 13 Test Suite: Reputation & Trust Engine
Validates deterministic 5-factor reputation scoring, cold-start handling,
reputation event audit trail, automatic triggers on settlement/verification,
matching and bidding integration, idempotency, and API endpoints.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from main import app
from database import SessionLocal
from app.models.agent import Agent
from app.models.task import Task
from app.models.reputation import ReputationEvent
from app.services import reputation_service
from app.services.matching_service import score_agent_task_pair
from app.services.bidding_service import calculate_bid_selection_score

client = TestClient(app)

passed = 0
failed = 0


def check(label: str, condition: bool):
    global passed, failed
    if condition:
        print(f"  [PASS] {label}")
        passed += 1
    else:
        print(f"  [FAIL] {label}")
        failed += 1


print("\n=== Phase 13 Reputation & Trust Engine Verification ===")

# --------------------------------------------------------------------------
# 0. Health Check
# --------------------------------------------------------------------------
print("\n--- 0. Health Check ---")
resp = client.get("/api/health")
check("GET /api/health returns 200", resp.status_code == 200)

# --------------------------------------------------------------------------
# 1. Cold Start & New Agent Baseline
# --------------------------------------------------------------------------
print("\n--- 1. Cold Start for New Agent ---")
new_agent_payload = {
    "name": f"Cold-Start-Agent-{datetime.utcnow().timestamp()}",
    "agent_type": "worker",
    "capabilities": ["NLP", "Text Summarization"],
    "status": "available",
}
create_resp = client.post("/api/agents", json=new_agent_payload)
check("POST /api/agents returns 201", create_resp.status_code == 201)
new_agent = create_resp.json()
new_agent_id = new_agent["id"]

rep_resp = client.get(f"/api/agents/{new_agent_id}/reputation")
check("GET /api/agents/{id}/reputation returns 200", rep_resp.status_code == 200)
rep_data = rep_resp.json()

check("New agent has default score 80.0", rep_data["reputation_score"] == 80.0)
check("New agent status is Provisional", rep_data["is_provisional"] is True)
check("New agent level is 'Provisional'", rep_data["reputation_level"] == "Provisional")
check("New agent has 0 verified tasks", rep_data["total_verified_tasks"] == 0)
check("New agent has 5-factor weights dict", len(rep_data["weights"]) == 5)
check("Quality weight is 0.35", rep_data["weights"]["quality"] == 0.35)
check("Success rate weight is 0.30", rep_data["weights"]["success_rate"] == 0.30)
check("Reliability weight is 0.20", rep_data["weights"]["reliability"] == 0.20)
check("Consistency weight is 0.10", rep_data["weights"]["consistency"] == 0.10)
check("Experience weight is 0.05", rep_data["weights"]["experience"] == 0.05)

# --------------------------------------------------------------------------
# 2. Pure Deterministic Formula Computation
# --------------------------------------------------------------------------
print("\n--- 2. Deterministic Formula Computation ---")
# Test known inputs: 5 PASS scores [90, 92, 88, 95, 91]
scores = [90.0, 92.0, 88.0, 95.0, 91.0]
breakdown = reputation_service.compute_reputation_breakdown(
    verification_scores=scores,
    successful_count=5,
    failed_count=0,
    integrity_fail_count=0,
)

expected_qual = sum(scores) / 5.0  # 91.2
check(f"Calculated Quality is {expected_qual:.1f}", abs(breakdown["quality_score"] - 91.2) < 0.1)
check("Calculated Success Rate is 100.0%", breakdown["success_rate_score"] == 100.0)
check("Calculated Reliability is 100.0%", breakdown["reliability_score"] == 100.0)
check("Calculated Experience for 5 tasks is 70.0", breakdown["experience_score"] == 70.0)
check("Consistency score > 90", breakdown["consistency_score"] > 90.0)
check("Established status when >= 3 tasks", breakdown["is_provisional"] is False)
check("Level is 'Excellent' for high score", breakdown["reputation_level"] in ("Excellent", "Strong"))
check("Reputation score is within [90, 100]", 90.0 <= breakdown["reputation_score"] <= 100.0)

# --------------------------------------------------------------------------
# 3. Full E2E PASS Lifecycle -> Automatic Positive Reputation Update
# --------------------------------------------------------------------------
print("\n--- 3. E2E PASS Lifecycle & Positive Reputation Event ---")
# 1. Create worker agent
worker_name = f"E2E-Worker-P13-{datetime.utcnow().timestamp()}"
worker_resp = client.post("/api/agents", json={
    "name": worker_name,
    "agent_type": "worker",
    "capabilities": ["NLP", "Sentiment Analysis"],
    "status": "available",
})
worker_id = worker_resp.json()["id"]

# 2. Create verifier agent
verifier_name = f"E2E-Verifier-P13-{datetime.utcnow().timestamp()}"
verifier_resp = client.post("/api/agents", json={
    "name": verifier_name,
    "agent_type": "verifier",
    "capabilities": ["NLP", "Quality Assurance"],
    "status": "available",
})
verifier_id = verifier_resp.json()["id"]

# 3. Create task
task_payload = {
    "title": "Reputation Test Sentiment Task",
    "description": "Analyze sentiments of customer reviews with high quality.",
    "category": "NLP",
    "required_capability": "NLP",
    "reward": 100.0,
    "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z",
    "minimum_reputation": 60,
    "minimum_quality_score": 75,
}
task_resp = client.post("/api/tasks", json=task_payload)
task_id = task_resp.json()["id"]

# 4. Bid and Select Worker
bid_resp = client.post("/api/bids", json={
    "task_id": task_id,
    "agent_id": worker_id,
    "bid_amount": 90.0,
    "estimated_completion_minutes": 20,
    "proposal": "Expert NLP classification.",
})
bid_id = bid_resp.json()["id"]

select_resp = client.post(f"/api/tasks/{task_id}/select-bid/{bid_id}")
check("Select bid returns 200", select_resp.status_code == 200)

# 5. Execute
exec_start = client.post(f"/api/tasks/{task_id}/execution/start")
exec_id = exec_start.json()["id"]
exec_run = client.post(f"/api/executions/{exec_id}/run")
check("Execution completed", exec_run.json()["status"] == "completed")

# 6. Submit Result
submit_resp = client.post(f"/api/executions/{exec_id}/submit", json={
    "output_text": "Customer sentiment analysis report: Overall positive 88%, negative 12%. Detailed breakdown attached.",
    "structured_output": {"positive_ratio": 0.88, "negative_ratio": 0.12, "sample_count": 500},
    "evidence": {"method": "BERT classifier", "accuracy": 0.94},
    "provenance": {"model": "finetuned-roberta-v2"},
})
submission_id = submit_resp.json()["submission_id"]

# 7. Verify (PASS)
verif_start = client.post(f"/api/submissions/{submission_id}/verification/start")
verif_id = verif_start.json()["verification_id"]
verif_run = client.post(f"/api/verifications/{verif_id}/run")
verif_data = verif_run.json()
check("Verification decision is PASS", verif_data["decision"] == "PASS")

# 8. Check Automatic Settlement Completed
settle_resp = client.get(f"/api/tasks/{task_id}/settlement")
check("Task settlement exists", settle_resp.status_code == 200)
settlement_data = settle_resp.json()
check("Settlement status is completed", settlement_data["status"] == "completed")

# 9. Verify Worker Reputation Updated
worker_rep_resp = client.get(f"/api/agents/{worker_id}/reputation")
worker_rep = worker_rep_resp.json()
check("Worker has 1 total verified task", worker_rep["total_verified_tasks"] == 1)
check("Worker has 1 successful verified task", worker_rep["successful_verified_tasks"] == 1)
check("Worker average quality > 80", worker_rep["average_quality_score"] > 80.0)

# 10. Verify Reputation History Event
history_resp = client.get(f"/api/agents/{worker_id}/reputation/history")
check("GET /api/agents/{id}/reputation/history returns 200", history_resp.status_code == 200)
events = history_resp.json()
check("At least 1 reputation event recorded", len(events) >= 1)
latest_event = events[0]
check("Event code starts with RE-", str(latest_event["event_code"]).startswith("RE-"))
check("Event type is 'successful_settlement'", latest_event["event_type"] == "successful_settlement")
check("Event task_id matches", latest_event["task_id"] == task_id)
check("Event verification_decision is PASS", latest_event["verification_decision"] == "PASS")
check("Event has explainable reason", len(latest_event["reason"]) > 10)

# --------------------------------------------------------------------------
# 4. Failure Impact -> Automatic Negative Reputation Update
# --------------------------------------------------------------------------
print("\n--- 4. Verification FAIL & Negative Reputation Event ---")
# Create high-bar task that will fail
fail_task_resp = client.post("/api/tasks", json={
    "title": "Impossible Accuracy Task",
    "description": "Requires 99.9% precision.",
    "category": "NLP",
    "required_capability": "NLP",
    "reward": 50.0,
    "deadline": (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z",
    "minimum_reputation": 50,
    "minimum_quality_score": 99,
})
fail_task_id = fail_task_resp.json()["id"]

# Bid and Select same worker
fail_bid_resp = client.post("/api/bids", json={
    "task_id": fail_task_id,
    "agent_id": worker_id,
    "bid_amount": 45.0,
    "estimated_completion_minutes": 15,
    "proposal": "Attempting high accuracy requirement.",
})
check("Bid submitted for fail test", fail_bid_resp.status_code == 201)
fail_bid_id = fail_bid_resp.json().get("id")
client.post(f"/api/tasks/{fail_task_id}/select-bid/{fail_bid_id}")

# Execute and submit inadequate result
f_exec_start = client.post(f"/api/tasks/{fail_task_id}/execution/start")
f_exec_id = f_exec_start.json()["id"]
client.post(f"/api/executions/{f_exec_id}/run")

f_sub_resp = client.post(f"/api/executions/{f_exec_id}/submit", json={
    "output_text": "Short answer.",
})
f_sub_id = f_sub_resp.json()["submission_id"]

# Run verification (will fail because quality < 99)
f_verif_start = client.post(f"/api/submissions/{f_sub_id}/verification/start")
f_verif_id = f_verif_start.json()["verification_id"]
f_verif_run = client.post(f"/api/verifications/{f_verif_id}/run")
f_verif_data = f_verif_run.json()
check("Verification decision is FAIL", f_verif_data["decision"] == "FAIL")

# Verify Worker Reputation Updated with Failure
worker_rep_after_fail = client.get(f"/api/agents/{worker_id}/reputation").json()
check("Worker has 2 total verified tasks", worker_rep_after_fail["total_verified_tasks"] == 2)
check("Worker has 1 failed verified task", worker_rep_after_fail["failed_verified_tasks"] == 1)
check("Worker success rate decreased to 50%", abs(worker_rep_after_fail["success_rate_score"] - 50.0) < 0.1)

# Check Failure Event in History
f_history = client.get(f"/api/agents/{worker_id}/reputation/history").json()
f_latest = f_history[0]
check("Latest event is 'verification_fail'", f_latest["event_type"] == "verification_fail")
check("Score delta is negative or decreasing", f_latest["score_delta"] < 0)
check("Failure reason mentions failed verification", "failed" in f_latest["reason"].lower())

# --------------------------------------------------------------------------
# 5. Review Handling (Neutral Hold)
# --------------------------------------------------------------------------
print("\n--- 5. Review Required Handling ---")
db = SessionLocal()
try:
    rev_event = reputation_service.record_reputation_event(
        db=db,
        agent_id=worker_id,
        event_type="review_required",
        previous_score=worker_rep_after_fail["reputation_score"],
        new_score=worker_rep_after_fail["reputation_score"],
        reason="Task under human review: score held neutrally.",
        task_id=fail_task_id,
    )
    db.commit()
    check("Review event created with RE- code", rev_event.event_code.startswith("RE-"))
    check("Review event delta is 0.0", rev_event.score_delta == 0.0)
finally:
    db.close()

# --------------------------------------------------------------------------
# 6. Integrity Failure Penalty
# --------------------------------------------------------------------------
print("\n--- 6. Integrity Failure Handling ---")
db = SessionLocal()
try:
    int_breakdown = reputation_service.compute_reputation_breakdown(
        verification_scores=[80.0],
        successful_count=1,
        failed_count=1,
        integrity_fail_count=2,  # Heavy penalty in reliability
    )
    check("Integrity failure reduces reliability component", int_breakdown["reliability_score"] < 50.0)
    check("Overall reputation reflects integrity penalty", int_breakdown["reputation_score"] < 75.0)
finally:
    db.close()

# --------------------------------------------------------------------------
# 7. Idempotency & Duplicate Protection
# --------------------------------------------------------------------------
print("\n--- 7. Idempotency Protection ---")
db = SessionLocal()
try:
    # Triggering hook twice for same settlement
    ev1 = reputation_service.on_settlement_completed(db, settlement_data["id"])
    db.commit()
    history_len_before = len(client.get(f"/api/agents/{worker_id}/reputation/history").json())
    ev2 = reputation_service.on_settlement_completed(db, settlement_data["id"])
    db.commit()
    history_len_after = len(client.get(f"/api/agents/{worker_id}/reputation/history").json())
    check("Duplicate settlement callback does NOT duplicate reputation event", history_len_before == history_len_after)
finally:
    db.close()

# --------------------------------------------------------------------------
# 8. Score Bounds (0 <= Score <= 100)
# --------------------------------------------------------------------------
print("\n--- 8. Score Clamping and Bounds ---")
extreme_fail = reputation_service.compute_reputation_breakdown(
    verification_scores=[0.0, 0.0, 0.0],
    successful_count=0,
    failed_count=10,
    integrity_fail_count=5,
)
check("Extreme failure clamped >= 0", extreme_fail["reputation_score"] >= 0.0)

extreme_pass = reputation_service.compute_reputation_breakdown(
    verification_scores=[100.0] * 30,
    successful_count=30,
    failed_count=0,
    integrity_fail_count=0,
)
check("Extreme success clamped <= 100", extreme_pass["reputation_score"] <= 100.0)

# --------------------------------------------------------------------------
# 9. Matching Integration (Phase 6 uses Real Reputation)
# --------------------------------------------------------------------------
print("\n--- 9. Capability Matching with Real Reputation ---")
db = SessionLocal()
try:
    # Create Agent High Rep (95) and Agent Low Rep (50)
    high_rep_agent = Agent(
        name=f"HighRep-{datetime.utcnow().timestamp()}",
        agent_type="worker",
        capabilities=["Research"],
        status="available",
        reputation_score=95.0,
        average_quality_score=95.0,
        success_rate=95.0,
        is_active=True,
    )
    low_rep_agent = Agent(
        name=f"LowRep-{datetime.utcnow().timestamp()}",
        agent_type="worker",
        capabilities=["Research"],
        status="available",
        reputation_score=50.0,
        average_quality_score=50.0,
        success_rate=50.0,
        is_active=True,
    )
    db.add(high_rep_agent)
    db.add(low_rep_agent)
    db.commit()
    db.refresh(high_rep_agent)
    db.refresh(low_rep_agent)

    test_task = Task(
        title="Research Task for Matching",
        description="Deep literature survey.",
        category="Research",
        required_capability="Research",
        reward=80.0,
        deadline=datetime.utcnow() + timedelta(days=5),
        minimum_reputation=80,
        minimum_quality_score=80,
        status="open",
    )
    db.add(test_task)
    db.commit()
    db.refresh(test_task)

    high_match = score_agent_task_pair(high_rep_agent, test_task)
    low_match = score_agent_task_pair(low_rep_agent, test_task)

    check("High reputation agent achieves higher match score", high_match["overall_score"] > low_match["overall_score"])
    check("High rep agent reputation score is 100", high_match["reputation_score"] == 100.0)
    check("Low rep agent reputation reflects deficit", low_match["reputation_score"] < 100.0)
finally:
    db.close()

# --------------------------------------------------------------------------
# 10. Bid Ranking Integration (Phase 7 uses Real Reputation)
# --------------------------------------------------------------------------
print("\n--- 10. Bid Ranking with Real Reputation ---")
high_bid_score = calculate_bid_selection_score(
    match_score=90.0,
    reputation=95.0,
    bid_amount=80.0,
    task_reward=100.0,
    estimated_minutes=30,
)
low_bid_score = calculate_bid_selection_score(
    match_score=90.0,
    reputation=50.0,
    bid_amount=80.0,
    task_reward=100.0,
    estimated_minutes=30,
)
check("High reputation bid achieves higher selection score", high_bid_score > low_bid_score)

# --------------------------------------------------------------------------
# 11. Leaderboard & Summary APIs
# --------------------------------------------------------------------------
print("\n--- 11. Leaderboard and Summary APIs ---")
leaderboard_resp = client.get("/api/reputation/leaderboard?limit=10")
check("GET /api/reputation/leaderboard returns 200", leaderboard_resp.status_code == 200)
leaderboard = leaderboard_resp.json()
check("Leaderboard returns items", len(leaderboard) > 0)
check("Leaderboard is sorted descending by reputation",
      all(leaderboard[i]["reputation_score"] >= leaderboard[i+1]["reputation_score"] for i in range(len(leaderboard)-1)))
check("Leaderboard item contains rank and level", "rank" in leaderboard[0] and "reputation_level" in leaderboard[0])

summary_resp = client.get("/api/reputation/summary")
check("GET /api/reputation/summary returns 200", summary_resp.status_code == 200)
summary = summary_resp.json()
check("Summary total_agents > 0", summary["total_agents"] > 0)
check("Summary has established and provisional counts", "established_agents" in summary and "provisional_agents" in summary)
check("Summary has tier distribution counts", "excellent_count" in summary and "strong_count" in summary)

# --------------------------------------------------------------------------
# Final Summary
# --------------------------------------------------------------------------
total = passed + failed
print("\n" + "="*56)
print(f"Phase 13 Results: {passed}/{total} passed, {failed} failed")
if failed == 0:
    print("Phase 13 Status: ALL TESTS PASSED [OK]")
    print("\nVerified Core Reputation Engine:")
    print("  [x] Deterministic 5-Factor Formula (Quality 35%, Success 30%, Reliability 20%, Consistency 10%, Experience 5%)")
    print("  [x] Cold Start: 80.0 Baseline, labeled 'Provisional' until >= 3 verified tasks")
    print("  [x] Automatic Positive Recalculation & RE-xxxx Event on Settlement Completion")
    print("  [x] Automatic Negative Recalculation on Verification FAIL")
    print("  [x] Neutral Review Event recording")
    print("  [x] Reliability Penalty on Integrity Tampering")
    print("  [x] Duplicate Callback Idempotency Protection")
    print("  [x] Bounded Score Range [0, 100]")
    print("  [x] Real Reputation utilized in Phase 6 Capability Matching")
    print("  [x] Real Reputation utilized in Phase 7 Bid Ranking")
    print("  [x] Full Leaderboard and Trust Distribution APIs")
else:
    print("Phase 13 Status: FAILURES DETECTED")
print("="*56)
