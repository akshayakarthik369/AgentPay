from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Import Base and engine first, then all models so that
# create_all() knows about every table before it runs.
from database import engine, Base, get_db, run_migrations

# Importing models here registers them with Base.metadata
from app.models.task import Task  # noqa: F401
from app.models.agent import Agent  # noqa: F401
from app.models.bid import Bid  # noqa: F401
from app.models.task_execution import TaskExecution, ExecutionLog  # noqa: F401
from app.models.result_submission import ResultSubmission, SubmissionAuditLog  # noqa: F401
from app.models.verification import Verification, VerificationAuditLog  # noqa: F401
from app.models.wallet import Wallet  # noqa: F401
from app.models.escrow import Escrow, EscrowAuditLog  # noqa: F401
from app.models.settlement import Settlement, SettlementAuditLog, LedgerEntry  # noqa: F401
from app.models.reputation import ReputationEvent  # noqa: F401
from app.models.human_review import HumanReview, HumanReviewAuditLog  # noqa: F401
from app.models.dispute import Dispute, DisputeEvidence, DisputeAuditLog  # noqa: F401
from app.models.arbitration import Arbitration, ArbitrationAuditLog  # noqa: F401

# Import routers
from app.routers.tasks import router as tasks_router
from app.routers.marketplace import router as marketplace_router
from app.routers.agents import router as agents_router
from app.routers.bids import router as bids_router
from app.routers.executions import router as executions_router
from app.routers.submissions import router as submissions_router
from app.routers.verifications import router as verifications_router
from app.routers.wallets import router as wallets_router
from app.routers.escrows import router as escrows_router
from app.routers.settlements import router as settlements_router
from app.routers.reputation import router as reputation_router
from app.routers.reviews import router as reviews_router
from app.routers.disputes import router as disputes_router
from app.routers.arbitrations import router as arbitrations_router

# Import services
from app.services.task_service import get_dashboard_metrics
from app.services.wallet_service import get_or_create_requester_wallet
from app.services.wallet_service import get_or_create_agent_wallet

# Create all database tables (idempotent — safe on every startup)
Base.metadata.create_all(bind=engine)
# Run column additions on existing SQLite database safely
run_migrations()

# Phase 11: Seed requester wallet (idempotent — only creates if not already exists)
def _seed_wallet_on_startup():
    from database import SessionLocal
    db = SessionLocal()
    try:
        get_or_create_requester_wallet(db, seed_amount=5000.0)
        # Seed agent wallets for all existing agents
        from app.models.agent import Agent
        agents = db.query(Agent).all()
        for agent in agents:
            get_or_create_agent_wallet(db, agent.id)
        db.commit()
    except Exception as e:
        print(f"Wallet seeding note: {e}")
    finally:
        db.close()

_seed_wallet_on_startup()

app = FastAPI(
    title="AgentPay API",
    description="Autonomous Economic Platform API for AI Agents",
    version="0.16.0",
)

# ---------------------------------------------------------------------------
# CORS — allow Vite dev server on 5173 and 3000
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(tasks_router)
app.include_router(marketplace_router)
app.include_router(agents_router)
app.include_router(bids_router)
app.include_router(executions_router)
app.include_router(submissions_router)
app.include_router(verifications_router)
app.include_router(wallets_router)
app.include_router(escrows_router)
app.include_router(settlements_router)
app.include_router(reputation_router)
app.include_router(reviews_router)
app.include_router(disputes_router)
app.include_router(arbitrations_router)


# ---------------------------------------------------------------------------
# Core endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["System"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/client/dashboard", tags=["Client"])
def get_client_dashboard(db: Session = Depends(get_db)):
    """
    Client dashboard summary metrics.
    total_tasks, active_tasks, completed_tasks come from the real Task table.
    """
    return get_dashboard_metrics(db)


@app.get("/", tags=["System"])
def root():
    return {
        "message": "Welcome to AgentPay API v0.8.0",
        "documentation": "/docs",
        "health": "/api/health",
        "client_dashboard": "/api/client/dashboard",
        "tasks": "/api/tasks",
        "marketplace_stats": "/api/marketplace/stats",
        "agents": "/api/agents",
        "executions": "/api/executions/{id}",
    }
