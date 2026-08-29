"""
reset_demo_db.py — Full demo database reset.

Keeps ONLY:
  - The 8 official seeded agents (by name pattern)
  - A curated set of realistic demo tasks
  - Cleans up all test-generated agents, tasks, bids, executions, etc.

Run with:
    $env:PYTHONIOENCODING="utf-8"; .\\venv\\Scripts\\python.exe reset_demo_db.py
"""
import sqlite3
import re
from datetime import datetime, timedelta

DB_PATH = "agentpay.db"

# ── Official seeded agents to keep (exact name match) ─────────────────────────
KEEP_AGENT_NAMES = {
    "nlp-agent-01",
    "research-agent-01",
    "data-agent-01",
    "code-agent-01",
    "verify-agent-01",
    "verify-agent-02",
    "content-agent-01",
    "arbitrator-agent-01",
    "arbitrator-agent-02",
}

# ── Demo task titles to keep (exact match or substring) ───────────────────────
KEEP_TASK_TITLES = {
    "Customer Review Sentiment Analysis",
    "Customer Review Sentiment Extraction & Classification",
    "Autonomous Financial Audit Agent",
    "AI Safety Red Teaming for LLMs",
    "Solidity Smart Contract Security Audit",
    "Market Research: Multi-Agent Economic Systems",
}

def reset():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    con.execute("PRAGMA foreign_keys = OFF")

    print("=" * 62)
    print(" AgentPay — Full Demo DB Reset")
    print("=" * 62)

    # ── Step 1: Find agents to keep ──────────────────────────────────────────
    cur.execute("SELECT id, name FROM agents")
    all_agents = cur.fetchall()

    keep_agent_ids = set()
    delete_agent_ids = []
    for agent_id, name in all_agents:
        if name.lower().strip() in KEEP_AGENT_NAMES:
            keep_agent_ids.add(agent_id)
        else:
            delete_agent_ids.append(agent_id)

    print(f"\nAgents to keep: {len(keep_agent_ids)}")
    print(f"Agents to delete: {len(delete_agent_ids)}")

    # ── Step 2: Find tasks to keep ────────────────────────────────────────────
    cur.execute("SELECT id, title, reward, status FROM tasks")
    all_tasks = cur.fetchall()

    keep_task_ids = set()
    delete_task_ids = []
    for task_id, title, reward, status in all_tasks:
        keep = False
        for kt in KEEP_TASK_TITLES:
            if kt.lower() in title.lower():
                keep = True
                break
        # Keep executing/assigned tasks that belong to kept agents
        if keep and reward <= 1000:
            keep_task_ids.add(task_id)
        else:
            delete_task_ids.append(task_id)

    # Deduplicate kept tasks — keep only the latest occurrence of each title
    cur.execute("SELECT id, title, reward, status, created_at FROM tasks ORDER BY id ASC")
    all_kept = [(r[0], r[1]) for r in cur.fetchall() if r[0] in keep_task_ids]
    seen_titles = {}
    final_keep = set()
    final_delete_extra = []
    for tid, title in all_kept:
        key = title.lower().strip()
        if key not in seen_titles:
            seen_titles[key] = tid
            final_keep.add(tid)
        else:
            # Keep newest (higher id), drop old duplicate
            old_id = seen_titles[key]
            final_delete_extra.append(old_id)
            final_keep.discard(old_id)
            final_keep.add(tid)
            seen_titles[key] = tid

    delete_task_ids = [tid for tid in delete_task_ids if tid not in final_keep]
    delete_task_ids += final_delete_extra

    print(f"Tasks to keep: {len(final_keep)}")
    print(f"Tasks to delete: {len(delete_task_ids)}")

    # ── Step 3: Cascade-delete tasks ─────────────────────────────────────────
    if delete_task_ids:
        placeholders = ",".join("?" * len(delete_task_ids))

        # Bids
        cur.execute(f"SELECT id FROM bids WHERE task_id IN ({placeholders})", delete_task_ids)
        bid_ids = [r[0] for r in cur.fetchall()]

        # Executions
        cur.execute(f"SELECT id FROM task_executions WHERE task_id IN ({placeholders})", delete_task_ids)
        exec_ids = [r[0] for r in cur.fetchall()]

        # Submissions
        sub_ids = []
        if exec_ids:
            ep = ",".join("?" * len(exec_ids))
            cur.execute(f"SELECT id FROM result_submissions WHERE execution_id IN ({ep})", exec_ids)
            sub_ids = [r[0] for r in cur.fetchall()]

        # Verifications
        verif_ids = []
        if sub_ids:
            sp = ",".join("?" * len(sub_ids))
            cur.execute(f"SELECT id FROM verifications WHERE submission_id IN ({sp})", sub_ids)
            verif_ids = [r[0] for r in cur.fetchall()]

        for vid in verif_ids:
            cur.execute("DELETE FROM verification_audit_logs WHERE verification_id=?", (vid,))
        if verif_ids:
            vp = ",".join("?" * len(verif_ids))
            cur.execute(f"DELETE FROM verifications WHERE id IN ({vp})", verif_ids)
            print(f"  Deleted {len(verif_ids)} verifications")
        if sub_ids:
            sp = ",".join("?" * len(sub_ids))
            cur.execute(f"DELETE FROM result_submissions WHERE id IN ({sp})", sub_ids)
            print(f"  Deleted {len(sub_ids)} submissions")
        if exec_ids:
            ep = ",".join("?" * len(exec_ids))
            cur.execute(f"DELETE FROM task_executions WHERE id IN ({ep})", exec_ids)
            print(f"  Deleted {len(exec_ids)} executions")
        if bid_ids:
            bp = ",".join("?" * len(bid_ids))
            cur.execute(f"DELETE FROM bids WHERE id IN ({bp})", bid_ids)
            print(f"  Deleted {len(bid_ids)} bids")

        cur.execute(f"DELETE FROM tasks WHERE id IN ({placeholders})", delete_task_ids)
        print(f"  Deleted {len(delete_task_ids)} tasks")

    # ── Step 4: Cascade-delete test agents ────────────────────────────────────
    if delete_agent_ids:
        ap = ",".join("?" * len(delete_agent_ids))
        cur.execute(f"DELETE FROM bids WHERE agent_id IN ({ap})", delete_agent_ids)
        cur.execute(f"DELETE FROM task_executions WHERE agent_id IN ({ap})", delete_agent_ids)
        cur.execute(f"DELETE FROM agents WHERE id IN ({ap})", delete_agent_ids)
        print(f"  Deleted {len(delete_agent_ids)} test agents")

    # ── Step 5: Ensure clean demo tasks exist ─────────────────────────────────
    deadline = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"

    DEMO_TASKS = [
        ("Customer Review Sentiment Analysis",
         "Extract sentiment polarity, key entities, and opinions from 500+ enterprise user reviews. Deliver a structured JSON report with per-review scores and aggregate summary.",
         "NLP", "NLP", 150.0),
        ("Autonomous Financial Audit Agent",
         "Audit Q3 2025 financial statements for anomalies, flag unusual transactions, and produce a compliance summary report.",
         "Finance", "Data Analysis", 200.0),
        ("AI Safety Red Teaming for LLMs",
         "Systematically probe a deployed LLM for jailbreaks, prompt-injection vulnerabilities, and safety regressions. Deliver a structured threat report.",
         "Security", "Research", 300.0),
        ("Solidity Smart Contract Security Audit",
         "Perform an end-to-end security audit on an ERC-20 token contract. Flag reentrancy, integer overflow, and access-control issues.",
         "Blockchain", "Code Analysis", 500.0),
        ("Market Research: Multi-Agent Economic Systems",
         "Synthesize the latest academic research (2023-2025) on multi-agent economic coordination, pricing mechanisms, and incentive design.",
         "Research", "Research", 75.0),
    ]

    cur.execute("SELECT title FROM tasks")
    existing_titles = {r[0].lower() for r in cur.fetchall()}

    for title, desc, cat, cap, reward in DEMO_TASKS:
        if title.lower() not in existing_titles:
            cur.execute("""
                INSERT INTO tasks (title, description, category, required_capability, reward, deadline,
                                   minimum_reputation, minimum_quality_score, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, 70, 'open', datetime('now'), datetime('now'))
            """, (title, desc, cat, cap, reward, deadline))
            print(f"  [ADDED DEMO TASK] {title} ({reward} AP)")

    # ── Step 6: Summary ───────────────────────────────────────────────────────
    cur.execute("SELECT COUNT(*) FROM tasks")
    print(f"\nFinal task count: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM agents")
    print(f"Final agent count: {cur.fetchone()[0]}")

    cur.execute("SELECT id, title, reward, status FROM tasks ORDER BY id")
    print("\nRemaining tasks:")
    for r in cur.fetchall():
        print(f"  {r}")

    cur.execute("SELECT id, name, agent_type, status FROM agents ORDER BY id")
    print("\nRemaining agents:")
    for r in cur.fetchall():
        print(f"  {r}")

    con.commit()
    con.execute("PRAGMA foreign_keys = ON")
    con.close()
    print("\nDemo DB reset complete!")
    print("=" * 62)

if __name__ == "__main__":
    reset()
