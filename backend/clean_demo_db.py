"""
clean_demo_db.py — Remove test-generated records from agentpay.db

Rules:
  - Remove tasks whose titles match known test patterns or have reward > 1000 AP
  - Remove agents whose names match known test patterns
  - Cascade-delete related bids, executions, submissions, verifications, etc.
  - Preserve all legitimate demo tasks and seeded agents (ids 1-6)
  - Add a fresh clean demo task if none exists

Run with:
    venv\\Scripts\\python.exe clean_demo_db.py
"""
import sqlite3
import re
from datetime import datetime, timedelta

DB_PATH = "agentpay.db"

# ── Patterns that mark a record as test-generated ────────────────────────────
TASK_TEST_PATTERNS = [
    r"^Phase\d",                      # Phase11..., Phase 10...
    r"^E2E ",                          # E2E Task...
    r"Giant Reward",                   # Insufficient-balance test tasks
    r"^NLP Test",
    r"^Test Task",
    r"^Automated",
    r"^Stress",
    r"Phase \d+ Test",
    r"Phase\d+ ",
    r"escrow test",
    r"insuff",
]

AGENT_TEST_PATTERNS = [
    r"Phase\d",                        # Research-Agent-Phase8-*
    r"Phase \d",
    r"E2E-Agent-\d",                   # E2E-Agent-1787...
    r"Final-E2E",
    r"-P11-",                          # NLP-Worker-P11-*
    r"NLP-Worker-P\d",
    r"NLP-Bidder-[A-Z]-\d",           # NLP-Bidder-A-178...
    r"NLP-Specialist-\d",
    r"Code-Ineligible-",
    r"Insuff-",
    r"Agent-Insuff",
    r"Stress-Agent",
    r"Research-Agent-Phase",
    r"Data-Agent-Phase",
    r"Code-Agent-Phase",
    r"General-Agent-Phase",
]

# ── Seeded agent IDs to ALWAYS preserve ──────────────────────────────────────
# These are the demo roster from seed_agents.py (ids 1–6 typically)
PRESERVE_AGENT_IDS = {1, 2, 3, 4, 5, 6}

def matches_any(name: str, patterns: list) -> bool:
    name_lower = name.lower()
    for p in patterns:
        if re.search(p, name, re.IGNORECASE):
            return True
    return False


def clean_database():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    con.execute("PRAGMA foreign_keys = OFF")  # Handle cascade manually

    print("=" * 60)
    print("AgentPay Demo DB Cleaner")
    print("=" * 60)

    # ── 1. Identify test task IDs ─────────────────────────────────────────────
    cur.execute("SELECT id, title, reward FROM tasks")
    all_tasks = cur.fetchall()
    test_task_ids = []
    for task_id, title, reward in all_tasks:
        is_test = matches_any(title, TASK_TEST_PATTERNS)
        is_huge = reward and reward > 1000
        if is_test or is_huge:
            test_task_ids.append(task_id)
            print(f"  [DEL TASK] id={task_id}, title='{title}', reward={reward}")

    print(f"\n  => {len(test_task_ids)} test tasks identified for deletion")

    # ── 2. Identify test agent IDs ────────────────────────────────────────────
    cur.execute("SELECT id, name, agent_type FROM agents")
    all_agents = cur.fetchall()
    test_agent_ids = []
    for agent_id, name, agent_type in all_agents:
        if agent_id in PRESERVE_AGENT_IDS:
            continue
        if matches_any(name, AGENT_TEST_PATTERNS):
            test_agent_ids.append(agent_id)

    print(f"  => {len(test_agent_ids)} test agents identified for deletion")

    # ── 3. Cascade-delete test task related records ───────────────────────────
    if test_task_ids:
        placeholders = ",".join("?" * len(test_task_ids))

        # Bids for test tasks
        cur.execute(f"SELECT id FROM bids WHERE task_id IN ({placeholders})", test_task_ids)
        test_bid_ids = [r[0] for r in cur.fetchall()]

        # Executions for test tasks
        cur.execute(f"SELECT id FROM task_executions WHERE task_id IN ({placeholders})", test_task_ids)
        test_exec_ids = [r[0] for r in cur.fetchall()]

        # Submissions for test executions
        sub_ids = []
        if test_exec_ids:
            ep = ",".join("?" * len(test_exec_ids))
            cur.execute(f"SELECT id FROM result_submissions WHERE execution_id IN ({ep})", test_exec_ids)
            sub_ids = [r[0] for r in cur.fetchall()]

        # Verifications for test submissions
        verif_ids = []
        if sub_ids:
            sp = ",".join("?" * len(sub_ids))
            cur.execute(f"SELECT id FROM verifications WHERE submission_id IN ({sp})", sub_ids)
            verif_ids = [r[0] for r in cur.fetchall()]

        # Delete in order: verifications → submissions → executions → bids → tasks
        for verif_id in verif_ids:
            cur.execute("DELETE FROM verification_audit_logs WHERE verification_id=?", (verif_id,))
        if verif_ids:
            vp = ",".join("?" * len(verif_ids))
            cur.execute(f"DELETE FROM verifications WHERE id IN ({vp})", verif_ids)
            print(f"  Deleted {len(verif_ids)} verifications")

        if sub_ids:
            sp = ",".join("?" * len(sub_ids))
            cur.execute(f"DELETE FROM result_submissions WHERE id IN ({sp})", sub_ids)
            print(f"  Deleted {len(sub_ids)} submissions")

        if test_exec_ids:
            ep = ",".join("?" * len(test_exec_ids))
            cur.execute(f"DELETE FROM task_executions WHERE id IN ({ep})", test_exec_ids)
            print(f"  Deleted {len(test_exec_ids)} executions")

        if test_bid_ids:
            bp = ",".join("?" * len(test_bid_ids))
            cur.execute(f"DELETE FROM bids WHERE id IN ({bp})", test_bid_ids)
            print(f"  Deleted {len(test_bid_ids)} bids")

        cur.execute(f"DELETE FROM tasks WHERE id IN ({placeholders})", test_task_ids)
        print(f"  Deleted {len(test_task_ids)} tasks")

    # ── 4. Cascade-delete test agent related records ──────────────────────────
    if test_agent_ids:
        ap = ",".join("?" * len(test_agent_ids))
        cur.execute(f"DELETE FROM bids WHERE agent_id IN ({ap})", test_agent_ids)
        cur.execute(f"DELETE FROM task_executions WHERE agent_id IN ({ap})", test_agent_ids)
        cur.execute(f"DELETE FROM agents WHERE id IN ({ap})", test_agent_ids)
        print(f"  Deleted {len(test_agent_ids)} test agents + their related bids/executions")

    # ── 5. Verify remaining tasks ─────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM tasks")
    remaining_tasks = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM agents")
    remaining_agents = cur.fetchone()[0]

    print(f"\n  Remaining tasks: {remaining_tasks}")
    print(f"  Remaining agents: {remaining_agents}")

    # ── 6. Ensure at least one clean demo task exists ─────────────────────────
    cur.execute("SELECT COUNT(*) FROM tasks WHERE title='Customer Review Sentiment Analysis' AND status='open'")
    demo_exists = cur.fetchone()[0]
    if not demo_exists:
        deadline = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
        cur.execute("""
            INSERT INTO tasks (title, description, category, required_capability, reward, deadline,
                               minimum_reputation, minimum_quality_score, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', datetime('now'), datetime('now'))
        """, (
            "Customer Review Sentiment Analysis",
            "Extract sentiment polarity, key entities, and opinions from enterprise user reviews. "
            "Deliver a structured JSON report with per-review scores.",
            "NLP",
            "NLP",
            150.0,
            deadline,
            0,
            70,
        ))
        print("\n  Added fresh demo task: Customer Review Sentiment Analysis (150 AP)")

    con.commit()
    con.execute("PRAGMA foreign_keys = ON")
    con.close()
    print("\n  Database cleanup complete!")
    print("=" * 60)


if __name__ == "__main__":
    clean_database()
