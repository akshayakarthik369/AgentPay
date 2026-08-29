"""
seed_marketplace_demo.py — Idempotent Seeding Script for AgentPay Marketplace Demo Data.

Populates the database with real demo records:
- Available (open) tasks (3+ tasks)
- Bidding tasks (3 tasks, each with >= 2 valid linked bids)
- Assigned tasks (3 tasks, each with winning bid, selected worker, and locked escrow)

Usage:
  .\\venv\\Scripts\\python.exe seed_marketplace_demo.py
"""

import sys
import os
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, Base, engine
from app.models.agent import Agent
from app.models.task import Task
from app.models.bid import Bid
from app.models.escrow import Escrow
from app.models.wallet import Wallet
from app.schemas.agent import AgentCreate
from app.schemas.task import TaskCreate
from app.schemas.bid import BidCreate
from app.services import (
    agent_service,
    task_service,
    bidding_service,
    wallet_service,
    escrow_service,
)

# ── 1. Official Demo Agents ───────────────────────────────────────────────────
DEMO_AGENTS = [
    {
        "name": "NLP-Agent-01",
        "agent_type": "worker",
        "description": "Autonomous AI agent specialized in natural language processing, sentiment analysis, text extraction, and summarization.",
        "capabilities": ["NLP", "Sentiment Analysis", "Summarization", "Classification"],
        "status": "available",
    },
    {
        "name": "Research-Agent-01",
        "agent_type": "worker",
        "description": "Autonomous research agent that synthesizes market intelligence, extracts key findings, and produces structured summaries.",
        "capabilities": ["Research", "Summarization", "NLP", "Data Analysis"],
        "status": "available",
    },
    {
        "name": "Data-Agent-01",
        "agent_type": "worker",
        "description": "Specialist data analysis agent. Handles dataset profiling, statistical inference, anomaly detection, and classification.",
        "capabilities": ["Data Analysis", "Classification", "Research"],
        "status": "available",
    },
    {
        "name": "Code-Agent-01",
        "agent_type": "worker",
        "description": "Static code analysis and security audit agent. Performs AST inspections, vulnerability scans, and code quality audits.",
        "capabilities": ["Code Analysis", "Code Review", "Security Audit"],
        "status": "available",
    },
    {
        "name": "Content-Agent-01",
        "agent_type": "worker",
        "description": "Technical writer and documentation synthesis agent. Generates reports, API specs, and research summaries.",
        "capabilities": ["Content Generation", "Summarization", "NLP", "Research"],
        "status": "available",
    },
    {
        "name": "Verify-Agent-01",
        "agent_type": "verifier",
        "description": "Independent verifier agent auditing submitted task deliverables against 5-factor quality thresholds.",
        "capabilities": ["Verification", "Quality Evaluation"],
        "status": "available",
    },
    {
        "name": "Verify-Agent-02",
        "agent_type": "verifier",
        "description": "Advanced verifier agent specialized in NLP, data consistency, and research methodology verification.",
        "capabilities": ["Verification", "Quality Evaluation", "NLP", "Research", "Data Analysis"],
        "status": "available",
    },
    {
        "name": "Arbitrator-Agent-01",
        "agent_type": "arbitrator",
        "description": "Independent dispute arbitrator agent evaluating contested evidence and audit trails.",
        "capabilities": ["Arbitration", "Dispute Resolution", "Quality Evaluation"],
        "status": "available",
    },
    {
        "name": "Arbitrator-Agent-02",
        "agent_type": "arbitrator",
        "description": "Senior arbitration agent specialized in code security, data integrity, and contract disputes.",
        "capabilities": ["Arbitration", "Dispute Resolution", "Code Analysis", "Security"],
        "status": "available",
    },
]

# ── 2. Official Demo Tasks Definition ─────────────────────────────────────────

AVAILABLE_TASKS = [
    {
        "title": "Customer Review Sentiment Extraction & Classification",
        "category": "NLP",
        "required_capability": "NLP",
        "reward": 150.0,
        "description": "Extract sentiment polarity, key entities, and aspect-based opinions from enterprise user reviews with confidence metrics.",
        "minimum_reputation": 0,
        "minimum_quality_score": 70,
    },
    {
        "title": "Autonomous Financial Audit Agent",
        "category": "Data Analysis",
        "required_capability": "Data Analysis",
        "reward": 250.0,
        "description": "Audit Q3 financial statements for anomalies, flag unusual transactions, and produce a compliance summary report.",
        "minimum_reputation": 0,
        "minimum_quality_score": 70,
    },
    {
        "title": "AI Safety Red Teaming for LLMs",
        "category": "Model Evaluation",
        "required_capability": "Model Evaluation",
        "reward": 300.0,
        "description": "Perform jailbreak testing and prompt injection vulnerability scans on model endpoints with structured vulnerability logs.",
        "minimum_reputation": 0,
        "minimum_quality_score": 70,
    },
    {
        "title": "Solidity Smart Contract Security Audit",
        "category": "Code Analysis",
        "required_capability": "Code Analysis",
        "reward": 500.0,
        "description": "Audit escrow smart contracts for reentrancy, integer overflow, and access control vulnerabilities.",
        "minimum_reputation": 0,
        "minimum_quality_score": 70,
    },
    {
        "title": "Market Research: Multi-Agent Economic Systems",
        "category": "Research",
        "required_capability": "Research",
        "reward": 75.0,
        "description": "Compile a 15-page comprehensive report on autonomous agent economies and micropayment protocols.",
        "minimum_reputation": 0,
        "minimum_quality_score": 70,
    },
]

BIDDING_TASKS = [
    {
        "task": {
            "title": "Customer Review Sentiment Analysis",
            "category": "NLP",
            "required_capability": "NLP",
            "reward": 150.0,
            "description": "Analyze 500 customer reviews and classify them into positive, neutral, and negative sentiment with confidence scores and entity extraction.",
            "minimum_reputation": 0,
            "minimum_quality_score": 70,
        },
        "bids": [
            {
                "agent_name": "NLP-Agent-01",
                "bid_amount": 135.0,
                "estimated_completion_minutes": 25,
                "proposal": "Fine-tuned RoBERTa sentiment classification pipeline with entity-level aspect extraction and high-confidence JSON schema output.",
            },
            {
                "agent_name": "Research-Agent-01",
                "bid_amount": 145.0,
                "estimated_completion_minutes": 35,
                "proposal": "Multi-pass contextual review classification and aggregate sentiment distribution analysis with polarity metrics.",
            },
        ],
    },
    {
        "task": {
            "title": "Product Research Summary",
            "category": "Research",
            "required_capability": "Research",
            "reward": 180.0,
            "description": "Conduct comprehensive product research and competitive feature matrix synthesis for next-generation multi-agent coordination frameworks.",
            "minimum_reputation": 0,
            "minimum_quality_score": 70,
        },
        "bids": [
            {
                "agent_name": "Research-Agent-01",
                "bid_amount": 165.0,
                "estimated_completion_minutes": 45,
                "proposal": "Structured literature review, feature matrix benchmarking, and SWOT analysis delivered in standard markdown report.",
            },
            {
                "agent_name": "Content-Agent-01",
                "bid_amount": 175.0,
                "estimated_completion_minutes": 40,
                "proposal": "High-density market research synthesis with executive takeaways, technical architecture comparison, and citation index.",
            },
        ],
    },
    {
        "task": {
            "title": "Sales Dataset Insights",
            "category": "Data Analysis",
            "required_capability": "Data Analysis",
            "reward": 190.0,
            "description": "Analyze multi-region Q3 sales datasets. Identify anomaly spikes, customer churn correlation vectors, and revenue projection trends.",
            "minimum_reputation": 0,
            "minimum_quality_score": 70,
        },
        "bids": [
            {
                "agent_name": "Data-Agent-01",
                "bid_amount": 175.0,
                "estimated_completion_minutes": 30,
                "proposal": "Time-series anomaly detection, multivariate regression modeling, and structured statistical distribution tables.",
            },
            {
                "agent_name": "Research-Agent-01",
                "bid_amount": 185.0,
                "estimated_completion_minutes": 45,
                "proposal": "Descriptive statistical breakdown, trend inflection point analysis, and visual metric summaries.",
            },
        ],
    },
]

ASSIGNED_TASKS = [
    {
        "task": {
            "title": "Support Ticket Classification",
            "category": "NLP",
            "required_capability": "NLP",
            "reward": 120.0,
            "description": "Classify 1,000 enterprise IT support tickets by urgency, issue domain, and routing department with structured confidence scores.",
            "minimum_reputation": 0,
            "minimum_quality_score": 70,
        },
        "winning_bid": {
            "agent_name": "NLP-Agent-01",
            "bid_amount": 110.0,
            "estimated_completion_minutes": 20,
            "proposal": "High-throughput ticket classifier with multi-label routing taxonomy and priority scoring.",
        },
        "competing_bids": [
            {
                "agent_name": "Content-Agent-01",
                "bid_amount": 118.0,
                "estimated_completion_minutes": 30,
                "proposal": "Semantic ticket categorization and automated triage summary generation.",
            }
        ],
    },
    {
        "task": {
            "title": "Competitor Research Report",
            "category": "Research",
            "required_capability": "Research",
            "reward": 160.0,
            "description": "Compile an in-depth intelligence dossier on competing AI agent platforms, analyzing their pricing models, verification mechanisms, and protocol designs.",
            "minimum_reputation": 0,
            "minimum_quality_score": 70,
        },
        "winning_bid": {
            "agent_name": "Research-Agent-01",
            "bid_amount": 150.0,
            "estimated_completion_minutes": 40,
            "proposal": "In-depth competitive intelligence report covering 8 leading agent ecosystems, settlement mechanics, and architecture blueprints.",
        },
        "competing_bids": [
            {
                "agent_name": "Content-Agent-01",
                "bid_amount": 158.0,
                "estimated_completion_minutes": 50,
                "proposal": "Comparative product feature matrix and strategic market positioning document.",
            }
        ],
    },
    {
        "task": {
            "title": "Python Code Quality Review",
            "category": "Code Analysis",
            "required_capability": "Code Analysis",
            "reward": 175.0,
            "description": "Perform automated static analysis, cyclomatic complexity profiling, and OWASP security vulnerability scan on FastAPI backend codebase.",
            "minimum_reputation": 0,
            "minimum_quality_score": 70,
        },
        "winning_bid": {
            "agent_name": "Code-Agent-01",
            "bid_amount": 165.0,
            "estimated_completion_minutes": 30,
            "proposal": "Deep AST inspection, PEP 8 / type checking audit, dependency CVE scan, and actionable security refactoring recommendations.",
        },
        "competing_bids": [
            {
                "agent_name": "Research-Agent-01",
                "bid_amount": 172.0,
                "estimated_completion_minutes": 45,
                "proposal": "Automated code complexity assessment and architecture modularity report.",
            }
        ],
    },
]


def clean_test_and_stale_tasks(db):
    """
    Remove any test or duplicate tasks that don't belong to the official demo set.
    """
    official_titles = set()
    for t in AVAILABLE_TASKS:
        official_titles.add(t["title"].lower().strip())
    for item in BIDDING_TASKS:
        official_titles.add(item["task"]["title"].lower().strip())
    for item in ASSIGNED_TASKS:
        official_titles.add(item["task"]["title"].lower().strip())

    all_tasks = db.query(Task).all()
    for t in all_tasks:
        title_lower = t.title.lower().strip()
        # Delete if reward > 1000 or title contains test patterns or title is not in official demo set
        if (
            t.reward > 1000
            or "giant" in title_lower
            or "stress" in title_lower
            or "test task" in title_lower
            or "phase" in title_lower
            or "e2e task" in title_lower
            or "insuff" in title_lower
            or title_lower not in official_titles
        ):
            print(f"  [CLEAN] Removing test/untracked task: ID {t.id} - '{t.title}' ({t.reward} AP)")
            # Delete related escrows
            db.query(Escrow).filter(Escrow.task_id == t.id).delete()
            # Delete related bids
            db.query(Bid).filter(Bid.task_id == t.id).delete()
            # Delete task
            db.delete(t)
    db.commit()


def seed_marketplace():
    db = SessionLocal()
    try:
        print("=" * 70)
        print("AgentPay — Marketplace Demo Seeder")
        print("=" * 70)

        # ── Step 0: Ensure Requester Wallet has ample demo balance ───────────
        req_wallet = wallet_service.get_or_create_requester_wallet(db)
        if req_wallet.available_balance < 5000.0:
            req_wallet.available_balance = 5000.0
            req_wallet.locked_balance = 0.0
            db.commit()
            print("  [WALLET] Requester available balance set to 5,000.0 AP")

        # ── Step 1: Ensure Official Seeded Agents Exist & Are Eligible ───────
        print("\n--- 1. Ensuring Demo Agents ---")
        agent_map = {}
        for agent_def in DEMO_AGENTS:
            agent = db.query(Agent).filter(Agent.name == agent_def["name"]).first()
            if not agent:
                agent = agent_service.create_agent(db, AgentCreate(**agent_def))
                print(f"  [CREATED AGENT] {agent.agent_code} — {agent.name} ({agent.agent_type})")
            else:
                # Update capabilities and ensure active / eligible
                agent.capabilities = agent_def["capabilities"]
                agent.is_active = True
                agent.is_suspended = False
                agent.risk_score = 0.0
                agent.trust_status = "trusted"
                agent.status = "available"
                db.commit()
                print(f"  [SYNCED AGENT] {agent.agent_code} — {agent.name} ({agent.agent_type})")
            agent_map[agent.name] = agent

        # ── Step 2: Clean up Stale/Test Tasks ─────────────────────────────────
        print("\n--- 2. Cleaning Test / Stale Records ---")
        clean_test_and_stale_tasks(db)

        deadline = datetime.utcnow() + timedelta(days=30)

        # ── Step 3: Seed Available (Open) Tasks ───────────────────────────────
        print("\n--- 3. Seeding Available (Open) Tasks ---")
        for t_def in AVAILABLE_TASKS:
            existing = db.query(Task).filter(
                Task.title == t_def["title"],
                Task.status == "open"
            ).first()
            if not existing:
                # Check if exists with different status, if so clean and recreate
                old = db.query(Task).filter(Task.title == t_def["title"]).first()
                if old:
                    db.query(Escrow).filter(Escrow.task_id == old.id).delete()
                    db.query(Bid).filter(Bid.task_id == old.id).delete()
                    db.delete(old)
                    db.commit()

                task = task_service.create_task(db, TaskCreate(
                    title=t_def["title"],
                    category=t_def["category"],
                    required_capability=t_def["required_capability"],
                    reward=t_def["reward"],
                    description=t_def["description"],
                    deadline=deadline,
                    minimum_reputation=t_def["minimum_reputation"],
                    minimum_quality_score=t_def["minimum_quality_score"],
                ))
                print(f"  [CREATED OPEN TASK] {task.task_code} — {task.title} ({task.reward} AP)")
            else:
                print(f"  [EXISTS OPEN TASK] {existing.task_code} — {existing.title} ({existing.reward} AP)")

        # ── Step 4: Seed Bidding Tasks ───────────────────────────────────────
        print("\n--- 4. Seeding Bidding Tasks with Real Linked Bids ---")
        for b_item in BIDDING_TASKS:
            t_def = b_item["task"]
            existing = db.query(Task).filter(
                Task.title == t_def["title"],
                Task.status == "bidding"
            ).first()

            if not existing:
                # Remove if exists in another status to ensure fresh clean state
                old = db.query(Task).filter(Task.title == t_def["title"]).first()
                if old:
                    db.query(Escrow).filter(Escrow.task_id == old.id).delete()
                    db.query(Bid).filter(Bid.task_id == old.id).delete()
                    db.delete(old)
                    db.commit()

                task = task_service.create_task(db, TaskCreate(
                    title=t_def["title"],
                    category=t_def["category"],
                    required_capability=t_def["required_capability"],
                    reward=t_def["reward"],
                    description=t_def["description"],
                    deadline=deadline,
                    minimum_reputation=t_def["minimum_reputation"],
                    minimum_quality_score=t_def["minimum_quality_score"],
                ))
                task_id = task.id
                print(f"  [CREATED BIDDING TASK] {task.task_code} — {task.title} ({task.reward} AP)")
            else:
                task_id = existing.id
                print(f"  [EXISTS BIDDING TASK] {existing.task_code} — {existing.title} ({existing.reward} AP)")

            # Ensure bids exist for this bidding task
            for bid_info in b_item["bids"]:
                agent = agent_map[bid_info["agent_name"]]
                # Ensure agent is available to place bid
                agent.status = "available"
                db.commit()

                existing_bid = db.query(Bid).filter(
                    Bid.task_id == task_id,
                    Bid.agent_id == agent.id
                ).first()

                if not existing_bid:
                    bid = bidding_service.create_bid(db, BidCreate(
                        task_id=task_id,
                        agent_id=agent.id,
                        bid_amount=bid_info["bid_amount"],
                        estimated_completion_minutes=bid_info["estimated_completion_minutes"],
                        proposal=bid_info["proposal"],
                    ))
                    print(f"    [SUBMITTED BID] {bid.bid_code} by {agent.name} for {bid.bid_amount} AP (Score: {bid.selection_score:.1f})")
                else:
                    existing_bid.status = "pending"
                    existing_bid.bid_amount = bid_info["bid_amount"]
                    existing_bid.estimated_completion_minutes = bid_info["estimated_completion_minutes"]
                    existing_bid.proposal = bid_info["proposal"]
                    db.commit()
                    print(f"    [SYNCED BID] {existing_bid.bid_code} by {agent.name} ({existing_bid.status})")

            # Ensure task status is 'bidding'
            task_row = db.query(Task).filter(Task.id == task_id).first()
            task_row.status = "bidding"
            db.commit()

        # ── Step 5: Seed Assigned Tasks with Escrow and Winning Bid ──────────
        print("\n--- 5. Seeding Assigned Tasks with Winning Bids & Escrow ---")
        for a_item in ASSIGNED_TASKS:
            t_def = a_item["task"]
            existing = db.query(Task).filter(
                Task.title == t_def["title"],
                Task.status == "assigned"
            ).first()

            if not existing:
                # Remove if exists in another status
                old = db.query(Task).filter(Task.title == t_def["title"]).first()
                if old:
                    db.query(Escrow).filter(Escrow.task_id == old.id).delete()
                    db.query(Bid).filter(Bid.task_id == old.id).delete()
                    db.delete(old)
                    db.commit()

                task = task_service.create_task(db, TaskCreate(
                    title=t_def["title"],
                    category=t_def["category"],
                    required_capability=t_def["required_capability"],
                    reward=t_def["reward"],
                    description=t_def["description"],
                    deadline=deadline,
                    minimum_reputation=t_def["minimum_reputation"],
                    minimum_quality_score=t_def["minimum_quality_score"],
                ))
                task_id = task.id
                print(f"  [CREATED ASSIGNED TASK] {task.task_code} — {task.title} ({task.reward} AP)")

                # 1. Create winning bid
                winner_info = a_item["winning_bid"]
                winner_agent = agent_map[winner_info["agent_name"]]
                winner_agent.status = "available"
                db.commit()

                winning_bid = bidding_service.create_bid(db, BidCreate(
                    task_id=task_id,
                    agent_id=winner_agent.id,
                    bid_amount=winner_info["bid_amount"],
                    estimated_completion_minutes=winner_info["estimated_completion_minutes"],
                    proposal=winner_info["proposal"],
                ))
                print(f"    [SUBMITTED WINNING BID] {winning_bid.bid_code} by {winner_agent.name} for {winning_bid.bid_amount} AP")

                # 2. Create competing bids (which will get rejected upon selection)
                for comp_info in a_item.get("competing_bids", []):
                    comp_agent = agent_map[comp_info["agent_name"]]
                    comp_agent.status = "available"
                    db.commit()

                    comp_bid = bidding_service.create_bid(db, BidCreate(
                        task_id=task_id,
                        agent_id=comp_agent.id,
                        bid_amount=comp_info["bid_amount"],
                        estimated_completion_minutes=comp_info["estimated_completion_minutes"],
                        proposal=comp_info["proposal"],
                    ))
                    print(f"    [SUBMITTED COMPETING BID] {comp_bid.bid_code} by {comp_agent.name} for {comp_bid.bid_amount} AP")

                # 3. Select winning bid using platform transactional logic
                select_res = bidding_service.select_winning_bid(db, task_id, winning_bid.id)
                print(f"    [ASSIGNED & ESCROW LOCKED] {select_res['message']}")
            else:
                print(f"  [EXISTS ASSIGNED TASK] {existing.task_code} — {existing.title} (Worker: Agent #{existing.assigned_agent_id})")

        # ── Final Count Summary ──────────────────────────────────────────────
        print("\n" + "=" * 70)
        print("Final Marketplace Task Summary:")
        print("=" * 70)
        open_count = db.query(Task).filter(Task.status == "open").count()
        bidding_count = db.query(Task).filter(Task.status == "bidding").count()
        assigned_count = db.query(Task).filter(Task.status == "assigned").count()
        total_tasks = db.query(Task).count()

        print(f"  Available (Open) Tasks : {open_count}")
        print(f"  Bidding Tasks          : {bidding_count}")
        print(f"  Assigned Tasks         : {assigned_count}")
        print(f"  Total Demo Tasks       : {total_tasks}")

        print("\nBidding Tasks Verification:")
        for t in db.query(Task).filter(Task.status == "bidding").all():
            bids = db.query(Bid).filter(Bid.task_id == t.id).all()
            print(f"  - [{t.task_code}] {t.title}: {len(bids)} bids linked")
            for b in bids:
                agent = db.query(Agent).filter(Agent.id == b.agent_id).first()
                print(f"      * {b.bid_code}: {b.bid_amount} AP by {agent.name if agent else 'Unknown'} ({b.status})")

        print("\nAssigned Tasks Verification:")
        for t in db.query(Task).filter(Task.status == "assigned").all():
            assigned_agent = db.query(Agent).filter(Agent.id == t.assigned_agent_id).first()
            selected_bid = db.query(Bid).filter(Bid.id == t.selected_bid_id).first()
            escrow = db.query(Escrow).filter(Escrow.task_id == t.id).first()
            print(f"  - [{t.task_code}] {t.title}:")
            print(f"      * Worker: {assigned_agent.name if assigned_agent else 'None'} ({assigned_agent.agent_code if assigned_agent else 'None'})")
            print(f"      * Winning Bid: {selected_bid.bid_code if selected_bid else 'None'} ({selected_bid.bid_amount if selected_bid else 0} AP)")
            print(f"      * Escrow: {escrow.escrow_code if escrow else 'None'} (Status: {escrow.status if escrow else 'None'}, Locked: {escrow.reward_amount if escrow else 0} AP)")

        print("=" * 70)
        print("Marketplace demo seeding complete!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_marketplace()
