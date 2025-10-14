"""
Customer Success Data Fixtures
Mock customer success data for testing - customers, health scores, onboarding, tickets, renewals, feedback, usage
"""

import pytest
from datetime import datetime, timedelta, date
from typing import Dict, List, Any
from faker import Faker

fake = Faker()


# Mock Customer Data
@pytest.fixture
def mock_customer_data() -> Dict[str, Any]:
    """Single mock customer for basic testing"""
    return {
        "client_id": "cs_1696800000_acme",
        "client_name": "Acme Corporation",
        "company_name": "Acme Corp Inc.",
        "industry": "SaaS",
        "tier": "professional",
        "lifecycle_stage": "active",
        "contract_value": 72000.0,
        "contract_start_date": "2025-01-15",
        "contract_end_date": "2026-01-15",
        "renewal_date": "2026-01-15",
        "primary_contact_email": "john.smith@acme.com",
        "primary_contact_name": "John Smith",
        "csm_assigned": "Sarah Johnson",
        "health_score": 82,
        "health_trend": "improving",
        "last_engagement_date": "2025-10-08T14:30:00Z",
        "status": "active",
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-10-10T09:15:00Z"
    }


@pytest.fixture
def mock_customers_collection() -> List[Dict[str, Any]]:
    """Collection of 10 mock customers with varied health scores, tiers, lifecycle stages"""
    tiers = ["starter", "standard", "professional", "enterprise"]
    lifecycle_stages = ["onboarding", "active", "at_risk", "expansion", "renewal"]
    health_trends = ["improving", "stable", "declining"]
    industries = ["SaaS", "E-commerce", "Healthcare", "Finance", "Manufacturing"]

    customers = []
    for i in range(10):
        customer = {
            "client_id": f"cs_{1696800000 + i}_{fake.user_name()}",
            "client_name": fake.company(),
            "company_name": fake.company(),
            "industry": industries[i % len(industries)],
            "tier": tiers[i % len(tiers)],
            "lifecycle_stage": lifecycle_stages[i % len(lifecycle_stages)],
            "contract_value": [12000, 24000, 72000, 144000, 240000][i % 5],
            "contract_start_date": (date.today() - timedelta(days=180 + i*30)).isoformat(),
            "contract_end_date": (date.today() + timedelta(days=180 - i*20)).isoformat(),
            "renewal_date": (date.today() + timedelta(days=180 - i*20)).isoformat(),
            "primary_contact_email": fake.email(),
            "primary_contact_name": fake.name(),
            "csm_assigned": fake.name(),
            "health_score": 45 + (i * 5),
            "health_trend": health_trends[i % len(health_trends)],
            "last_engagement_date": (datetime.now() - timedelta(days=i*3)).isoformat(),
            "status": "active",
            "created_at": (datetime.now() - timedelta(days=180 + i*30)).isoformat(),
            "updated_at": (datetime.now() - timedelta(days=i)).isoformat()
        }
        customers.append(customer)

    return customers


# Mock Health Score Data
@pytest.fixture
def mock_health_score_data() -> Dict[str, Any]:
    """Single mock health score with components"""
    return {
        "client_id": "cs_1696800000_acme",
        "health_score": 82,
        "components": {
            "usage_score": 85.0,
            "engagement_score": 78.0,
            "support_score": 92.0,
            "satisfaction_score": 88.0,
            "payment_score": 100.0
        },
        "weights": {
            "usage_weight": 0.35,
            "engagement_weight": 0.25,
            "support_weight": 0.15,
            "satisfaction_weight": 0.15,
            "payment_weight": 0.10
        },
        "trend": "improving",
        "calculated_at": datetime.now().isoformat()
    }


@pytest.fixture
def mock_health_scores_collection() -> List[Dict[str, Any]]:
    """Collection of 15 mock health scores with different components"""
    health_scores = []
    for i in range(15):
        score = {
            "client_id": f"cs_{1696800000 + i}_{fake.user_name()}",
            "health_score": 40 + (i * 4),
            "components": {
                "usage_score": 40.0 + (i * 4),
                "engagement_score": 35.0 + (i * 4.5),
                "support_score": 50.0 + (i * 3),
                "satisfaction_score": 45.0 + (i * 3.5),
                "payment_score": 90.0 + (i % 3) * 5
            },
            "weights": {
                "usage_weight": 0.35,
                "engagement_weight": 0.25,
                "support_weight": 0.15,
                "satisfaction_weight": 0.15,
                "payment_weight": 0.10
            },
            "trend": ["improving", "stable", "declining"][i % 3],
            "calculated_at": (datetime.now() - timedelta(hours=i*2)).isoformat()
        }
        health_scores.append(score)

    return health_scores


# Mock Onboarding Plan Data
@pytest.fixture
def mock_onboarding_plan_data() -> Dict[str, Any]:
    """Single mock onboarding plan"""
    return {
        "plan_id": "onb_plan_001",
        "client_id": "cs_1696800000_acme",
        "plan_name": "Enterprise Onboarding - Acme Corp",
        "status": "in_progress",
        "start_date": date.today().isoformat(),
        "target_completion_date": (date.today() + timedelta(days=90)).isoformat(),
        "completion_percentage": 45,
        "milestones": [
            {
                "id": "m1",
                "name": "Kickoff Call",
                "status": "completed",
                "due_date": (date.today() - timedelta(days=7)).isoformat(),
                "completed_date": (date.today() - timedelta(days=7)).isoformat()
            },
            {
                "id": "m2",
                "name": "System Configuration",
                "status": "in_progress",
                "due_date": (date.today() + timedelta(days=7)).isoformat(),
                "completed_date": None
            },
            {
                "id": "m3",
                "name": "User Training",
                "status": "not_started",
                "due_date": (date.today() + timedelta(days=30)).isoformat(),
                "completed_date": None
            }
        ],
        "csm_assigned": "Sarah Johnson",
        "created_at": (datetime.now() - timedelta(days=14)).isoformat()
    }


@pytest.fixture
def mock_onboarding_plans_collection() -> List[Dict[str, Any]]:
    """Collection of 8 mock onboarding plans"""
    statuses = ["not_started", "in_progress", "completed", "at_risk"]
    plans = []
    for i in range(8):
        plan = {
            "plan_id": f"onb_plan_{i+1:03d}",
            "client_id": f"cs_{1696800000 + i}_{fake.user_name()}",
            "plan_name": f"{fake.company()} Onboarding",
            "status": statuses[i % len(statuses)],
            "start_date": (date.today() - timedelta(days=i*14)).isoformat(),
            "target_completion_date": (date.today() + timedelta(days=90 - i*10)).isoformat(),
            "completion_percentage": min(100, i * 12),
            "milestones": [
                {
                    "id": f"m{j+1}",
                    "name": ["Kickoff", "Setup", "Training", "Go-Live"][j % 4],
                    "status": "completed" if j <= i else "not_started",
                    "due_date": (date.today() + timedelta(days=j*20 - i*10)).isoformat(),
                    "completed_date": (date.today() - timedelta(days=i-j)).isoformat() if j <= i else None
                }
                for j in range(4)
            ],
            "csm_assigned": fake.name(),
            "created_at": (datetime.now() - timedelta(days=i*14 + 7)).isoformat()
        }
        plans.append(plan)

    return plans


# Mock Support Ticket Data
@pytest.fixture
def mock_support_ticket_data() -> Dict[str, Any]:
    """Single mock support ticket"""
    return {
        "ticket_id": "TICKET-12345",
        "client_id": "cs_1696800000_acme",
        "subject": "Login issue with SSO",
        "description": "Users cannot login using SSO authentication",
        "status": "open",
        "priority": "high",
        "category": "technical",
        "created_at": (datetime.now() - timedelta(hours=3)).isoformat(),
        "updated_at": datetime.now().isoformat(),
        "assigned_to": "Support Team A",
        "sla_due_date": (datetime.now() + timedelta(hours=5)).isoformat(),
        "requester_email": "john.smith@acme.com",
        "requester_name": "John Smith",
        "tags": ["sso", "authentication", "urgent"]
    }


@pytest.fixture
def mock_support_tickets_collection() -> List[Dict[str, Any]]:
    """Collection of 20 mock support tickets"""
    statuses = ["open", "pending", "in_progress", "resolved", "closed"]
    priorities = ["low", "medium", "high", "critical"]
    categories = ["technical", "billing", "feature_request", "how_to", "bug"]

    tickets = []
    for i in range(20):
        ticket = {
            "ticket_id": f"TICKET-{10000 + i}",
            "client_id": f"cs_{1696800000 + (i % 10)}_{fake.user_name()}",
            "subject": fake.sentence(nb_words=6),
            "description": fake.text(max_nb_chars=200),
            "status": statuses[i % len(statuses)],
            "priority": priorities[i % len(priorities)],
            "category": categories[i % len(categories)],
            "created_at": (datetime.now() - timedelta(days=i*2, hours=i)).isoformat(),
            "updated_at": (datetime.now() - timedelta(days=i)).isoformat(),
            "assigned_to": f"Support Team {chr(65 + (i % 3))}",
            "sla_due_date": (datetime.now() + timedelta(hours=24 - i*2)).isoformat(),
            "requester_email": fake.email(),
            "requester_name": fake.name(),
            "tags": [fake.word() for _ in range(2)]
        }
        tickets.append(ticket)

    return tickets


# Mock Renewal Forecast Data
@pytest.fixture
def mock_renewal_forecast_data() -> Dict[str, Any]:
    """Single mock renewal forecast"""
    return {
        "forecast_id": "renewal_forecast_001",
        "client_id": "cs_1696800000_acme",
        "renewal_date": (date.today() + timedelta(days=90)).isoformat(),
        "current_arr": 72000.0,
        "forecasted_arr": 90000.0,
        "renewal_probability": 0.85,
        "renewal_risk_level": "low",
        "expansion_opportunity": 18000.0,
        "contraction_risk": 0.0,
        "key_factors": [
            {"factor": "high_health_score", "impact": "positive"},
            {"factor": "strong_engagement", "impact": "positive"},
            {"factor": "expansion_signals", "impact": "positive"}
        ],
        "recommended_actions": [
            "Schedule renewal discussion 60 days prior",
            "Present expansion options during QBR",
            "Prepare ROI analysis"
        ],
        "last_updated": datetime.now().isoformat()
    }


@pytest.fixture
def mock_renewal_forecasts_collection() -> List[Dict[str, Any]]:
    """Collection of 10 mock renewal forecasts"""
    risk_levels = ["low", "medium", "high", "critical"]
    forecasts = []
    for i in range(10):
        forecast = {
            "forecast_id": f"renewal_forecast_{i+1:03d}",
            "client_id": f"cs_{1696800000 + i}_{fake.user_name()}",
            "renewal_date": (date.today() + timedelta(days=30 + i*20)).isoformat(),
            "current_arr": [12000, 24000, 72000, 144000][i % 4],
            "forecasted_arr": [12000, 24000, 72000, 144000][i % 4] * (1 + (i % 3) * 0.2),
            "renewal_probability": 0.95 - (i * 0.05),
            "renewal_risk_level": risk_levels[i % len(risk_levels)],
            "expansion_opportunity": [0, 5000, 10000, 20000][i % 4],
            "contraction_risk": [0, 2000, 5000, 10000][i % 4] if i > 5 else 0,
            "key_factors": [
                {"factor": fake.word(), "impact": ["positive", "negative"][i % 2]}
                for _ in range(3)
            ],
            "recommended_actions": [fake.sentence() for _ in range(3)],
            "last_updated": (datetime.now() - timedelta(hours=i*2)).isoformat()
        }
        forecasts.append(forecast)

    return forecasts


# Mock Feedback Data
@pytest.fixture
def mock_feedback_data() -> Dict[str, Any]:
    """Single mock feedback response"""
    return {
        "feedback_id": "feedback_001",
        "client_id": "cs_1696800000_acme",
        "feedback_type": "nps",
        "score": 9,
        "category": "promoter",
        "comment": "Great product, excellent support team!",
        "respondent_email": "john.smith@acme.com",
        "respondent_name": "John Smith",
        "submitted_at": (datetime.now() - timedelta(days=2)).isoformat(),
        "channel": "email",
        "campaign_id": "nps_q3_2025"
    }


@pytest.fixture
def mock_feedback_responses_collection() -> List[Dict[str, Any]]:
    """Collection of 15 NPS and CSAT feedback responses"""
    feedback_types = ["nps", "csat"]
    categories_nps = ["promoter", "passive", "detractor"]
    categories_csat = ["very_satisfied", "satisfied", "neutral", "dissatisfied", "very_dissatisfied"]
    channels = ["email", "in_app", "survey", "phone"]

    responses = []
    for i in range(15):
        feedback_type = feedback_types[i % len(feedback_types)]

        if feedback_type == "nps":
            score = [9, 10, 8, 7, 6, 5, 4, 3][i % 8]
            category = "promoter" if score >= 9 else "passive" if score >= 7 else "detractor"
        else:
            score = [5, 4, 3, 2, 1][i % 5]
            category = categories_csat[5 - score]

        response = {
            "feedback_id": f"feedback_{i+1:03d}",
            "client_id": f"cs_{1696800000 + (i % 10)}_{fake.user_name()}",
            "feedback_type": feedback_type,
            "score": score,
            "category": category,
            "comment": fake.text(max_nb_chars=150) if i % 2 == 0 else None,
            "respondent_email": fake.email(),
            "respondent_name": fake.name(),
            "submitted_at": (datetime.now() - timedelta(days=i*3)).isoformat(),
            "channel": channels[i % len(channels)],
            "campaign_id": f"survey_{['q1', 'q2', 'q3', 'q4'][i % 4]}_2025"
        }
        responses.append(response)

    return responses


# Mock Usage Analytics Data
@pytest.fixture
def mock_usage_analytics_data() -> Dict[str, Any]:
    """Single mock usage analytics data point"""
    return {
        "client_id": "cs_1696800000_acme",
        "period": "2025-10",
        "daily_active_users": 45,
        "weekly_active_users": 78,
        "monthly_active_users": 95,
        "total_users": 120,
        "feature_adoption_rate": 0.72,
        "core_features_used": 12,
        "total_features": 18,
        "avg_session_duration_minutes": 32,
        "logins_per_user": 4.2,
        "key_events_tracked": 1250,
        "recorded_at": datetime.now().isoformat()
    }


@pytest.fixture
def mock_usage_analytics_collection() -> List[Dict[str, Any]]:
    """Collection of 30 mock usage analytics data points"""
    analytics = []
    for i in range(30):
        data = {
            "client_id": f"cs_{1696800000 + (i % 10)}_{fake.user_name()}",
            "period": f"2025-{(i % 12) + 1:02d}",
            "daily_active_users": 10 + i * 2,
            "weekly_active_users": 20 + i * 3,
            "monthly_active_users": 30 + i * 4,
            "total_users": 50 + i * 5,
            "feature_adoption_rate": 0.3 + (i * 0.02),
            "core_features_used": 3 + (i % 15),
            "total_features": 18,
            "avg_session_duration_minutes": 15 + i,
            "logins_per_user": 1 + (i * 0.2),
            "key_events_tracked": 100 + i * 50,
            "recorded_at": (datetime.now() - timedelta(days=i*7)).isoformat()
        }
        analytics.append(data)

    return analytics


# Mock MCP Context
@pytest.fixture
def mock_context():
    """Mock MCP Context for testing"""
    class MockContext:
        async def info(self, message: str):
            """Mock info logger"""
            pass

        async def warn(self, message: str):
            """Mock warn logger"""
            pass

        async def error(self, message: str):
            """Mock error logger"""
            pass

    return MockContext()


# Invalid data for validation testing
@pytest.fixture
def invalid_customer_data() -> Dict[str, Any]:
    """Invalid customer data for validation testing"""
    return {
        "client_id": "invalid_id",  # Invalid format
        "client_name": "",  # Empty name
        "company_name": "Test",
        "contract_value": -1000,  # Negative value
        "contract_start_date": "2025-01-15",
        "contract_end_date": "2024-01-15",  # End before start
        "primary_contact_email": "not-an-email"  # Invalid email
    }


@pytest.fixture
def invalid_health_score_data() -> Dict[str, Any]:
    """Invalid health score data for validation testing"""
    return {
        "client_id": "",  # Empty
        "health_score": 150,  # Out of range
        "components": {
            "usage_score": -10,  # Negative
            "engagement_score": 200,  # Out of range
            "support_score": 50,
            "satisfaction_score": 50,
            "payment_score": 100
        }
    }


# Segmentation data
@pytest.fixture
def mock_segment_data() -> Dict[str, Any]:
    """Mock customer segment data"""
    return {
        "segment_id": "seg_high_value_saas",
        "segment_name": "High-Value SaaS Accounts",
        "segment_type": "value_based",
        "criteria": {
            "min_arr": 50000,
            "industry": ["SaaS", "Technology"],
            "tier": ["professional", "enterprise"]
        },
        "characteristics": {
            "typical_team_size": "50-200",
            "typical_arr": "50k-200k",
            "growth_stage": "scale-up"
        },
        "engagement_strategy": {
            "csm_touch_frequency": "weekly",
            "ebr_frequency": "quarterly",
            "success_programs": ["technical_advisory", "strategic_planning"]
        },
        "customer_count": 47,
        "total_arr": 4235000.0,
        "avg_health_score": 82.3
    }


# Churn risk data
@pytest.fixture
def mock_churn_risk_data() -> Dict[str, Any]:
    """Mock churn risk prediction data"""
    return {
        "client_id": "cs_1696800000_acme",
        "prediction_date": datetime.now().isoformat(),
        "churn_probability": 0.23,
        "churn_risk_level": "low",
        "confidence_score": 0.87,
        "contributing_factors": [
            {"factor": "decreased_login_frequency", "weight": 0.35},
            {"factor": "support_ticket_volume_increase", "weight": 0.25},
            {"factor": "feature_adoption_decline", "weight": 0.20}
        ],
        "predicted_churn_date": (date.today() + timedelta(days=120)).isoformat(),
        "retention_recommendations": [
            "Increase CSM touchpoints to weekly",
            "Provide advanced feature training",
            "Address support ticket backlog"
        ]
    }
