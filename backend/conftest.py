"""
conftest.py — Test DB Isolation for AgentPay Backend Tests

Every pytest session uses an in-memory SQLite database that is:
  - Created fresh at session start
  - Destroyed at session end
  - NEVER touches agentpay.db (the development / demo database)

This file is auto-discovered by pytest and applies to ALL test_phase*.py files.
"""
import os
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# ── Redirect database BEFORE importing anything from the app ─────────────────
# Point to a fresh in-memory DB for this test session only.
TEST_DB_URL = "sqlite:///:memory:"

# Patch the database module BEFORE the app loads its engine
import database as _db_module

_test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
)
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

# Replace the module-level engine and SessionLocal used by the app
_db_module.engine = _test_engine
_db_module.SessionLocal = _TestSessionLocal

# Now import the app (it will use the patched engine/SessionLocal)
from main import app
from database import Base, get_db


def override_get_db():
    """Dependency override: always use the test in-memory session."""
    db = _TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override FastAPI's DB dependency so all routers use the test DB
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables in the in-memory DB at session start, drop at end."""
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture(scope="session")
def client(setup_test_database):
    """Provide a TestClient wired to the in-memory test DB."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def db(setup_test_database):
    """Provide a fresh DB session per test function, rolling back after each test."""
    connection = _test_engine.connect()
    transaction = connection.begin()
    session = _TestSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
