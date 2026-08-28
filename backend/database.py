import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite connection URL
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "agentpay.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# create_engine with check_same_thread=False for SQLite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# SessionLocal for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

def get_db():
    """Dependency for obtaining database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_migrations():
    """Safely apply column additions to existing SQLite tables if not present."""
    from sqlalchemy import text
    with engine.connect() as conn:
        # Check columns in tasks table
        try:
            res = conn.execute(text("PRAGMA table_info(tasks)"))
            existing_columns = {row[1] for row in res.fetchall()}
            
            if existing_columns: # table exists
                if "assigned_agent_id" not in existing_columns:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN assigned_agent_id INTEGER REFERENCES agents(id)"))
                if "selected_bid_id" not in existing_columns:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN selected_bid_id INTEGER REFERENCES bids(id)"))
                if "assigned_at" not in existing_columns:
                    conn.execute(text("ALTER TABLE tasks ADD COLUMN assigned_at DATETIME"))
                conn.commit()
        except Exception as e:
            print(f"Migration note (tasks): {e}")

        # Check columns in agents table
        try:
            res = conn.execute(text("PRAGMA table_info(agents)"))
            existing_columns = {row[1] for row in res.fetchall()}

            if existing_columns:
                if "tasks_failed" not in existing_columns:
                    conn.execute(text("ALTER TABLE agents ADD COLUMN tasks_failed INTEGER DEFAULT 0"))
                conn.commit()
        except Exception as e:
            print(f"Migration note (agents): {e}")
