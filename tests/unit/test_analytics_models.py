"""
Unit Tests for Analytics Models

Tests for all analytics-related Pydantic models including health metrics,
engagement metrics, usage analytics, account metrics, and cohort analysis.
"""

import pytest
from datetime import datetime, date, timedelta
from pydantic import ValidationError

from src.models.analytics_models import (
    TimeGranularity, TrendDirection, BenchmarkComparison,
    HealthMetrics, EngagementMetrics, UsageAnalytics,
    AccountMetrics, CohortAnalysis
)
from src.models.customer_models import CustomerTier, LifecycleStage


# ============================================================================
# TimeGranularity Enum Tests
# ============================================================================

@pytest.mark.unit
def test_time_granularity_enum_values():
    """Test that TimeGranularity enum has all expected values."""
    assert TimeGranularity.HOURLY == "hourly"
    assert TimeGranularity.DAILY == "daily"
    assert TimeGranularity.WEEKLY == "weekly"
    assert TimeGranularity.MONTHLY == "monthly"
    assert TimeGranularity.QUARTERLY == "quarterly"
    assert TimeGranularity.YEARLY == "yearly"


@pytest.mark.unit
def test_time_granularity_enum_count():
    """Test that TimeGranularity has exactly 6 granularities."""
    assert len(list(TimeGranularity)) == 6


# ============================================================================
# TrendDirection Enum Tests
# ============================================================================

@pytest.mark.unit
def test_trend_direction_enum_values():
    """Test that TrendDirection enum has all expected values."""
    assert TrendDirection.UP == "up"
    assert TrendDirection.DOWN == "down"
    assert TrendDirection.FLAT == "flat"


# ============================================================================
# BenchmarkComparison Enum Tests
# ============================================================================

@pytest.mark.unit
def test_benchmark_comparison_enum_values():
    """Test that BenchmarkComparison enum has all expected values."""
    assert BenchmarkComparison.ABOVE == "above"
    assert BenchmarkComparison.BELOW == "below"
    assert BenchmarkComparison.AT == "at"


# ============================================================================
# HealthMetrics Model Tests
# ============================================================================

@pytest.mark.unit
def test_health_metrics_valid_creation(sample_client_id):
    """Test creating valid HealthMetrics with all required fields."""
    metrics = HealthMetrics(
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        overall_health_score=82,
        health_score_trend=TrendDirection.UP,
        health_score_change=5,
        health_components={
            "usage_score": 85,
            "engagement_score": 78,
            "support_score": 92
        },
        component_trends={
            "usage_score": "up",
            "engagement_score": "up",
            "support_score": "flat"
        }
    )

    assert metrics.client_id == sample_client_id
    assert metrics.overall_health_score == 82
    assert metrics.health_score_trend == TrendDirection.UP


@pytest.mark.unit
def test_health_metrics_health_score_boundaries():
    """Test that overall_health_score respects 0-100 boundaries."""
    # Test minimum
    metrics = HealthMetrics(
        client_id="cs_1234_test",
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        overall_health_score=0,
        health_score_trend=TrendDirection.DOWN,
        health_score_change=-10,
        health_components={},
        component_trends={}
    )
    assert metrics.overall_health_score == 0

    # Test maximum
    metrics.overall_health_score = 100
    assert metrics.overall_health_score == 100

    # Test above maximum
    with pytest.raises(ValidationError) as exc_info:
        HealthMetrics(
            client_id="cs_1234_test",
            period_start=datetime(2025, 10, 1),
            period_end=datetime(2025, 10, 31),
            overall_health_score=101,
            health_score_trend=TrendDirection.UP,
            health_score_change=10,
            health_components={},
            component_trends={}
        )

    assert "overall_health_score" in str(exc_info.value)


@pytest.mark.unit
def test_health_metrics_health_score_change_boundaries():
    """Test that health_score_change respects -100 to 100 boundaries."""
    metrics = HealthMetrics(
        client_id="cs_1234_test",
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        overall_health_score=50,
        health_score_trend=TrendDirection.DOWN,
        health_score_change=-100,
        health_components={},
        component_trends={}
    )
    assert metrics.health_score_change == -100


@pytest.mark.unit
def test_health_metrics_with_indicators(sample_client_id):
    """Test HealthMetrics with risk and positive indicators."""
    risk_indicators = [
        {"indicator": "decreased_usage", "severity": "medium", "detected_date": "2025-10-15"}
    ]
    positive_indicators = [
        {"indicator": "high_engagement", "strength": "strong", "detected_date": "2025-10-05"}
    ]

    metrics = HealthMetrics(
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        overall_health_score=75,
        health_score_trend=TrendDirection.UP,
        health_score_change=3,
        health_components={"usage": 80},
        component_trends={"usage": "up"},
        risk_indicators=risk_indicators,
        positive_indicators=positive_indicators
    )

    assert len(metrics.risk_indicators) == 1
    assert len(metrics.positive_indicators) == 1


@pytest.mark.unit
def test_health_metrics_with_benchmark_and_prediction(sample_client_id):
    """Test HealthMetrics with benchmark comparison and predictions."""
    benchmark = {
        "overall_health": "above",
        "vs_tier_average": 12,
        "percentile": 78
    }

    metrics = HealthMetrics(
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        overall_health_score=85,
        health_score_trend=TrendDirection.UP,
        health_score_change=5,
        health_components={"usage": 90},
        component_trends={"usage": "up"},
        benchmark_comparison=benchmark,
        predicted_next_period_score=87,
        confidence=0.82
    )

    assert metrics.benchmark_comparison["percentile"] == 78
    assert metrics.predicted_next_period_score == 87
    assert metrics.confidence == 0.82


@pytest.mark.unit
def test_health_metrics_default_values(sample_client_id):
    """Test that HealthMetrics has correct default values."""
    metrics = HealthMetrics(
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        overall_health_score=80,
        health_score_trend=TrendDirection.FLAT,
        health_score_change=0,
        health_components={},
        component_trends={}
    )

    assert metrics.risk_indicators == []
    assert metrics.positive_indicators == []
    assert metrics.benchmark_comparison == {}
    assert metrics.confidence == 0.0


# ============================================================================
# EngagementMetrics Model Tests
# ============================================================================

@pytest.mark.unit
def test_engagement_metrics_valid_creation(sample_client_id):
    """Test creating valid EngagementMetrics."""
    metrics = EngagementMetrics(
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_users=50,
        active_users=42,
        daily_active_users=28,
        weekly_active_users=45,
        monthly_active_users=48,
        activation_rate=0.96,
        engagement_rate=0.84,
        total_logins=847,
        avg_logins_per_user=20.2,
        total_session_minutes=12450,
        avg_session_duration_minutes=14.7,
        total_actions=3821,
        avg_actions_per_session=4.5,
        feature_adoption={"core_features": 0.92},
        engagement_trend=TrendDirection.UP
    )

    assert metrics.total_users == 50
    assert metrics.active_users == 42
    assert metrics.engagement_rate == 0.84


@pytest.mark.unit
def test_engagement_metrics_rate_boundaries():
    """Test that engagement rates respect 0-1 boundaries."""
    metrics = EngagementMetrics(
        client_id="cs_1234_test",
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_users=100,
        active_users=100,
        daily_active_users=80,
        weekly_active_users=95,
        monthly_active_users=100,
        activation_rate=1.0,
        engagement_rate=1.0,
        total_logins=1000,
        avg_logins_per_user=10.0,
        total_session_minutes=10000,
        avg_session_duration_minutes=10.0,
        total_actions=5000,
        avg_actions_per_session=5.0,
        feature_adoption={},
        engagement_trend=TrendDirection.UP
    )

    assert metrics.activation_rate == 1.0
    assert metrics.engagement_rate == 1.0


@pytest.mark.unit
def test_engagement_metrics_user_segmentation():
    """Test EngagementMetrics with user segmentation."""
    metrics = EngagementMetrics(
        client_id="cs_1234_test",
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_users=50,
        active_users=42,
        daily_active_users=30,
        weekly_active_users=45,
        monthly_active_users=48,
        activation_rate=0.96,
        engagement_rate=0.84,
        total_logins=500,
        avg_logins_per_user=12.0,
        total_session_minutes=5000,
        avg_session_duration_minutes=10.0,
        total_actions=2000,
        avg_actions_per_session=4.0,
        feature_adoption={},
        engagement_trend=TrendDirection.UP,
        power_users=12,
        inactive_users=8,
        at_risk_users=3
    )

    assert metrics.power_users == 12
    assert metrics.inactive_users == 8
    assert metrics.at_risk_users == 3


@pytest.mark.unit
def test_engagement_metrics_with_trends():
    """Test EngagementMetrics with vs_previous_period data."""
    vs_previous = {
        "active_users_change": 3,
        "logins_change_pct": 0.08,
        "session_duration_change_pct": 0.12
    }

    metrics = EngagementMetrics(
        client_id="cs_1234_test",
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_users=50,
        active_users=42,
        daily_active_users=30,
        weekly_active_users=45,
        monthly_active_users=48,
        activation_rate=0.96,
        engagement_rate=0.84,
        total_logins=500,
        avg_logins_per_user=12.0,
        total_session_minutes=5000,
        avg_session_duration_minutes=10.0,
        total_actions=2000,
        avg_actions_per_session=4.0,
        feature_adoption={},
        engagement_trend=TrendDirection.UP,
        vs_previous_period=vs_previous
    )

    assert metrics.vs_previous_period["active_users_change"] == 3


# ============================================================================
# UsageAnalytics Model Tests
# ============================================================================

@pytest.mark.unit
def test_usage_analytics_valid_creation(sample_client_id):
    """Test creating valid UsageAnalytics."""
    top_features = [
        {"feature": "dashboard", "usage_count": 2847, "user_count": 45, "adoption_rate": 0.90}
    ]

    analytics = UsageAnalytics(
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_usage_events=15847,
        unique_features_used=42,
        total_features_available=68,
        feature_utilization_rate=0.62,
        top_features=top_features,
        usage_trend=TrendDirection.UP,
        usage_growth_rate=0.15
    )

    assert analytics.total_usage_events == 15847
    assert analytics.unique_features_used == 42
    assert analytics.feature_utilization_rate == 0.62


@pytest.mark.unit
def test_usage_analytics_utilization_rate_boundaries():
    """Test that feature_utilization_rate respects 0-1 boundaries."""
    analytics = UsageAnalytics(
        client_id="cs_1234_test",
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_usage_events=1000,
        unique_features_used=50,
        total_features_available=50,
        feature_utilization_rate=1.0,
        top_features=[],
        usage_trend=TrendDirection.UP,
        usage_growth_rate=0.1
    )

    assert analytics.feature_utilization_rate == 1.0


@pytest.mark.unit
def test_usage_analytics_with_underutilized_features():
    """Test UsageAnalytics with underutilized features tracking."""
    underutilized = [
        {"feature": "advanced_analytics", "usage_count": 45, "adoption_rate": 0.06}
    ]

    analytics = UsageAnalytics(
        client_id="cs_1234_test",
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_usage_events=1000,
        unique_features_used=30,
        total_features_available=50,
        feature_utilization_rate=0.6,
        top_features=[],
        underutilized_features=underutilized,
        usage_trend=TrendDirection.UP,
        usage_growth_rate=0.1
    )

    assert len(analytics.underutilized_features) == 1


@pytest.mark.unit
def test_usage_analytics_with_integrations_and_api():
    """Test UsageAnalytics with integration and API usage."""
    integration_usage = {
        "salesforce": {"active": True, "usage_count": 1247}
    }
    api_usage = {
        "total_calls": 24567,
        "error_rate": 0.012
    }

    analytics = UsageAnalytics(
        client_id="cs_1234_test",
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_usage_events=1000,
        unique_features_used=30,
        total_features_available=50,
        feature_utilization_rate=0.6,
        top_features=[],
        usage_trend=TrendDirection.UP,
        usage_growth_rate=0.1,
        integration_usage=integration_usage,
        api_usage=api_usage
    )

    assert analytics.integration_usage["salesforce"]["usage_count"] == 1247
    assert analytics.api_usage["total_calls"] == 24567


@pytest.mark.unit
def test_usage_analytics_growth_rate():
    """Test usage growth rate can be negative."""
    analytics = UsageAnalytics(
        client_id="cs_1234_test",
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_usage_events=1000,
        unique_features_used=30,
        total_features_available=50,
        feature_utilization_rate=0.6,
        top_features=[],
        usage_trend=TrendDirection.DOWN,
        usage_growth_rate=-0.15
    )

    assert analytics.usage_growth_rate == -0.15


# ============================================================================
# AccountMetrics Model Tests
# ============================================================================

@pytest.mark.unit
def test_account_metrics_valid_creation(sample_client_id, sample_health_score_components):
    """Test creating valid AccountMetrics."""
    # Create required nested models
    health_metrics = HealthMetrics(
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        overall_health_score=82,
        health_score_trend=TrendDirection.UP,
        health_score_change=5,
        health_components={},
        component_trends={}
    )

    engagement_metrics = EngagementMetrics(
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_users=50,
        active_users=42,
        daily_active_users=30,
        weekly_active_users=45,
        monthly_active_users=48,
        activation_rate=0.96,
        engagement_rate=0.84,
        total_logins=500,
        avg_logins_per_user=12.0,
        total_session_minutes=5000,
        avg_session_duration_minutes=10.0,
        total_actions=2000,
        avg_actions_per_session=4.0,
        feature_adoption={},
        engagement_trend=TrendDirection.UP
    )

    usage_analytics = UsageAnalytics(
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_usage_events=1000,
        unique_features_used=30,
        total_features_available=50,
        feature_utilization_rate=0.6,
        top_features=[],
        usage_trend=TrendDirection.UP,
        usage_growth_rate=0.1
    )

    account_metrics = AccountMetrics(
        client_id=sample_client_id,
        client_name="Acme Corporation",
        report_date=date.today(),
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        health_metrics=health_metrics,
        engagement_metrics=engagement_metrics,
        usage_analytics=usage_analytics,
        financial_metrics={
            "current_arr": 72000.0,
            "payment_status": "current"
        },
        renewal_forecast={
            "renewal_probability": 0.89,
            "renewal_status": "on_track"
        },
        executive_summary="Account health strong with positive trends"
    )

    assert account_metrics.client_id == sample_client_id
    assert account_metrics.client_name == "Acme Corporation"
    assert account_metrics.financial_metrics["current_arr"] == 72000.0


@pytest.mark.unit
def test_account_metrics_with_insights(sample_client_id):
    """Test AccountMetrics with key achievements and concerns."""
    health_metrics = HealthMetrics(
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        overall_health_score=85,
        health_score_trend=TrendDirection.UP,
        health_score_change=8,
        health_components={},
        component_trends={}
    )

    engagement_metrics = EngagementMetrics(
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_users=50,
        active_users=42,
        daily_active_users=30,
        weekly_active_users=45,
        monthly_active_users=48,
        activation_rate=0.96,
        engagement_rate=0.84,
        total_logins=500,
        avg_logins_per_user=12.0,
        total_session_minutes=5000,
        avg_session_duration_minutes=10.0,
        total_actions=2000,
        avg_actions_per_session=4.0,
        feature_adoption={},
        engagement_trend=TrendDirection.UP
    )

    usage_analytics = UsageAnalytics(
        client_id=sample_client_id,
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        total_usage_events=1000,
        unique_features_used=30,
        total_features_available=50,
        feature_utilization_rate=0.6,
        top_features=[],
        usage_trend=TrendDirection.UP,
        usage_growth_rate=0.15
    )

    achievements = [
        "Reached 90% feature adoption",
        "Zero P0/P1 support tickets"
    ]
    concerns = [
        "3 users inactive for 30+ days"
    ]
    actions = [
        "Schedule quarterly business review",
        "Present expansion opportunities"
    ]

    account_metrics = AccountMetrics(
        client_id=sample_client_id,
        client_name="Acme Corp",
        report_date=date.today(),
        period_start=datetime(2025, 10, 1),
        period_end=datetime(2025, 10, 31),
        health_metrics=health_metrics,
        engagement_metrics=engagement_metrics,
        usage_analytics=usage_analytics,
        financial_metrics={"current_arr": 72000.0},
        renewal_forecast={"renewal_probability": 0.89},
        executive_summary="Strong performance",
        key_achievements=achievements,
        areas_of_concern=concerns,
        recommended_actions=actions,
        next_csm_touchpoint=date.today() + timedelta(days=7)
    )

    assert len(account_metrics.key_achievements) == 2
    assert len(account_metrics.areas_of_concern) == 1
    assert len(account_metrics.recommended_actions) == 2


# ============================================================================
# CohortAnalysis Model Tests
# ============================================================================

@pytest.mark.unit
def test_cohort_analysis_valid_creation():
    """Test creating valid CohortAnalysis."""
    retention_data = [
        {"month": 1, "retained": 47, "retention_rate": 1.00},
        {"month": 3, "retained": 45, "retention_rate": 0.96}
    ]

    engagement_data = [
        {"month": 1, "avg_health_score": 65, "avg_dau": 18},
        {"month": 3, "avg_health_score": 75, "avg_dau": 26}
    ]

    revenue = {
        "starting_arr": 1980000.0,
        "current_arr": 2150000.0,
        "net_retention_rate": 1.025
    }

    cohort = CohortAnalysis(
        cohort_id="cohort_2025_q1",
        cohort_name="Q1 2025 New Customers",
        cohort_definition={
            "start_date": "2025-01-01",
            "criteria": "customers onboarded in Q1 2025"
        },
        cohort_size=47,
        analysis_date=date(2025, 10, 31),
        months_since_cohort=9,
        retention_by_month=retention_data,
        engagement_by_month=engagement_data,
        revenue_metrics=revenue
    )

    assert cohort.cohort_id == "cohort_2025_q1"
    assert cohort.cohort_size == 47
    assert cohort.months_since_cohort == 9


@pytest.mark.unit
def test_cohort_analysis_with_benchmark():
    """Test CohortAnalysis with benchmark comparison."""
    benchmark = {
        "retention_vs_avg": "above",
        "engagement_vs_avg": "above"
    }

    cohort = CohortAnalysis(
        cohort_id="cohort_test",
        cohort_name="Test Cohort",
        cohort_definition={"criteria": "test"},
        cohort_size=50,
        analysis_date=date.today(),
        months_since_cohort=6,
        retention_by_month=[],
        engagement_by_month=[],
        revenue_metrics={"starting_arr": 1000000.0},
        benchmark_comparison=benchmark
    )

    assert cohort.benchmark_comparison["retention_vs_avg"] == "above"


@pytest.mark.unit
def test_cohort_analysis_default_values():
    """Test that CohortAnalysis has correct default values."""
    cohort = CohortAnalysis(
        cohort_id="cohort_test",
        cohort_name="Test Cohort",
        cohort_definition={"criteria": "test"},
        cohort_size=50,
        analysis_date=date.today(),
        months_since_cohort=6,
        retention_by_month=[],
        engagement_by_month=[],
        revenue_metrics={}
    )

    assert cohort.benchmark_comparison == {}
