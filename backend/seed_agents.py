"""
Idempotent seed script for AgentPay demo agents.
Run once to populate the database with 5 demo agents.
Running again will NOT create duplicates — agents are matched by name.

Usage:
  cd agentpay/backend
  .\\venv\\Scripts\\python.exe seed_agents.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from app.models.agent import Agent  # noqa: registers model
from app.services.agent_service import create_agent, get_agents
from app.schemas.agent import AgentCreate

DEMO_AGENTS = [
    {
        "name": "NLP-Agent-01",
        "agent_type": "worker",
        "description": "Autonomous AI agent specialized in natural language processing, sentiment analysis, and text summarization tasks.",
        "capabilities": ["NLP", "Sentiment Analysis", "Summarization"],
        "status": "available",
    },
    {
        "name": "Research-Agent-01",
        "agent_type": "worker",
        "description": "Autonomous research agent that synthesizes academic papers, extracts key findings, and produces structured summaries.",
        "capabilities": ["Research", "Summarization"],
        "status": "available",
    },
    {
        "name": "Data-Agent-01",
        "agent_type": "worker",
        "description": "Specialist data analysis agent. Handles time-series anomaly detection, statistical inference, and classification pipelines.",
        "capabilities": ["Data Analysis", "Classification"],
        "status": "available",
    },
    {
        "name": "Code-Agent-01",
        "agent_type": "worker",
        "description": "Static analysis and security audit agent. Performs OWASP Top 10 scanning and code quality assessments.",
        "capabilities": ["Code Analysis"],
        "status": "available",
    },
    {
        "name": "Verify-Agent-01",
        "agent_type": "verifier",
        "description": "Independent verifier agent responsible for auditing submitted task results against quality thresholds and format compliance criteria.",
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
]



def seed():
    db = SessionLocal()
    try:
        existing_agents = {a.name.lower() for a in get_agents(db)}
        created = 0
        skipped = 0

        for demo in DEMO_AGENTS:
            name_lower = demo["name"].lower()
            if name_lower in existing_agents:
                print(f"  [SKIP] '{demo['name']}' already exists.")
                skipped += 1
            else:
                agent = create_agent(db, AgentCreate(**demo))
                print(f"  [CREATED] {agent.agent_code} — {agent.name} ({agent.agent_type})")
                created += 1

        print(f"\nSeeding complete: {created} created, {skipped} skipped.")
    finally:
        db.close()


if __name__ == "__main__":
    print("=== AgentPay — Seeding Demo Agents ===")
    seed()
