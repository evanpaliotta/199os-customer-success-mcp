"""
Pytest Configuration and Shared Fixtures

This module contains pytest configuration and shared fixtures used across all tests.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, Any
from faker import Faker

# Import models for type hints
from src.models.customer_models import (
    CustomerAccount, HealthScoreComponents, CustomerSegment,
    RiskIndicator, ChurnPrediction, CustomerTier, LifecycleStage,
    HealthTrend, AccountStatus
)

# Import test fixtures - using relative imports
tests_dir = Path(__file__).parent
sys.path.insert(0, str(tests_dir))

from fixtures.cs_fixtures import *
from fixtures.api_fixtures import *
from fixtures.database_fixtures import *

# Initialize Faker for generating test data
fake = Faker()

# ============================================================================
# Event Loop Configuration
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Basic Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_client_id() -> str:
    """Generate a valid client ID for testing."""
    timestamp = int(datetime.now().timestamp())
    company_slug = fake.company().lower().replace(" ", "_").replace(",", "")[:20]
    return f"cs_{timestamp}_{company_slug}"


@pytest.fixture
def sample_email() -> str:
    """Generate a valid email address for testing."""
    return fake.email()


@pytest.fixture
def sample_date() -> date:
    """Generate a sample date for testing."""
    return date.today()


@pytest.fixture
def sample_datetime() -> datetime:
    """Generate a sample datetime for testing."""
    return datetime.now()


# ============================================================================
# Customer Account Fixtures
# ============================================================================

@pytest.fixture
def sample_customer_account(sample_client_id: str) -> CustomerAccount:
    """Create a sample CustomerAccount for testing."""
    return CustomerAccount(
        client_id=sample_client_id,
        client_name=fake.company(),
        company_name=fake.company() + " Inc.",
        industry=fake.random_element(["SaaS", "Technology", "Healthcare", "Finance", "E-commerce"]),
        tier=CustomerTier.PROFESSIONAL,
        lifecycle_stage=LifecycleStage.ACTIVE,
        contract_value=72000.0,
        contract_start_date=date.today() - timedelta(days=180),
        contract_end_date=date.today() + timedelta(days=185),
        renewal_date=date.today() + timedelta(days=185),
        primary_contact_email=fake.email(),
        primary_contact_name=fake.name(),
        csm_assigned=fake.name(),
        health_score=82,
        health_trend=HealthTrend.IMPROVING,
        last_engagement_date=datetime.now() - timedelta(days=2),
        status=AccountStatus.ACTIVE
    )


@pytest.fixture
def sample_customer_accounts(sample_client_id: str) -> list[CustomerAccount]:
    """Create multiple sample CustomerAccount objects for testing."""
    accounts = []
    for i in range(5):
        timestamp = int(datetime.now().timestamp()) + i
        company_slug = fake.company().lower().replace(" ", "_").replace(",", "")[:20]
        client_id = f"cs_{timestamp}_{company_slug}"

        accounts.append(CustomerAccount(
            client_id=client_id,
            client_name=fake.company(),
            company_name=fake.company() + " Inc.",
            industry=fake.random_element(["SaaS", "Technology", "Healthcare", "Finance"]),
            tier=fake.random_element(list(CustomerTier)),
            lifecycle_stage=fake.random_element(list(LifecycleStage)),
            contract_value=fake.random_int(min=10000, max=500000),
            contract_start_date=date.today() - timedelta(days=fake.random_int(min=30, max=730)),
            contract_end_date=date.today() + timedelta(days=fake.random_int(min=30, max=365)),
            renewal_date=date.today() + timedelta(days=fake.random_int(min=30, max=365)),
            primary_contact_email=fake.email(),
            primary_contact_name=fake.name(),
            csm_assigned=fake.name(),
            health_score=fake.random_int(min=20, max=100),
            health_trend=fake.random_element(list(HealthTrend)),
            last_engagement_date=datetime.now() - timedelta(days=fake.random_int(min=1, max=30)),
            status=AccountStatus.ACTIVE
        ))
    return accounts


# ============================================================================
# Health Score Fixtures
# ============================================================================

@pytest.fixture
def sample_health_score_components() -> HealthScoreComponents:
    """Create sample HealthScoreComponents for testing."""
    return HealthScoreComponents(
        usage_score=85.0,
        engagement_score=78.0,
        support_score=92.0,
        satisfaction_score=88.0,
        payment_score=100.0,
        usage_weight=0.35,
        engagement_weight=0.25,
        support_weight=0.15,
        satisfaction_weight=0.15,
        payment_weight=0.10
    )


@pytest.fixture
def sample_health_score_components_varied() -> list[HealthScoreComponents]:
    """Create multiple varied HealthScoreComponents for testing."""
    return [
        HealthScoreComponents(
            usage_score=95.0, engagement_score=88.0, support_score=92.0,
            satisfaction_score=90.0, payment_score=100.0
        ),
        HealthScoreComponents(
            usage_score=45.0, engagement_score=40.0, support_score=60.0,
            satisfaction_score=50.0, payment_score=70.0
        ),
        HealthScoreComponents(
            usage_score=75.0, engagement_score=70.0, support_score=80.0,
            satisfaction_score=78.0, payment_score=95.0
        )
    ]


# ============================================================================
# Customer Segment Fixtures
# ============================================================================

@pytest.fixture
def sample_customer_segment() -> CustomerSegment:
    """Create a sample CustomerSegment for testing."""
    return CustomerSegment(
        segment_id="seg_high_value_saas",
        segment_name="High-Value SaaS Accounts",
        segment_type="value_based",
        criteria={
            "min_arr": 50000,
            "industry": ["SaaS", "Technology"],
            "tier": ["professional", "enterprise"]
        },
        characteristics={
            "typical_team_size": "50-200",
            "typical_arr": "50k-200k",
            "growth_stage": "scale-up"
        },
        engagement_strategy={
            "csm_touch_frequency": "weekly",
            "ebr_frequency": "quarterly",
            "success_programs": ["technical_advisory", "strategic_planning"]
        },
        success_metrics={
            "target_health_score": 85.0,
            "target_nps": 50.0,
            "target_retention_rate": 0.95
        },
        customer_count=47,
        total_arr=4235000.0,
        avg_health_score=82.3
    )


# ============================================================================
# Risk and Churn Fixtures
# ============================================================================

@pytest.fixture
def sample_risk_indicator() -> RiskIndicator:
    """Create a sample RiskIndicator for testing."""
    return RiskIndicator(
        indicator_id="risk_low_engagement",
        indicator_name="Low Product Engagement",
        category="engagement",
        severity="high",
        current_value=2.3,
        threshold_value=5.0,
        description="Weekly active users below threshold",
        detected_at=datetime.now(),
        mitigation_actions=[
            "Schedule check-in call",
            "Provide training resources",
            "Activate engagement campaign"
        ]
    )


@pytest.fixture
def sample_churn_prediction(sample_client_id: str) -> ChurnPrediction:
    """Create a sample ChurnPrediction for testing."""
    return ChurnPrediction(
        client_id=sample_client_id,
        prediction_date=datetime.now(),
        churn_probability=0.23,
        churn_risk_level="low",
        confidence_score=0.87,
        contributing_factors=[
            {"factor": "decreased_login_frequency", "weight": 0.35},
            {"factor": "support_ticket_volume_increase", "weight": 0.25},
            {"factor": "feature_adoption_decline", "weight": 0.20}
        ],
        risk_indicators=[],
        predicted_churn_date=date.today() + timedelta(days=90),
        retention_recommendations=[
            "Increase CSM touchpoints to weekly",
            "Provide advanced feature training",
            "Address support ticket backlog"
        ],
        model_version="v2.3.1"
    )


# ============================================================================
# Mock Environment Configuration
# ============================================================================

@pytest.fixture
def mock_env_vars(monkeypatch) -> Dict[str, str]:
    """Set up mock environment variables for testing."""
    env_vars = {
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test_cs_mcp",
        "REDIS_URL": "redis://localhost:6379/0",
        "ENCRYPTION_KEY": "test_encryption_key_32_chars_long",
        "JWT_SECRET": "test_jwt_secret_32_characters_long",
        "LOG_LEVEL": "DEBUG",
        "ZENDESK_SUBDOMAIN": "test",
        "ZENDESK_EMAIL": "test@test.com",
        "ZENDESK_API_TOKEN": "test_token",
        "INTERCOM_ACCESS_TOKEN": "test_intercom_token",
        "MIXPANEL_PROJECT_TOKEN": "test_mixpanel_token",
        "SENDGRID_API_KEY": "test_sendgrid_key"
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    return env_vars


# ============================================================================
# Mock Database Fixtures
# ============================================================================

@pytest.fixture
async def mock_database():
    """Create a mock database connection for testing."""
    # This will be expanded when implementing database integration
    class MockDatabase:
        def __init__(self):
            self.data = {}

        async def connect(self):
            pass

        async def disconnect(self):
            pass

        async def execute(self, query: str, *args):
            return {"status": "success"}

        async def fetch_one(self, query: str, *args):
            return None

        async def fetch_many(self, query: str, *args):
            return []

    db = MockDatabase()
    await db.connect()
    yield db
    await db.disconnect()


@pytest.fixture
async def mock_redis():
    """Create a mock Redis connection for testing."""
    # This will be expanded when implementing Redis integration
    class MockRedis:
        def __init__(self):
            self.cache = {}

        async def connect(self):
            pass

        async def get(self, key: str):
            return self.cache.get(key)

        async def set(self, key: str, value: str, ttl: int = 3600):
            self.cache[key] = value

        async def delete(self, key: str):
            if key in self.cache:
                del self.cache[key]

        async def clear_pattern(self, pattern: str):
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]

    redis = MockRedis()
    await redis.connect()
    yield redis


# ============================================================================
# Validation Test Data
# ============================================================================

@pytest.fixture
def invalid_client_ids() -> list[str]:
    """Provide a list of invalid client IDs for validation testing."""
    return [
        "",  # Empty string
        "invalid",  # Missing prefix
        "cs_",  # Missing timestamp and name
        "cs_abc_test",  # Non-numeric timestamp
        "CS_1234_test",  # Uppercase prefix
        "cs_1234_TEST",  # Uppercase name
        "cs_1234_test-name",  # Hyphen instead of underscore
        "cs_1234_test name",  # Space in name
        "../../../etc/passwd",  # Path traversal attempt
        "cs_1234_test'; DROP TABLE customers;--",  # SQL injection attempt
    ]


@pytest.fixture
def invalid_emails() -> list[str]:
    """Provide a list of invalid email addresses for validation testing."""
    return [
        "",  # Empty string
        "invalid",  # No @ sign
        "@example.com",  # Missing local part
        "user@",  # Missing domain
        "user @example.com",  # Space in local part
        "user@example",  # Missing TLD
        "user@.com",  # Missing domain name
        "<script>alert('xss')</script>@example.com",  # XSS attempt
    ]


# ============================================================================
# Performance Testing Fixtures
# ============================================================================

@pytest.fixture
def performance_timer():
    """Timer fixture for performance testing."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        def elapsed(self) -> float:
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0.0

    return Timer()
