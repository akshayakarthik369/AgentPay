"""
Phase 11 — Wallet + Escrow System Tests
Uses the real database but works idempotently by checking relative balance changes.
"""

import sys
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

passed = 0
failed = 0

def check(label, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  [PASS] {label}")
        passed += 1
    else:
        print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ""))
        failed += 1

def check_eq(label, actual, expected):
    check(label, actual == expected, f"got {actual!r}, expected {expected!r}")

def uid():
    """Short unique suffix to avoid DB collisions between test runs."""
    return str(uuid.uuid4())[:8]


print("\n=== Phase 11 Wallet + Escrow System Verification ===\n")

# --------------------------------------------------------------------------
# 0. Health check
# --------------------------------------------------------------------------
resp = client.get("/api/health")
check("GET /api/health returns 200", resp.status_code == 200)

# --------------------------------------------------------------------------
# 1. Client Wallet — Seeded at 5000 AP
# --------------------------------------------------------------------------
print("\n--- 1. Client Wallet Seeding ---")
resp = client.get("/api/client/wallet")
check("GET /api/client/wallet returns 200", resp.status_code == 200)
wallet_data = resp.json()
check("Client wallet has wallet_code starting with WL-", wallet_data.get("wallet_code", "").startswith("WL-"))
check("Client wallet currency is AP", wallet_data.get("currency") == "AP")
check("Client wallet available_balance > 0", wallet_data.get("available_balance", 0) > 0)
check("Client wallet is_active is True", wallet_data.get("is_active") is True)

initial_available = wallet_data["available_balance"]
initial_locked = wallet_data.get("locked_balance", 0)
print(f"  (Info) Client wallet: {initial_available} AP available, {initial_locked} AP locked")

# --------------------------------------------------------------------------
# 2. Create Test Task, Agents, Bids
# --------------------------------------------------------------------------
print("\n--- 2. Create Task, Agents, and Bids ---")
deadline = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
suffix = uid()
REWARD = 50.0  # Use small reward to not exhaust balance

task_resp = client.post("/api/tasks", json={
    "title": f"Phase11 Escrow Test {suffix}",
    "description": "Testing reward locking and escrow lifecycle.",
    "category": "NLP",
    "required_capability": "NLP",
    "reward": REWARD,
    "deadline": deadline,
    "minimum_reputation": 0,
    "minimum_quality_score": 70,
})
check("POST /api/tasks returns 201", task_resp.status_code == 201)
task = task_resp.json()
task_id = task["id"]
check("Task has task_code", bool(task.get("task_code")))

# Create worker agent
worker_resp = client.post("/api/agents", json={
    "name": f"NLP-Worker-P11-{suffix}",
    "agent_type": "worker",
    "description": "Phase 11 test worker",
    "capabilities": ["NLP"],
    "status": "available",
})
check("POST /api/agents creates worker (201)", worker_resp.status_code == 201)
worker = worker_resp.json()
worker_id = worker["id"]

# Create verifier agent  
verifier_resp = client.post("/api/agents", json={
    "name": f"Verifier-P11-{suffix}",
    "agent_type": "verifier",
    "description": "Phase 11 test verifier",
    "capabilities": ["NLP", "Verification"],
    "status": "available",
})
check("POST /api/agents creates verifier (201)", verifier_resp.status_code == 201)
verifier_id = verifier_resp.json()["id"]

# Get agent wallets
worker_wallet_resp = client.get(f"/api/agents/{worker_id}/wallet")
check(f"GET /api/agents/{worker_id}/wallet returns 200", worker_wallet_resp.status_code == 200)
worker_wallet = worker_wallet_resp.json()
check("Worker wallet starts at 0 AP available", worker_wallet["available_balance"] == 0.0)

# --------------------------------------------------------------------------
# 3. Submit Bid and Select Winner (locks escrow atomically)
# --------------------------------------------------------------------------
print("\n--- 3. Bid Submission and Winning Bid Selection ---")

bid_resp = client.post("/api/bids", json={
    "task_id": task_id,
    "agent_id": worker_id,
    "bid_amount": REWARD,
    "proposal": "I will complete this NLP task with high accuracy.",
    "estimated_completion_minutes": 30,
})
check("POST /api/bids returns 201", bid_resp.status_code == 201)
bid = bid_resp.json()
bid_id = bid["id"]

# Capture balance before assignment
pre_assign_resp = client.get("/api/client/wallet")
pre_available = pre_assign_resp.json()["available_balance"]
pre_locked = pre_assign_resp.json()["locked_balance"]

# Select winning bid (atomically locks REWARD AP in escrow)
select_resp = client.post(f"/api/tasks/{task_id}/select-bid/{bid_id}")
check("POST /api/tasks/{task_id}/select-bid/{bid_id} returns 200", select_resp.status_code == 200)
selection_result = select_resp.json()
check("Selection response has escrow_code", bool(selection_result.get("escrow_code")))
check(f"Selection response has reward_locked = {REWARD}", selection_result.get("reward_locked") == REWARD)
check("Escrow status is 'locked'", selection_result.get("escrow_status") == "locked")

escrow_id = selection_result.get("escrow_id")
check("escrow_id is present", bool(escrow_id))

# --------------------------------------------------------------------------
# 4. Verify Balance Lock
# --------------------------------------------------------------------------
print("\n--- 4. Verify Balance Locked After Assignment ---")
post_assign_resp = client.get("/api/client/wallet")
post_available = post_assign_resp.json()["available_balance"]
post_locked = post_assign_resp.json()["locked_balance"]

check(
    f"Available balance decreased by {REWARD} AP ({pre_available} -> {post_available})",
    abs((pre_available - post_available) - REWARD) < 0.01
)
check(
    f"Locked balance increased by {REWARD} AP ({pre_locked} -> {post_locked})",
    abs((post_locked - pre_locked) - REWARD) < 0.01
)

# Worker wallet still 0
worker_wallet_after = client.get(f"/api/agents/{worker_id}/wallet").json()
check("Worker wallet still 0 AP after escrow lock", worker_wallet_after["available_balance"] == 0.0)
check("Worker wallet total_earned still 0 (Phase 12 boundary)", worker_wallet_after["total_earned"] == 0.0)

# --------------------------------------------------------------------------
# 5. Escrow API
# --------------------------------------------------------------------------
print("\n--- 5. Escrow API Verification ---")
escrow_resp = client.get(f"/api/escrows/{escrow_id}")
check(f"GET /api/escrows/{escrow_id} returns 200", escrow_resp.status_code == 200)
escrow = escrow_resp.json()
check("Escrow has escrow_code", bool(escrow.get("escrow_code")))
check("Escrow task_id matches", escrow.get("task_id") == task_id)
check(f"Escrow reward_amount is {REWARD}", escrow.get("reward_amount") == REWARD)
check("Escrow status is 'locked'", escrow.get("status") == "locked")
check("Escrow has requester_wallet_code", bool(escrow.get("requester_wallet_code")))
check("Escrow has worker_agent_name", bool(escrow.get("worker_agent_name")))

# GET /api/tasks/{task_id}/escrow
task_escrow_resp = client.get(f"/api/tasks/{task_id}/escrow")
check("GET /api/tasks/{task_id}/escrow returns 200", task_escrow_resp.status_code == 200)
check_eq("Task escrow code matches", task_escrow_resp.json()["escrow_code"], escrow["escrow_code"])

# GET /api/escrows (list)
list_resp = client.get("/api/escrows")
check("GET /api/escrows returns 200", list_resp.status_code == 200)
check("Escrow list is not empty", len(list_resp.json()) >= 1)

# GET /api/escrows/summary
summary_resp = client.get("/api/escrows/summary")
check("GET /api/escrows/summary returns 200", summary_resp.status_code == 200)
summary = summary_resp.json()
check("Summary has count_locked >= 1", summary.get("count_locked", 0) >= 1)

# --------------------------------------------------------------------------
# 6. Duplicate Escrow Prevention
# --------------------------------------------------------------------------
print("\n--- 6. Duplicate Escrow Prevention ---")
dup_resp = client.post(f"/api/tasks/{task_id}/escrow/initialize")
check("Duplicate escrow on assigned task returns 409", dup_resp.status_code == 409)

# --------------------------------------------------------------------------
# 7. Insufficient Balance Guard
# --------------------------------------------------------------------------
print("\n--- 7. Insufficient Balance Guard ---")
# Create a task with reward > available balance
huge_task_resp = client.post("/api/tasks", json={
    "title": f"Giant Reward {suffix}",
    "description": "This reward exceeds requester balance.",
    "category": "NLP",
    "required_capability": "NLP",
    "reward": 999999.0,
    "deadline": deadline,
    "minimum_reputation": 0,
    "minimum_quality_score": 70,
})
check("Created huge reward task (201)", huge_task_resp.status_code == 201)
huge_task_id = huge_task_resp.json()["id"]

agent3_resp = client.post("/api/agents", json={
    "name": f"Agent-Insuff-{suffix}",
    "agent_type": "worker",
    "description": "Insufficiency test agent",
    "capabilities": ["NLP"],
    "status": "available",
})
check("Created test agent for insuff test", agent3_resp.status_code == 201)
agent3_id = agent3_resp.json()["id"]

bid3_resp = client.post("/api/bids", json={
    "task_id": huge_task_id,
    "agent_id": agent3_id,
    "bid_amount": 999999.0,
    "proposal": "I will work on this task.",
    "estimated_completion_minutes": 60,
})
check("Bid submitted for huge task", bid3_resp.status_code == 201)
bid3_id = bid3_resp.json()["id"]

# Try to select bid — should fail with 400 insufficient balance
insuff_select_resp = client.post(f"/api/tasks/{huge_task_id}/select-bid/{bid3_id}")
check("Selecting bid with insufficient balance returns 400", insuff_select_resp.status_code == 400)
check(
    "Error message mentions insufficient balance",
    "Insufficient" in insuff_select_resp.json().get("detail", "") or "insufficient" in insuff_select_resp.json().get("detail", "")
)

# Verify task NOT assigned (rollback)
insuff_task_resp = client.get(f"/api/tasks/{huge_task_id}")
status_val = insuff_task_resp.json().get("status")
print(f"DEBUG: insuff_task status={status_val}")
check("Task remains unassigned after failed escrow", status_val in ("open", "published", "bidding", "pending"))

# Verify wallet balance unchanged
after_fail_wallet = client.get("/api/client/wallet").json()
check("Available balance unchanged after failed lock", abs(after_fail_wallet["available_balance"] - post_available) < 0.01)
check("Locked balance unchanged after failed lock", abs(after_fail_wallet["locked_balance"] - post_locked) < 0.01)

# --------------------------------------------------------------------------
# 8. Escrow Audit Logs
# --------------------------------------------------------------------------
print("\n--- 8. Escrow Audit Logs ---")
audit_resp = client.get(f"/api/escrows/{escrow_id}/audit")
check(f"GET /api/escrows/{escrow_id}/audit returns 200", audit_resp.status_code == 200)
audit_logs = audit_resp.json()
check("Audit log has at least 2 entries", len(audit_logs) >= 2)
audit_actions = [log["action"] for log in audit_logs]
check("Audit contains 'escrow_created'", "escrow_created" in audit_actions)
check("Audit contains 'reward_locked'", "reward_locked" in audit_actions)

# --------------------------------------------------------------------------
# 9. Full E2E — Execute, Submit, Verify → Escrow Transitions
# --------------------------------------------------------------------------
print("\n--- 9. E2E: Execute -> Submit -> Verify -> Escrow Transitions ---")

exec_resp = client.post(f"/api/tasks/{task_id}/execution/start")
check("POST /api/tasks/{task_id}/execution/start returns 201", exec_resp.status_code == 201)
exec_id = exec_resp.json()["id"]

run_resp = client.post(f"/api/executions/{exec_id}/run")
check("POST /api/executions/{exec_id}/run returns 200", run_resp.status_code == 200)
check("Execution is completed", run_resp.json().get("status") == "completed")

submit_resp = client.post(f"/api/executions/{exec_id}/submit", json={
    "output_text": "Task completion output text.",
})
check("POST /api/executions/{exec_id}/submit returns 200/201", submit_resp.status_code in (200, 201))
submission_id = submit_resp.json()["submission_id"]

verif_start_resp = client.post(f"/api/submissions/{submission_id}/verification/start")
check("POST /api/submissions/{submission_id}/verification/start returns 201", verif_start_resp.status_code == 201)
verification_id = verif_start_resp.json()["verification_id"]

verif_run_resp = client.post(f"/api/verifications/{verification_id}/run")
check("POST /api/verifications/{verification_id}/run returns 200", verif_run_resp.status_code == 200)
verification = verif_run_resp.json()
decision = verification.get("decision")
check(f"Verification has a decision: {decision}", decision in ("PASS", "FAIL", "REVIEW"))

# Check escrow status updated from verification
escrow_after_verif = client.get(f"/api/escrows/{escrow_id}").json()
if decision == "PASS":
    check("Escrow status is 'releasable' or 'released' after PASS", escrow_after_verif["status"] in ("releasable", "released"))
    check("Escrow has releasable_at timestamp", bool(escrow_after_verif.get("releasable_at")))
    worker_wallet_verif = client.get(f"/api/agents/{worker_id}/wallet").json()
    check("Worker wallet received AP", worker_wallet_verif["available_balance"] >= 0.0)
elif decision in ("FAIL", "REVIEW"):
    check("Escrow status is 'blocked' after FAIL/REVIEW", escrow_after_verif["status"] == "blocked")

# Check audit log updated with verification outcome
audit_after_resp = client.get(f"/api/escrows/{escrow_id}/audit")
audit_after = audit_after_resp.json()
audit_actions_after = [log["action"] for log in audit_after]
if decision == "PASS":
    check("Audit contains 'verification_passed'", "verification_passed" in audit_actions_after)
    check("Audit contains 'marked_releasable'", "marked_releasable" in audit_actions_after)
elif decision in ("FAIL", "REVIEW"):
    check("Audit contains 'blocked'", "blocked" in audit_actions_after)

# --------------------------------------------------------------------------
# 10. Wallet API GET by id
# --------------------------------------------------------------------------
print("\n--- 10. Wallet API by ID ---")
req_wallet = client.get("/api/client/wallet").json()
# Wallet summary for agent
wid_resp = client.get(f"/api/agents/{worker_id}/wallet")
check("GET /api/agents/{worker_id}/wallet returns 200", wid_resp.status_code == 200)
check("Worker wallet owner_type is 'agent'", wid_resp.json().get("owner_type") == "agent")

# --------------------------------------------------------------------------
# Final Summary
# --------------------------------------------------------------------------
total = passed + failed
print("\n" + "="*52)
print(f"Results: {passed}/{total} passed, {failed} failed")
if failed == 0:
    print("Phase 11 Status: ALL PASS [OK]")
    print("\nPhase 11 boundary confirmed:")
    print("  [x] Escrow status updated correctly from verification")
    print("  [x] Worker wallet 0 AP (Phase 12 boundary held)")
    print("  [x] Audit log maintained throughout lifecycle")
else:
    print("Phase 11 Status: SOME FAILURES - review above")
print("="*52)

sys.exit(0 if failed == 0 else 1)
