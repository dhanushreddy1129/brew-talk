"""Pytest fixtures for Brew Talk API tests."""

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure the backend package is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import Base, get_db
from app.db.models import MenuItem, Order, OrderItem, Setting  # noqa: F401
from app.db.seed import seed_database
from app.main import app

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Yield a test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the DB dependency globally
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables and seed data once per test session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    """Provide a TestClient instance."""
    return TestClient(app)


@pytest.fixture()
def db():
    """Provide a raw database session for direct queries in tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def admin_headers():
    """Headers with a valid admin key."""
    return {"X-Admin-Key": "brewtalk2024"}
