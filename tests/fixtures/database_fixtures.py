"""
Database Fixtures
Test database setup, teardown, and helper functions for PostgreSQL and Redis
"""

import pytest
import asyncio
from typing import Generator, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(scope="function")
def temp_db_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for database files.

    Yields:
        Path to temporary directory (cleaned up after test)
    """
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def test_db_engine(temp_db_dir: Path):
    """
    Create a test SQLAlchemy engine with SQLite in-memory database.

    Args:
        temp_db_dir: Temporary directory fixture

    Yields:
        SQLAlchemy engine for testing
    """
    # Create in-memory SQLite database for fast testing
    # Using StaticPool to share connection across threads
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )

    yield engine

    # Cleanup
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """
    Create a test database session with automatic transaction rollback.

    This fixture creates tables, provides a session, and rolls back
    all changes after the test completes.

    Args:
        test_db_engine: Test database engine fixture

    Yields:
        SQLAlchemy session for testing
    """
    from src.database.models import Base

    # Create all tables
    Base.metadata.create_all(test_db_engine)

    # Create session
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()

    # Begin nested transaction for rollback
    connection = test_db_engine.connect()
    transaction = connection.begin()

    # Bind session to transaction
    session_with_transaction = SessionLocal(bind=connection)

    yield session_with_transaction

    # Rollback transaction
    session_with_transaction.close()
    transaction.rollback()
    connection.close()

    # Drop all tables
    Base.metadata.drop_all(test_db_engine)


@pytest.fixture(scope="function")
async def async_test_db_session(test_db_engine):
    """
    Create an async test database session.

    Args:
        test_db_engine: Test database engine fixture

    Yields:
        Async SQLAlchemy session for testing
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    from src.database.models import Base

    # Create async engine
    async_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )

    # Create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Create session
    async with async_session_maker() as session:
        yield session

    # Cleanup
    await async_engine.dispose()


@pytest.fixture(scope="function")
def mock_redis_client():
    """
    Create a mock Redis client for testing.

    Returns:
        Mock Redis client with basic operations
    """
    class MockRedis:
        def __init__(self):
            self.data: Dict[str, Any] = {}
            self.expiry: Dict[str, datetime] = {}

        async def get(self, key: str) -> Any:
            """Get value from mock Redis"""
            if key in self.expiry:
                if datetime.now() > self.expiry[key]:
                    del self.data[key]
                    del self.expiry[key]
                    return None
            return self.data.get(key)

        async def set(self, key: str, value: Any, ex: int = None) -> bool:
            """Set value in mock Redis"""
            self.data[key] = value
            if ex:
                from datetime import timedelta
                self.expiry[key] = datetime.now() + timedelta(seconds=ex)
            return True

        async def delete(self, key: str) -> int:
            """Delete key from mock Redis"""
            if key in self.data:
                del self.data[key]
                if key in self.expiry:
                    del self.expiry[key]
                return 1
            return 0

        async def exists(self, key: str) -> int:
            """Check if key exists"""
            if key in self.data:
                if key in self.expiry and datetime.now() > self.expiry[key]:
                    del self.data[key]
                    del self.expiry[key]
                    return 0
                return 1
            return 0

        async def ttl(self, key: str) -> int:
            """Get time to live for key"""
            if key in self.expiry:
                ttl = (self.expiry[key] - datetime.now()).total_seconds()
                return int(ttl) if ttl > 0 else -2
            return -1 if key in self.data else -2

        async def keys(self, pattern: str = "*") -> list:
            """Get keys matching pattern"""
            if pattern == "*":
                return list(self.data.keys())
            # Simple pattern matching
            import re
            regex_pattern = pattern.replace("*", ".*")
            return [k for k in self.data.keys() if re.match(regex_pattern, k)]

        async def flushall(self) -> bool:
            """Clear all data"""
            self.data.clear()
            self.expiry.clear()
            return True

        async def ping(self) -> bool:
            """Ping Redis"""
            return True

        async def close(self):
            """Close connection"""
            pass

    return MockRedis()


@pytest.fixture(scope="function")
def seed_customers(test_db_session: Session):
    """
    Seed test database with customer data.

    Args:
        test_db_session: Test database session

    Returns:
        List of created customer IDs
    """
    from src.database.models import Customer
    from datetime import date, timedelta

    customers = []
    for i in range(5):
        customer = Customer(
            client_id=f"cs_{1696800000 + i}_test",
            client_name=f"Test Customer {i+1}",
            company_name=f"Test Corp {i+1}",
            industry="Technology",
            tier=["starter", "standard", "professional", "enterprise"][i % 4],
            lifecycle_stage=["onboarding", "active", "at_risk", "expansion"][i % 4],
            contract_value=12000 * (i + 1),
            contract_start_date=date.today() - timedelta(days=180),
            contract_end_date=date.today() + timedelta(days=180),
            renewal_date=date.today() + timedelta(days=180),
            primary_contact_email=f"test{i+1}@example.com",
            primary_contact_name=f"Test User {i+1}",
            csm_assigned=f"CSM {i % 2 + 1}",
            health_score=50 + (i * 10),
            health_trend=["improving", "stable", "declining"][i % 3],
            status="active",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        test_db_session.add(customer)
        customers.append(customer.client_id)

    test_db_session.commit()
    return customers


@pytest.fixture(scope="function")
def seed_health_scores(test_db_session: Session, seed_customers):
    """
    Seed test database with health score data.

    Args:
        test_db_session: Test database session
        seed_customers: Customer seeding fixture

    Returns:
        List of created health score IDs
    """
    from src.database.models import HealthScore

    health_scores = []
    for i, client_id in enumerate(seed_customers):
        health_score = HealthScore(
            client_id=client_id,
            health_score=50 + (i * 10),
            usage_score=55.0 + (i * 8),
            engagement_score=45.0 + (i * 9),
            support_score=60.0 + (i * 7),
            satisfaction_score=50.0 + (i * 8),
            payment_score=95.0 + i,
            calculated_at=datetime.now(),
            trend="improving" if i % 2 == 0 else "stable"
        )
        test_db_session.add(health_score)
        health_scores.append(health_score.id)

    test_db_session.commit()
    return health_scores


@pytest.fixture(scope="function")
def seed_support_tickets(test_db_session: Session, seed_customers):
    """
    Seed test database with support ticket data.

    Args:
        test_db_session: Test database session
        seed_customers: Customer seeding fixture

    Returns:
        List of created ticket IDs
    """
    from src.database.models import SupportTicket

    tickets = []
    statuses = ["open", "pending", "in_progress", "resolved", "closed"]
    priorities = ["low", "medium", "high", "critical"]

    for i, client_id in enumerate(seed_customers):
        # Create 2 tickets per customer
        for j in range(2):
            ticket = SupportTicket(
                ticket_id=f"TICKET-{10000 + i*2 + j}",
                client_id=client_id,
                subject=f"Test Issue {i*2 + j + 1}",
                description=f"Test ticket description for issue {i*2 + j + 1}",
                status=statuses[(i*2 + j) % len(statuses)],
                priority=priorities[(i*2 + j) % len(priorities)],
                category="technical",
                created_at=datetime.now() - timedelta(days=i*2 + j),
                updated_at=datetime.now(),
                assigned_to=f"Support Team {chr(65 + ((i*2 + j) % 3))}",
                requester_email=f"test{i+1}@example.com",
                requester_name=f"Test User {i+1}"
            )
            test_db_session.add(ticket)
            tickets.append(ticket.ticket_id)

    test_db_session.commit()
    return tickets


@pytest.fixture(scope="function")
def seed_onboarding_plans(test_db_session: Session, seed_customers):
    """
    Seed test database with onboarding plan data.

    Args:
        test_db_session: Test database session
        seed_customers: Customer seeding fixture

    Returns:
        List of created plan IDs
    """
    from src.database.models import OnboardingPlan

    plans = []
    for i, client_id in enumerate(seed_customers):
        plan = OnboardingPlan(
            plan_id=f"onb_plan_{i+1:03d}",
            client_id=client_id,
            plan_name=f"Onboarding Plan {i+1}",
            status=["not_started", "in_progress", "completed"][i % 3],
            start_date=date.today() - timedelta(days=i*14),
            target_completion_date=date.today() + timedelta(days=90 - i*10),
            completion_percentage=min(100, i * 25),
            csm_assigned=f"CSM {i % 2 + 1}",
            created_at=datetime.now() - timedelta(days=i*14 + 7)
        )
        test_db_session.add(plan)
        plans.append(plan.plan_id)

    test_db_session.commit()
    return plans


# Database helper functions
def clear_all_tables(session: Session):
    """
    Clear all data from database tables.

    Args:
        session: SQLAlchemy session
    """
    from src.database.models import Base

    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()


def count_records(session: Session, model) -> int:
    """
    Count records in a table.

    Args:
        session: SQLAlchemy session
        model: SQLAlchemy model class

    Returns:
        Number of records
    """
    return session.query(model).count()


def get_by_id(session: Session, model, record_id: Any):
    """
    Get record by ID.

    Args:
        session: SQLAlchemy session
        model: SQLAlchemy model class
        record_id: Record identifier

    Returns:
        Model instance or None
    """
    return session.query(model).filter(model.id == record_id).first()


def create_test_customer(session: Session, **kwargs) -> str:
    """
    Create a test customer with custom attributes.

    Args:
        session: SQLAlchemy session
        **kwargs: Customer attributes

    Returns:
        Customer client_id
    """
    from src.database.models import Customer
    from datetime import date, timedelta

    defaults = {
        "client_id": f"cs_{int(datetime.now().timestamp())}_test",
        "client_name": "Test Customer",
        "company_name": "Test Corp",
        "industry": "Technology",
        "tier": "standard",
        "lifecycle_stage": "active",
        "contract_value": 24000.0,
        "contract_start_date": date.today(),
        "contract_end_date": date.today() + timedelta(days=365),
        "renewal_date": date.today() + timedelta(days=365),
        "status": "active"
    }

    customer_data = {**defaults, **kwargs}
    customer = Customer(**customer_data)
    session.add(customer)
    session.commit()

    return customer.client_id


def create_test_health_score(session: Session, client_id: str, **kwargs) -> int:
    """
    Create a test health score for a customer.

    Args:
        session: SQLAlchemy session
        client_id: Customer identifier
        **kwargs: Health score attributes

    Returns:
        Health score ID
    """
    from src.database.models import HealthScore

    defaults = {
        "client_id": client_id,
        "health_score": 75,
        "usage_score": 80.0,
        "engagement_score": 70.0,
        "support_score": 85.0,
        "satisfaction_score": 75.0,
        "payment_score": 100.0,
        "trend": "stable",
        "calculated_at": datetime.now()
    }

    score_data = {**defaults, **kwargs}
    health_score = HealthScore(**score_data)
    session.add(health_score)
    session.commit()

    return health_score.id
