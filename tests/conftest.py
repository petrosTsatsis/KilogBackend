import os

# --- 1. MOCK ENVIRONMENT VARIABLES ---
# We must do this BEFORE importing any part of the app.
# Pydantic loads settings as soon as you import 'app.main' or 'app.models',
# so these keys must exist in os.environ first.

os.environ["JWT_KEY"] = "testing_jwt_key"
os.environ["CLERK_SECRET_KEY"] = "testing_clerk_secret"
os.environ["CLERK_WEBHOOK_SECRET"] = "testing_clerk_webhook"
os.environ["RESEND_API_KEY"] = "testing_resend_key"
os.environ["SUPABASE_URL"] = "https://testing-supabase.com"
os.environ["SUPABASE_KEY"] = "testing_supabase_key"
os.environ["PROJECT_NAME"] = "TestFitApp"

# Database override (prevents using your real DB)
os.environ["POSTGRES_USER"] = "user"
os.environ["POSTGRES_PASSWORD"] = "password"
os.environ["POSTGRES_DB"] = "test_db"
os.environ["DATABASE_URL"] = "postgresql://user:password@localhost:5432/test_db"

# --- 2. NOW IMPORTS ARE SAFE ---
import pytest
from app.database import engine, SessionLocal, Base


# --- 3. DATABASE FIXTURES ---

@pytest.fixture(scope="session")
def db_engine():
    """
    Creates the test database schema once for the entire test session.
    """
    # Create all tables (User, Workout, Exercise, etc.)
    Base.metadata.create_all(bind=engine)
    yield engine
    # Cleanup: Drop tables after tests finish
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def mock_db(db_engine):
    """
    Creates a fresh, isolated database session for a single test.
    Rolls back any changes (INSERT/UPDATE) after the test finishes.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
