"""
Analytics Models
Pydantic models for customer success analytics, metrics, and reporting
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from enum import Enum


class TimeGranularity(str, Enum):
    """Time series granularity"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class TrendDirection(str, Enum):
    """Metric trend direction"""
    UP = "up"
    DOWN = "down"
    FLAT = "flat"


class BenchmarkComparison(str, Enum):
    """Comparison to benchmark"""
    ABOVE = "above"
    BELOW = "below"
    AT = "at"


class HealthMetrics(BaseModel):
    """
    Comprehensive health metrics for a customer.

    Includes all health score components with historical
    trends and benchmark comparisons.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "client_id": "cs_1696800000_acme",
            "period_start": "2025-10-01T00:00:00Z",
            "period_end": "2025-10-31T23:59:59Z",
            "overall_health_score": 82,
            "health_score_trend": "up",
            "health_score_change": 5,
            "health_components": {
                "usage_score": 85,
                "engagement_score": 78,
                "support_score": 92,
                "satisfaction_score": 88,
                "payment_score": 100
            },
            "component_trends": {
                "usage_score": "up",
                "engagement_score": "up",
                "support_score": "flat",
                "satisfaction_score": "down",
                "payment_score": "flat"
            },
            "risk_indicators": [
                {
                    "indicator": "decreased_satisfaction",
                    "severity": "medium",
                    "detected_date": "2025-10-15"
                }
            ],
            "positive_indicators": [
                {
                    "indicator": "increased_usage",
                    "strength": "strong",
                    "detected_date": "2025-10-05"
                }
            ],
            "benchmark_comparison": {
                "overall_health": "above",
                "vs_tier_average": 12,
                "vs_industry_average": 8,
                "percentile": 78
            },
            "predicted_next_period_score": 84,
            "confidence": 0.82
        }
    })

    # Identification
    client_id: str = Field(
        ...,
        description="Customer identifier"
    )
    period_start: datetime = Field(
        ...,
        description="Metrics period start"
    )
    period_end: datetime = Field(
        ...,
        description="Metrics period end"
    )

    # Overall health
    overall_health_score: int = Field(
        ...,
        description="Overall health score (0-100)",
        ge=0,
        le=100
    )
    health_score_trend: TrendDirection = Field(
        ...,
        description="Health score trend direction"
    )
    health_score_change: int = Field(
        ...,
        description="Change from previous period",
        ge=-100,
        le=100
    )

    # Component scores
    health_components: Dict[str, float] = Field(
        ...,
        description="Individual health component scores"
    )
    component_trends: Dict[str, str] = Field(
        ...,
        description="Trend direction for each component"
    )

    # Indicators
    risk_indicators: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detected risk indicators"
    )
    positive_indicators: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Positive health indicators"
    )

    # Benchmarking
    benchmark_comparison: Dict[str, Any] = Field(
        default_factory=dict,
        description="Comparison to benchmarks (tier, industry, etc.)"
    )

    # Predictions
    predicted_next_period_score: Optional[int] = Field(
        None,
        description="Predicted health score for next period",
        ge=0,
        le=100
    )
    confidence: float = Field(
        default=0.0,
        description="Prediction confidence (0-1)",
        ge=0,
        le=1
    )


class EngagementMetrics(BaseModel):
    """
    Customer engagement metrics tracking user activity and interaction.

    Measures depth and breadth of product usage and engagement.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "client_id": "cs_1696800000_acme",
            "period_start": "2025-10-01T00:00:00Z",
            "period_end": "2025-10-31T23:59:59Z",
            "total_users": 50,
            "active_users": 42,
            "daily_active_users": 28,
            "weekly_active_users": 45,
            "monthly_active_users": 48,
            "activation_rate": 0.96,
            "engagement_rate": 0.84,
            "total_logins": 847,
            "avg_logins_per_user": 20.2,
            "total_session_minutes": 12450,
            "avg_session_duration_minutes": 14.7,
            "total_actions": 3821,
            "avg_actions_per_session": 4.5,
            "feature_adoption": {
                "core_features": 0.92,
                "advanced_features": 0.58,
                "recent_features": 0.31
            },
            "power_users": 12,
            "inactive_users": 8,
            "at_risk_users": 3,
            "engagement_trend": "up",
            "vs_previous_period": {
                "active_users_change": 3,
                "logins_change_pct": 0.08,
                "session_duration_change_pct": 0.12
            }
        }
    })

    # Identification
    client_id: str = Field(..., description="Customer identifier")
    period_start: datetime = Field(..., description="Metrics period start")
    period_end: datetime = Field(..., description="Metrics period end")

    # User metrics
    total_users: int = Field(..., description="Total user count", ge=0)
    active_users: int = Field(..., description="Active users in period", ge=0)
    daily_active_users: int = Field(..., description="Average daily active users", ge=0)
    weekly_active_users: int = Field(..., description="Average weekly active users", ge=0)
    monthly_active_users: int = Field(..., description="Monthly active users", ge=0)

    # Engagement rates
    activation_rate: float = Field(
        ...,
        description="User activation rate (activated / total)",
        ge=0,
        le=1
    )
    engagement_rate: float = Field(
        ...,
        description="Engagement rate (active / total)",
        ge=0,
        le=1
    )

    # Activity metrics
    total_logins: int = Field(..., description="Total login events", ge=0)
    avg_logins_per_user: float = Field(
        ...,
        description="Average logins per active user",
        ge=0
    )
    total_session_minutes: int = Field(
        ...,
        description="Total session time in minutes",
        ge=0
    )
    avg_session_duration_minutes: float = Field(
        ...,
        description="Average session duration",
        ge=0
    )
    total_actions: int = Field(..., description="Total user actions", ge=0)
    avg_actions_per_session: float = Field(
        ...,
        description="Average actions per session",
        ge=0
    )

    # Feature adoption
    feature_adoption: Dict[str, float] = Field(
        ...,
        description="Adoption rates by feature category"
    )

    # User segmentation
    power_users: int = Field(
        default=0,
        description="Number of power users (high engagement)",
        ge=0
    )
    inactive_users: int = Field(
        default=0,
        description="Number of inactive users",
        ge=0
    )
    at_risk_users: int = Field(
        default=0,
        description="Number of at-risk users (declining engagement)",
        ge=0
    )

    # Trends
    engagement_trend: TrendDirection = Field(
        ...,
        description="Overall engagement trend"
    )
    vs_previous_period: Dict[str, Any] = Field(
        default_factory=dict,
        description="Changes vs. previous period"
    )


class UsageAnalytics(BaseModel):
    """
    Product usage analytics with feature-level detail.

    Tracks feature usage, adoption patterns, and usage trends.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "client_id": "cs_1696800000_acme",
            "period_start": "2025-10-01T00:00:00Z",
            "period_end": "2025-10-31T23:59:59Z",
            "total_usage_events": 15847,
            "unique_features_used": 42,
            "total_features_available": 68,
            "feature_utilization_rate": 0.62,
            "top_features": [
                {"feature": "dashboard", "usage_count": 2847, "user_count": 45, "adoption_rate": 0.90},
                {"feature": "reports", "usage_count": 1923, "user_count": 38, "adoption_rate": 0.76},
                {"feature": "export", "usage_count": 1456, "user_count": 32, "adoption_rate": 0.64}
            ],
            "underutilized_features": [
                {"feature": "advanced_analytics", "usage_count": 45, "user_count": 3, "adoption_rate": 0.06},
                {"feature": "api_access", "usage_count": 12, "user_count": 2, "adoption_rate": 0.04}
            ],
            "new_feature_adoption": {
                "feature_x": {"launched": "2025-09-15", "adoption_rate": 0.31, "days_since_launch": 46}
            },
            "usage_by_user_role": {
                "admin": {"users": 5, "usage_events": 4821, "avg_per_user": 964},
                "power_user": {"users": 12, "usage_events": 7234, "avg_per_user": 603},
                "standard_user": {"users": 33, "usage_events": 3792, "avg_per_user": 115}
            },
            "integration_usage": {
                "salesforce": {"active": True, "usage_count": 1247, "sync_frequency": "hourly"},
                "slack": {"active": True, "usage_count": 892, "sync_frequency": "real_time"}
            },
            "api_usage": {
                "total_calls": 24567,
                "avg_daily_calls": 792,
                "error_rate": 0.012,
                "rate_limit_reached": False
            },
            "usage_trend": "up",
            "usage_growth_rate": 0.15
        }
    })

    # Identification
    client_id: str = Field(..., description="Customer identifier")
    period_start: datetime = Field(..., description="Metrics period start")
    period_end: datetime = Field(..., description="Metrics period end")

    # Overall usage
    total_usage_events: int = Field(
        ...,
        description="Total feature usage events",
        ge=0
    )
    unique_features_used: int = Field(
        ...,
        description="Number of unique features used",
        ge=0
    )
    total_features_available: int = Field(
        ...,
        description="Total features available to customer",
        ge=1
    )
    feature_utilization_rate: float = Field(
        ...,
        description="Percentage of available features used",
        ge=0,
        le=1
    )

    # Feature breakdown
    top_features: List[Dict[str, Any]] = Field(
        ...,
        description="Most used features with metrics",
        min_length=0
    )
    underutilized_features: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Features with low adoption"
    )
    new_feature_adoption: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Adoption metrics for recently launched features"
    )

    # User segmentation
    usage_by_user_role: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Usage metrics by user role"
    )

    # Integration usage
    integration_usage: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Usage of integrations and connected services"
    )

    # API usage
    api_usage: Dict[str, Any] = Field(
        default_factory=dict,
        description="API usage statistics (if applicable)"
    )

    # Trends
    usage_trend: TrendDirection = Field(
        ...,
        description="Overall usage trend"
    )
    usage_growth_rate: float = Field(
        ...,
        description="Usage growth rate vs. previous period",
        ge=-1
    )


class AccountMetrics(BaseModel):
    """
    Comprehensive account-level metrics combining all dimensions.

    Executive summary of customer health, engagement, and value.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "client_id": "cs_1696800000_acme",
            "client_name": "Acme Corporation",
            "report_date": "2025-10-31",
            "period_start": "2025-10-01T00:00:00Z",
            "period_end": "2025-10-31T23:59:59Z",
            "health_metrics": {},
            "engagement_metrics": {},
            "usage_analytics": {},
            "support_metrics": {
                "tickets_opened": 8,
                "tickets_resolved": 7,
                "avg_resolution_time_hours": 4.2,
                "satisfaction_rating": 4.6
            },
            "financial_metrics": {
                "current_arr": 72000.0,
                "lifetime_value": 156000.0,
                "payment_status": "current",
                "days_until_renewal": 77
            },
            "renewal_forecast": {
                "renewal_probability": 0.89,
                "renewal_status": "on_track",
                "expansion_probability": 0.64,
                "forecasted_arr": 78000.0
            },
            "key_achievements": [
                "Reached 90% feature adoption milestone",
                "Zero support tickets in P0/P1 categories",
                "Engagement increased 15% month-over-month"
            ],
            "areas_of_concern": [
                "User satisfaction declined slightly (4.8 -> 4.6)",
                "3 users inactive for 30+ days"
            ],
            "recommended_actions": [
                "Schedule quarterly business review",
                "Present expansion opportunities",
                "Conduct satisfaction follow-up survey"
            ],
            "next_csm_touchpoint": "2025-11-07",
            "executive_summary": "Account health strong with minor satisfaction decline. Excellent expansion opportunity."
        }
    })

    # Identification
    client_id: str = Field(..., description="Customer identifier")
    client_name: str = Field(..., description="Customer name")
    report_date: date = Field(..., description="Report generation date")
    period_start: datetime = Field(..., description="Reporting period start")
    period_end: datetime = Field(..., description="Reporting period end")

    # Core metrics (references to detailed models)
    health_metrics: HealthMetrics
    engagement_metrics: EngagementMetrics
    usage_analytics: UsageAnalytics

    # Support metrics summary
    support_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary support metrics"
    )

    # Financial metrics
    financial_metrics: Dict[str, Any] = Field(
        ...,
        description="Financial and contract metrics"
    )

    # Renewal information
    renewal_forecast: Dict[str, Any] = Field(
        ...,
        description="Renewal forecast summary"
    )

    # Insights
    key_achievements: List[str] = Field(
        default_factory=list,
        description="Key achievements and positive developments"
    )
    areas_of_concern: List[str] = Field(
        default_factory=list,
        description="Areas requiring attention"
    )
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Recommended CSM actions"
    )

    # Next steps
    next_csm_touchpoint: Optional[date] = Field(
        None,
        description="Next scheduled CSM interaction"
    )
    executive_summary: str = Field(
        ...,
        description="Executive summary of account status"
    )


class CohortAnalysis(BaseModel):
    """
    Cohort analysis for customer groups.

    Tracks retention, engagement, and value metrics
    for customer cohorts over time.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "cohort_id": "cohort_2025_q1",
            "cohort_name": "Q1 2025 New Customers",
            "cohort_definition": {
                "start_date": "2025-01-01",
                "end_date": "2025-03-31",
                "criteria": "customers onboarded in Q1 2025"
            },
            "cohort_size": 47,
            "analysis_date": "2025-10-31",
            "months_since_cohort": 9,
            "retention_by_month": [
                {"month": 1, "retained": 47, "retention_rate": 1.00},
                {"month": 3, "retained": 45, "retention_rate": 0.96},
                {"month": 6, "retained": 43, "retention_rate": 0.91},
                {"month": 9, "retained": 41, "retention_rate": 0.87}
            ],
            "engagement_by_month": [
                {"month": 1, "avg_health_score": 65, "avg_dau": 18},
                {"month": 3, "avg_health_score": 75, "avg_dau": 26},
                {"month": 6, "avg_health_score": 82, "avg_dau": 31},
                {"month": 9, "avg_health_score": 85, "avg_dau": 33}
            ],
            "revenue_metrics": {
                "starting_arr": 1980000.0,
                "current_arr": 2150000.0,
                "expansion_rate": 0.086,
                "churned_arr": 120000.0,
                "net_retention_rate": 1.025
            },
            "benchmark_comparison": {
                "retention_vs_avg": "above",
                "engagement_vs_avg": "above"
            }
        }
    })

    cohort_id: str = Field(..., description="Unique cohort identifier")
    cohort_name: str = Field(..., description="Cohort name")
    cohort_definition: Dict[str, Any] = Field(
        ...,
        description="Cohort definition criteria"
    )
    cohort_size: int = Field(..., description="Initial cohort size", ge=0)
    analysis_date: date = Field(..., description="Analysis date")
    months_since_cohort: int = Field(
        ...,
        description="Months since cohort formation",
        ge=0
    )

    # Retention analysis
    retention_by_month: List[Dict[str, Any]] = Field(
        ...,
        description="Retention metrics by month"
    )

    # Engagement trends
    engagement_by_month: List[Dict[str, Any]] = Field(
        ...,
        description="Engagement metrics by month"
    )

    # Revenue metrics
    revenue_metrics: Dict[str, float] = Field(
        ...,
        description="Revenue and retention metrics"
    )

    # Benchmarking
    benchmark_comparison: Dict[str, str] = Field(
        default_factory=dict,
        description="Comparison to benchmarks"
    )


__all__ = [
    'TimeGranularity',
    'TrendDirection',
    'BenchmarkComparison',
    'HealthMetrics',
    'EngagementMetrics',
    'UsageAnalytics',
    'AccountMetrics',
    'CohortAnalysis'
]
