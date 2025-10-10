"""
Test Data Fixtures and Mock Data Generators

This module provides utility functions for generating realistic test data
for Customer Success MCP tests.
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
from faker import Faker
import random

from src.models.customer_models import (
    CustomerAccount, HealthScoreComponents, CustomerSegment,
    RiskIndicator, ChurnPrediction, CustomerTier, LifecycleStage,
    HealthTrend, AccountStatus
)

# Initialize Faker
fake = Faker()


# ============================================================================
# Customer Account Generators
# ============================================================================

def generate_client_id(company_name: Optional[str] = None) -> str:
    """
    Generate a valid client ID for testing.

    Args:
        company_name: Optional company name to use in the slug

    Returns:
        str: Valid client ID in format cs_{timestamp}_{slug}
    """
    timestamp = int(datetime.now().timestamp()) + random.randint(0, 10000)
    if company_name:
        slug = company_name.lower().replace(" ", "_").replace(",", "")[:20]
    else:
        slug = fake.company().lower().replace(" ", "_").replace(",", "")[:20]
    return f"cs_{timestamp}_{slug}"


def generate_customer_account(
    client_id: Optional[str] = None,
    tier: Optional[CustomerTier] = None,
    lifecycle_stage: Optional[LifecycleStage] = None,
    health_score: Optional[int] = None,
    status: Optional[AccountStatus] = None
) -> CustomerAccount:
    """
    Generate a realistic CustomerAccount for testing.

    Args:
        client_id: Optional custom client ID
        tier: Optional tier override
        lifecycle_stage: Optional lifecycle stage override
        health_score: Optional health score override
        status: Optional status override

    Returns:
        CustomerAccount: Generated customer account
    """
    if not client_id:
        client_id = generate_client_id()

    company = fake.company()
    contract_start = date.today() - timedelta(days=random.randint(30, 730))
    contract_duration = random.randint(180, 730)

    return CustomerAccount(
        client_id=client_id,
        client_name=company,
        company_name=company + " Inc.",
        industry=fake.random_element(["SaaS", "Technology", "Healthcare", "Finance", "E-commerce", "Manufacturing"]),
        tier=tier or fake.random_element(list(CustomerTier)),
        lifecycle_stage=lifecycle_stage or fake.random_element(list(LifecycleStage)),
        contract_value=float(random.randint(5000, 500000)),
        contract_start_date=contract_start,
        contract_end_date=contract_start + timedelta(days=contract_duration),
        renewal_date=contract_start + timedelta(days=contract_duration),
        primary_contact_email=fake.email(),
        primary_contact_name=fake.name(),
        csm_assigned=fake.name(),
        health_score=health_score or random.randint(20, 100),
        health_trend=fake.random_element(list(HealthTrend)),
        last_engagement_date=datetime.now() - timedelta(days=random.randint(0, 30)),
        status=status or AccountStatus.ACTIVE
    )


def generate_customer_accounts(count: int = 10) -> List[CustomerAccount]:
    """
    Generate multiple customer accounts for testing.

    Args:
        count: Number of accounts to generate

    Returns:
        List[CustomerAccount]: List of generated accounts
    """
    return [generate_customer_account() for _ in range(count)]


# ============================================================================
# Health Score Generators
# ============================================================================

def generate_health_score_components(
    target_score: Optional[float] = None,
    custom_weights: Optional[Dict[str, float]] = None
) -> HealthScoreComponents:
    """
    Generate HealthScoreComponents for testing.

    Args:
        target_score: Optional target weighted score (will generate components to match)
        custom_weights: Optional custom weight distribution

    Returns:
        HealthScoreComponents: Generated health score components
    """
    if custom_weights:
        weights = custom_weights
    else:
        weights = {
            "usage_weight": 0.35,
            "engagement_weight": 0.25,
            "support_weight": 0.15,
            "satisfaction_weight": 0.15,
            "payment_weight": 0.10
        }

    if target_score:
        # Generate scores that will result in the target weighted score
        # This is a simplified approach - real implementation might be more sophisticated
        usage_score = target_score + random.uniform(-10, 10)
        engagement_score = target_score + random.uniform(-10, 10)
        support_score = target_score + random.uniform(-10, 10)
        satisfaction_score = target_score + random.uniform(-10, 10)
        payment_score = target_score + random.uniform(-10, 10)
    else:
        usage_score = float(random.randint(0, 100))
        engagement_score = float(random.randint(0, 100))
        support_score = float(random.randint(0, 100))
        satisfaction_score = float(random.randint(0, 100))
        payment_score = float(random.randint(0, 100))

    return HealthScoreComponents(
        usage_score=min(100, max(0, usage_score)),
        engagement_score=min(100, max(0, engagement_score)),
        support_score=min(100, max(0, support_score)),
        satisfaction_score=min(100, max(0, satisfaction_score)),
        payment_score=min(100, max(0, payment_score)),
        **weights
    )


# ============================================================================
# Segment Generators
# ============================================================================

def generate_customer_segment(
    segment_type: str = "value_based",
    customer_count: int = 50
) -> CustomerSegment:
    """
    Generate a CustomerSegment for testing.

    Args:
        segment_type: Type of segmentation
        customer_count: Number of customers in segment

    Returns:
        CustomerSegment: Generated customer segment
    """
    segment_name = fake.catch_phrase()
    segment_id = f"seg_{segment_name.lower().replace(' ', '_')[:30]}"

    if segment_type == "value_based":
        criteria = {
            "min_arr": random.choice([10000, 50000, 100000, 250000]),
            "tier": random.sample(["starter", "standard", "professional", "enterprise"], k=random.randint(1, 3))
        }
    elif segment_type == "industry":
        criteria = {
            "industry": random.sample(["SaaS", "Technology", "Healthcare", "Finance"], k=random.randint(1, 3))
        }
    elif segment_type == "lifecycle":
        criteria = {
            "lifecycle_stage": random.sample(["onboarding", "active", "at_risk", "expansion"], k=random.randint(1, 2))
        }
    else:
        criteria = {"type": segment_type}

    return CustomerSegment(
        segment_id=segment_id,
        segment_name=segment_name,
        segment_type=segment_type,
        criteria=criteria,
        characteristics={
            "typical_team_size": f"{random.randint(10, 200)}-{random.randint(201, 500)}",
            "typical_arr": f"{random.randint(10, 100)}k-{random.randint(101, 500)}k",
            "growth_stage": random.choice(["startup", "scale-up", "mature"])
        },
        engagement_strategy={
            "csm_touch_frequency": random.choice(["weekly", "bi-weekly", "monthly"]),
            "ebr_frequency": random.choice(["quarterly", "bi-annual", "annual"]),
            "success_programs": random.sample(["technical_advisory", "strategic_planning", "training", "best_practices"], k=random.randint(1, 3))
        },
        success_metrics={
            "target_health_score": float(random.randint(75, 95)),
            "target_nps": float(random.randint(40, 70)),
            "target_retention_rate": round(random.uniform(0.85, 0.98), 2)
        },
        customer_count=customer_count,
        total_arr=float(customer_count * random.randint(50000, 150000)),
        avg_health_score=float(random.randint(60, 90))
    )


# ============================================================================
# Risk and Churn Generators
# ============================================================================

def generate_risk_indicator(
    severity: str = "medium",
    category: str = "engagement"
) -> RiskIndicator:
    """
    Generate a RiskIndicator for testing.

    Args:
        severity: Risk severity level
        category: Risk category

    Returns:
        RiskIndicator: Generated risk indicator
    """
    risk_names = {
        "engagement": "Low Product Engagement",
        "usage": "Declining Usage",
        "support": "High Support Ticket Volume",
        "payment": "Payment Issues",
        "satisfaction": "Low Satisfaction Score"
    }

    return RiskIndicator(
        indicator_id=f"risk_{category}_{random.randint(1000, 9999)}",
        indicator_name=risk_names.get(category, "Risk Indicator"),
        category=category,
        severity=severity,
        current_value=float(random.uniform(0, 10)),
        threshold_value=float(random.uniform(10, 20)),
        description=f"{risk_names.get(category, 'Risk')} detected based on recent activity",
        detected_at=datetime.now(),
        mitigation_actions=[
            "Schedule check-in call",
            "Provide additional resources",
            f"Review {category} metrics"
        ]
    )


def generate_churn_prediction(
    client_id: str,
    churn_risk_level: str = "medium"
) -> ChurnPrediction:
    """
    Generate a ChurnPrediction for testing.

    Args:
        client_id: Customer identifier
        churn_risk_level: Risk level classification

    Returns:
        ChurnPrediction: Generated churn prediction
    """
    risk_probabilities = {
        "low": (0.0, 0.25),
        "medium": (0.25, 0.50),
        "high": (0.50, 0.75),
        "critical": (0.75, 1.0)
    }

    prob_range = risk_probabilities.get(churn_risk_level, (0.25, 0.50))
    churn_probability = round(random.uniform(*prob_range), 2)

    contributing_factors = [
        {"factor": "decreased_login_frequency", "weight": round(random.uniform(0.2, 0.4), 2)},
        {"factor": "support_ticket_volume_increase", "weight": round(random.uniform(0.15, 0.3), 2)},
        {"factor": "feature_adoption_decline", "weight": round(random.uniform(0.1, 0.25), 2)},
        {"factor": "engagement_score_decline", "weight": round(random.uniform(0.1, 0.2), 2)}
    ]

    return ChurnPrediction(
        client_id=client_id,
        prediction_date=datetime.now(),
        churn_probability=churn_probability,
        churn_risk_level=churn_risk_level,
        confidence_score=round(random.uniform(0.7, 0.95), 2),
        contributing_factors=contributing_factors,
        risk_indicators=[generate_risk_indicator() for _ in range(random.randint(1, 3))],
        predicted_churn_date=date.today() + timedelta(days=random.randint(30, 180)),
        retention_recommendations=[
            "Increase CSM touchpoints to weekly",
            "Provide advanced feature training",
            "Address support ticket backlog",
            "Schedule executive business review"
        ],
        model_version=f"v{random.randint(1, 3)}.{random.randint(0, 5)}.{random.randint(0, 10)}"
    )


# ============================================================================
# Validation Test Data Generators
# ============================================================================

def generate_invalid_client_ids() -> List[str]:
    """Generate a list of invalid client IDs for validation testing."""
    return [
        "",  # Empty
        "invalid",  # Wrong format
        "cs_",  # Incomplete
        "cs_abc_test",  # Non-numeric timestamp
        "CS_1234_test",  # Uppercase
        "cs_1234_TEST",  # Uppercase name
        "cs_1234_test-name",  # Hyphen
        "cs_1234_test name",  # Space
        "cs_1234_test@hack",  # Special char
        "../../../etc/passwd",  # Path traversal
        "cs_1234_test'; DROP TABLE customers;--",  # SQL injection
        "<script>alert('xss')</script>",  # XSS
        "x" * 256,  # Too long
    ]


def generate_invalid_emails() -> List[str]:
    """Generate a list of invalid email addresses for validation testing."""
    return [
        "",
        "invalid",
        "@example.com",
        "user@",
        "user @example.com",
        "user@example",
        "user@.com",
        "user@@example.com",
        "<script>@example.com",
        "user@example..com",
        "user name@example.com",
    ]


def generate_sql_injection_attempts() -> List[str]:
    """Generate SQL injection test strings."""
    return [
        "'; DROP TABLE customers;--",
        "1' OR '1'='1",
        "admin'--",
        "' OR 1=1--",
        "'; DELETE FROM customers WHERE '1'='1",
        "1' UNION SELECT * FROM users--",
    ]


def generate_xss_attempts() -> List[str]:
    """Generate XSS test strings."""
    return [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "javascript:alert('XSS')",
        "<svg onload=alert('XSS')>",
        "<iframe src='javascript:alert(\"XSS\")'></iframe>",
        "<<SCRIPT>alert('XSS');//<</SCRIPT>",
    ]


# ============================================================================
# Bulk Data Generators
# ============================================================================

def generate_test_dataset(
    num_customers: int = 100,
    include_churn_predictions: bool = True,
    include_segments: bool = True
) -> Dict[str, Any]:
    """
    Generate a complete test dataset with customers, predictions, and segments.

    Args:
        num_customers: Number of customers to generate
        include_churn_predictions: Whether to include churn predictions
        include_segments: Whether to include customer segments

    Returns:
        Dict containing customers, predictions, and segments
    """
    customers = generate_customer_accounts(num_customers)

    dataset = {
        "customers": customers,
        "customer_count": len(customers)
    }

    if include_churn_predictions:
        predictions = [
            generate_churn_prediction(
                customer.client_id,
                random.choice(["low", "medium", "high", "critical"])
            )
            for customer in random.sample(customers, min(20, num_customers))
        ]
        dataset["churn_predictions"] = predictions

    if include_segments:
        segments = [
            generate_customer_segment("value_based", random.randint(20, 50)),
            generate_customer_segment("industry", random.randint(15, 40)),
            generate_customer_segment("lifecycle", random.randint(10, 30))
        ]
        dataset["segments"] = segments

    return dataset


__all__ = [
    'generate_client_id',
    'generate_customer_account',
    'generate_customer_accounts',
    'generate_health_score_components',
    'generate_customer_segment',
    'generate_risk_indicator',
    'generate_churn_prediction',
    'generate_invalid_client_ids',
    'generate_invalid_emails',
    'generate_sql_injection_attempts',
    'generate_xss_attempts',
    'generate_test_dataset'
]
