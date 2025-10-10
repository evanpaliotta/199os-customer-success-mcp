"""
Health & Segmentation Tools
MCP tools for customer health monitoring, scoring, and segmentation functionality
"""

from mcp.server.fastmcp import Context
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, date
from pydantic import BaseModel, Field
from src.models.customer_models import (
    CustomerAccount, HealthScoreComponents, CustomerSegment,
    RiskIndicator, ChurnPrediction, CustomerTier, LifecycleStage,
    HealthTrend, AccountStatus
)
from src.models.analytics_models import (
    HealthMetrics, EngagementMetrics, UsageAnalytics,
    TrendDirection, BenchmarkComparison
)
from src.mock_data import generators as mock
from src.security.input_validation import validate_client_id, ValidationError
from src.utils.file_operations import SafeFileOperations
from src.integrations.mixpanel_client import MixpanelClient

# Import global dependencies
def get_enhanced_agent():
    from server import enhanced_agent
    return enhanced_agent

# Initialize safe file operations
safe_file_ops = SafeFileOperations()


# ============================================================================
# Helper Classes for Type Validation
# ============================================================================

class UsageEngagementRequest(BaseModel):
    """Request model for tracking usage and engagement analytics"""
    client_id: str = Field(..., description="Customer identifier")
    period_start: datetime = Field(..., description="Analysis period start date")
    period_end: datetime = Field(..., description="Analysis period end date")
    granularity: str = Field(
        default="daily",
        description="Data granularity (hourly, daily, weekly, monthly)"
    )
    include_feature_breakdown: bool = Field(
        default=True,
        description="Include feature-level usage breakdown"
    )
    include_user_segmentation: bool = Field(
        default=True,
        description="Include user-level segmentation analysis"
    )
    benchmark_comparison: bool = Field(
        default=True,
        description="Compare against industry benchmarks"
    )


class UsageEngagementResults(BaseModel):
    """Results from usage and engagement tracking"""
    client_id: str = Field(..., description="Customer identifier")
    analysis_period: Dict[str, datetime] = Field(
        ...,
        description="Analysis period boundaries"
    )
    engagement_metrics: EngagementMetrics = Field(
        ...,
        description="Comprehensive engagement metrics"
    )
    usage_analytics: UsageAnalytics = Field(
        ...,
        description="Detailed usage analytics"
    )
    usage_trends: Dict[str, Any] = Field(
        ...,
        description="Usage trend analysis over time"
    )
    engagement_patterns: Dict[str, Any] = Field(
        ...,
        description="Identified engagement patterns and behaviors"
    )
    user_cohorts: Dict[str, Any] = Field(
        ...,
        description="User cohort analysis (power users, at-risk, inactive)"
    )
    feature_adoption_timeline: List[Dict[str, Any]] = Field(
        ...,
        description="Feature adoption progression over time"
    )
    activity_heatmap: Dict[str, Any] = Field(
        ...,
        description="Time-based activity patterns (day/hour)"
    )
    benchmark_insights: Dict[str, Any] = Field(
        ...,
        description="Comparison to industry and tier benchmarks"
    )
    recommendations: List[str] = Field(
        ...,
        description="Actionable recommendations to improve engagement"
    )
    alerts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Usage or engagement alerts requiring attention"
    )


class HealthScoreRequest(BaseModel):
    """Request model for calculating customer health scores"""
    client_id: str = Field(..., description="Customer identifier")
    scoring_model: str = Field(
        default="weighted_composite",
        description="Health scoring methodology (weighted_composite, ml_predictive, custom)"
    )
    component_weights: Optional[Dict[str, float]] = Field(
        None,
        description="Custom weights for health score components (if applicable)"
    )
    lookback_period_days: int = Field(
        default=30,
        description="Days to look back for trend analysis",
        ge=1,
        le=365
    )
    include_predictions: bool = Field(
        default=True,
        description="Include future health score predictions"
    )
    risk_threshold: float = Field(
        default=60.0,
        description="Health score threshold for risk alerts",
        ge=0,
        le=100
    )
    alert_preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Alert configuration and notification preferences"
    )


class HealthScoreResults(BaseModel):
    """Results from health score calculation"""
    client_id: str = Field(..., description="Customer identifier")
    calculation_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When health score was calculated"
    )
    current_health_score: int = Field(
        ...,
        description="Current overall health score (0-100)",
        ge=0,
        le=100
    )
    health_trend: HealthTrend = Field(
        ...,
        description="Health score trend direction"
    )
    score_change: int = Field(
        ...,
        description="Change from previous calculation",
        ge=-100,
        le=100
    )
    component_scores: HealthScoreComponents = Field(
        ...,
        description="Detailed breakdown by component"
    )
    health_metrics: HealthMetrics = Field(
        ...,
        description="Comprehensive health metrics"
    )
    risk_level: str = Field(
        ...,
        description="Overall risk level (low, medium, high, critical)"
    )
    risk_indicators: List[RiskIndicator] = Field(
        default_factory=list,
        description="Identified risk indicators"
    )
    churn_prediction: ChurnPrediction = Field(
        ...,
        description="Churn probability and risk assessment"
    )
    historical_scores: List[Dict[str, Any]] = Field(
        ...,
        description="Historical health score data points"
    )
    predicted_scores: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Future predicted health scores"
    )
    contributing_factors: Dict[str, Any] = Field(
        ...,
        description="Factors influencing current health score"
    )
    improvement_opportunities: List[Dict[str, Any]] = Field(
        ...,
        description="Specific opportunities to improve health"
    )
    automated_alerts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Triggered alerts based on thresholds"
    )
    recommended_actions: List[str] = Field(
        ...,
        description="CSM actions to address health concerns"
    )


class SegmentationRequest(BaseModel):
    """Request model for customer segmentation"""
    segmentation_type: str = Field(
        ...,
        description="Segmentation approach (value_based, usage_based, health_based, industry, lifecycle, custom)"
    )
    criteria: Dict[str, Any] = Field(
        ...,
        description="Segmentation criteria and rules"
    )
    min_segment_size: int = Field(
        default=5,
        description="Minimum customers per segment",
        ge=1
    )
    include_recommendations: bool = Field(
        default=True,
        description="Include segment-specific engagement recommendations"
    )
    benchmark_analysis: bool = Field(
        default=True,
        description="Include benchmark analysis per segment"
    )


class SegmentationResults(BaseModel):
    """Results from customer segmentation analysis"""
    segmentation_id: str = Field(..., description="Unique segmentation identifier")
    segmentation_type: str = Field(..., description="Type of segmentation performed")
    execution_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When segmentation was performed"
    )
    total_customers_analyzed: int = Field(
        ...,
        description="Total number of customers included",
        ge=0
    )
    segments_created: int = Field(
        ...,
        description="Number of segments identified",
        ge=0
    )
    segments: List[CustomerSegment] = Field(
        ...,
        description="Detailed segment definitions and metrics"
    )
    segment_distribution: Dict[str, Any] = Field(
        ...,
        description="Distribution of customers across segments"
    )
    segment_characteristics: Dict[str, Any] = Field(
        ...,
        description="Key characteristics of each segment"
    )
    segment_performance: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Performance metrics by segment"
    )
    cross_segment_analysis: Dict[str, Any] = Field(
        ...,
        description="Comparison and insights across segments"
    )
    engagement_strategies: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Recommended engagement strategies per segment"
    )
    resource_allocation: Dict[str, Any] = Field(
        ...,
        description="Recommended resource allocation across segments"
    )
    segment_migration: Dict[str, Any] = Field(
        ...,
        description="Analysis of segment transitions over time"
    )
    recommendations: List[str] = Field(
        ...,
        description="Strategic recommendations for segment management"
    )


class FeatureAdoptionRequest(BaseModel):
    """Request model for feature adoption tracking"""
    client_id: Optional[str] = Field(
        None,
        description="Specific customer (None for all customers)"
    )
    feature_id: Optional[str] = Field(
        None,
        description="Specific feature (None for all features)"
    )
    time_period_days: int = Field(
        default=90,
        description="Analysis time period in days",
        ge=1,
        le=365
    )
    adoption_threshold: float = Field(
        default=0.20,
        description="Adoption rate threshold (0-1) for classification",
        ge=0,
        le=1
    )
    include_user_personas: bool = Field(
        default=True,
        description="Include adoption by user persona/role"
    )
    optimization_recommendations: bool = Field(
        default=True,
        description="Include optimization recommendations"
    )


class FeatureAdoptionResults(BaseModel):
    """Results from feature adoption tracking"""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When analysis was performed"
    )
    scope: Dict[str, Any] = Field(
        ...,
        description="Analysis scope (customer, feature, time period)"
    )
    overall_adoption_rate: float = Field(
        ...,
        description="Overall feature adoption rate",
        ge=0,
        le=1
    )
    feature_adoption_breakdown: List[Dict[str, Any]] = Field(
        ...,
        description="Adoption metrics for each feature"
    )
    adoption_by_tier: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Feature adoption segmented by customer tier"
    )
    adoption_by_lifecycle: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Feature adoption by lifecycle stage"
    )
    adoption_velocity: Dict[str, Any] = Field(
        ...,
        description="Speed of feature adoption over time"
    )
    adoption_patterns: Dict[str, Any] = Field(
        ...,
        description="Identified adoption patterns and correlations"
    )
    high_value_features: List[Dict[str, Any]] = Field(
        ...,
        description="Features with high adoption and impact"
    )
    underutilized_features: List[Dict[str, Any]] = Field(
        ...,
        description="Features with low adoption requiring attention"
    )
    feature_stickiness: Dict[str, float] = Field(
        ...,
        description="Feature retention and continued usage metrics"
    )
    adoption_barriers: List[Dict[str, Any]] = Field(
        ...,
        description="Identified barriers to adoption"
    )
    success_factors: List[Dict[str, Any]] = Field(
        ...,
        description="Factors correlated with successful adoption"
    )
    optimization_opportunities: List[Dict[str, Any]] = Field(
        ...,
        description="Specific opportunities to increase adoption"
    )
    recommended_actions: List[str] = Field(
        ...,
        description="Actions to drive feature adoption"
    )


class LifecycleManagementRequest(BaseModel):
    """Request model for lifecycle stage management"""
    client_id: Optional[str] = Field(
        None,
        description="Specific customer (None for all customers)"
    )
    current_stage: Optional[LifecycleStage] = Field(
        None,
        description="Filter by current lifecycle stage"
    )
    include_transitions: bool = Field(
        default=True,
        description="Include lifecycle transition analysis"
    )
    intervention_planning: bool = Field(
        default=True,
        description="Include intervention recommendations"
    )
    automation_rules: bool = Field(
        default=True,
        description="Include automated stage transition rules"
    )


class LifecycleManagementResults(BaseModel):
    """Results from lifecycle stage management"""
    management_id: str = Field(..., description="Unique management session identifier")
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When analysis was performed"
    )
    total_customers: int = Field(
        ...,
        description="Total customers analyzed",
        ge=0
    )
    stage_distribution: Dict[str, int] = Field(
        ...,
        description="Customer count by lifecycle stage"
    )
    stage_characteristics: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Key characteristics and metrics per stage"
    )
    stage_transitions: Dict[str, Any] = Field(
        ...,
        description="Historical stage transition patterns"
    )
    transition_triggers: Dict[str, List[str]] = Field(
        ...,
        description="Events and conditions triggering stage transitions"
    )
    average_stage_duration: Dict[str, float] = Field(
        ...,
        description="Average days spent in each lifecycle stage"
    )
    stage_success_metrics: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Success metrics by lifecycle stage"
    )
    at_risk_transitions: List[Dict[str, Any]] = Field(
        ...,
        description="Customers at risk of negative transitions"
    )
    expansion_opportunities: List[Dict[str, Any]] = Field(
        ...,
        description="Customers ready for expansion stage"
    )
    intervention_playbooks: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Stage-specific intervention playbooks"
    )
    automated_workflows: Dict[str, List[Dict[str, Any]]] = Field(
        ...,
        description="Automated workflows by lifecycle stage"
    )
    stage_optimization: Dict[str, List[str]] = Field(
        ...,
        description="Recommendations to optimize each stage"
    )
    recommended_actions: List[Dict[str, Any]] = Field(
        ...,
        description="Prioritized actions by customer/stage"
    )


class AdoptionMilestoneRequest(BaseModel):
    """Request model for product adoption milestone tracking"""
    client_id: Optional[str] = Field(
        None,
        description="Specific customer (None for all customers)"
    )
    milestone_framework: str = Field(
        default="standard",
        description="Milestone framework to use (standard, custom, industry_specific)"
    )
    custom_milestones: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Custom milestone definitions (if using custom framework)"
    )
    include_benchmarks: bool = Field(
        default=True,
        description="Include benchmark time-to-milestone data"
    )
    celebration_recommendations: bool = Field(
        default=True,
        description="Include customer celebration recommendations"
    )


class AdoptionMilestoneResults(BaseModel):
    """Results from adoption milestone tracking"""
    tracking_id: str = Field(..., description="Unique tracking identifier")
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When analysis was performed"
    )
    milestone_framework: str = Field(
        ...,
        description="Milestone framework used"
    )
    total_milestones: int = Field(
        ...,
        description="Total number of milestones defined",
        ge=0
    )
    milestone_definitions: List[Dict[str, Any]] = Field(
        ...,
        description="Detailed milestone definitions and criteria"
    )
    customer_progress: List[Dict[str, Any]] = Field(
        ...,
        description="Milestone progress by customer"
    )
    completion_rates: Dict[str, float] = Field(
        ...,
        description="Overall completion rates by milestone"
    )
    time_to_milestone: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Average, median, and percentile time to reach milestones"
    )
    milestone_correlation: Dict[str, Any] = Field(
        ...,
        description="Correlation between milestones and success outcomes"
    )
    stuck_customers: List[Dict[str, Any]] = Field(
        ...,
        description="Customers stuck at specific milestones"
    )
    fast_track_customers: List[Dict[str, Any]] = Field(
        ...,
        description="Customers progressing faster than benchmarks"
    )
    milestone_blockers: Dict[str, List[str]] = Field(
        ...,
        description="Common blockers preventing milestone completion"
    )
    success_factors: Dict[str, List[str]] = Field(
        ...,
        description="Factors enabling fast milestone completion"
    )
    benchmark_comparison: Dict[str, Any] = Field(
        ...,
        description="Comparison to industry and tier benchmarks"
    )
    celebration_opportunities: List[Dict[str, Any]] = Field(
        ...,
        description="Upcoming milestone celebrations to plan"
    )
    intervention_recommendations: List[Dict[str, Any]] = Field(
        ...,
        description="Interventions for stuck customers"
    )
    recommended_actions: List[str] = Field(
        ...,
        description="Prioritized actions to accelerate adoption"
    )


class ValueTierRequest(BaseModel):
    """Request model for value-based tier segmentation"""
    segmentation_criteria: Dict[str, Any] = Field(
        ...,
        description="Criteria for value tier segmentation (ARR, LTV, potential, etc.)"
    )
    tier_definitions: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Custom tier definitions (if not using default)"
    )
    service_level_mapping: bool = Field(
        default=True,
        description="Include service level recommendations per tier"
    )
    vip_identification: bool = Field(
        default=True,
        description="Identify VIP accounts requiring special treatment"
    )
    resource_planning: bool = Field(
        default=True,
        description="Include CSM resource allocation planning"
    )


class ValueTierResults(BaseModel):
    """Results from value-based tier segmentation"""
    segmentation_id: str = Field(..., description="Unique segmentation identifier")
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When segmentation was performed"
    )
    total_customers: int = Field(
        ...,
        description="Total customers segmented",
        ge=0
    )
    tier_definitions: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Detailed tier definitions and criteria"
    )
    tier_distribution: Dict[str, int] = Field(
        ...,
        description="Customer count by tier"
    )
    tier_metrics: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Key metrics by tier (ARR, LTV, health, etc.)"
    )
    value_concentration: Dict[str, Any] = Field(
        ...,
        description="Analysis of value concentration (80/20 rule, etc.)"
    )
    vip_accounts: List[Dict[str, Any]] = Field(
        ...,
        description="VIP accounts requiring special attention"
    )
    tier_characteristics: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Typical characteristics by tier"
    )
    service_level_recommendations: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Recommended service levels and touch frequencies by tier"
    )
    csm_allocation: Dict[str, Any] = Field(
        ...,
        description="Recommended CSM resource allocation by tier"
    )
    tier_performance: Dict[str, Dict[str, float]] = Field(
        ...,
        description="Performance metrics by tier (retention, NPS, etc.)"
    )
    upgrade_candidates: List[Dict[str, Any]] = Field(
        ...,
        description="Customers likely to move to higher tiers"
    )
    downgrade_risks: List[Dict[str, Any]] = Field(
        ...,
        description="Customers at risk of tier downgrade"
    )
    tier_optimization: Dict[str, List[str]] = Field(
        ...,
        description="Strategies to optimize each tier"
    )
    recommended_actions: List[str] = Field(
        ...,
        description="Strategic actions for tier management"
    )


class EngagementPatternRequest(BaseModel):
    """Request model for behavioral engagement pattern analysis"""
    analysis_scope: str = Field(
        default="all_customers",
        description="Analysis scope (all_customers, segment, individual)"
    )
    scope_filter: Optional[Dict[str, Any]] = Field(
        None,
        description="Filter criteria for scoped analysis"
    )
    pattern_types: List[str] = Field(
        default_factory=lambda: ["temporal", "feature_usage", "communication", "support"],
        description="Types of patterns to analyze"
    )
    lookback_period_days: int = Field(
        default=90,
        description="Days of history to analyze",
        ge=7,
        le=365
    )
    anomaly_detection: bool = Field(
        default=True,
        description="Include anomaly detection in patterns"
    )
    predictive_insights: bool = Field(
        default=True,
        description="Include predictive pattern insights"
    )


class EngagementPatternResults(BaseModel):
    """Results from behavioral engagement pattern analysis"""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    analysis_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When analysis was performed"
    )
    analysis_scope: Dict[str, Any] = Field(
        ...,
        description="Scope and parameters of analysis"
    )
    customers_analyzed: int = Field(
        ...,
        description="Number of customers included in analysis",
        ge=0
    )
    identified_patterns: List[Dict[str, Any]] = Field(
        ...,
        description="Identified behavioral patterns with details"
    )
    temporal_patterns: Dict[str, Any] = Field(
        ...,
        description="Time-based engagement patterns (day, time, seasonality)"
    )
    feature_usage_patterns: Dict[str, Any] = Field(
        ...,
        description="Feature usage and adoption patterns"
    )
    communication_patterns: Dict[str, Any] = Field(
        ...,
        description="Customer communication and response patterns"
    )
    support_patterns: Dict[str, Any] = Field(
        ...,
        description="Support interaction patterns"
    )
    user_personas: List[Dict[str, Any]] = Field(
        ...,
        description="Identified user personas based on behavior"
    )
    success_patterns: Dict[str, Any] = Field(
        ...,
        description="Patterns correlated with customer success"
    )
    risk_patterns: Dict[str, Any] = Field(
        ...,
        description="Patterns correlated with churn risk"
    )
    anomalies: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detected anomalies requiring attention"
    )
    pattern_transitions: Dict[str, Any] = Field(
        ...,
        description="How patterns change over lifecycle"
    )
    predictive_insights: Dict[str, Any] = Field(
        ...,
        description="Predictive insights based on patterns"
    )
    engagement_optimization: List[Dict[str, Any]] = Field(
        ...,
        description="Opportunities to optimize engagement based on patterns"
    )
    recommended_actions: List[str] = Field(
        ...,
        description="Actions to leverage pattern insights"
    )


# ============================================================================
# Tool 1: Track Usage & Engagement (Process 87)
# ============================================================================


# ============================================================================
# Helper Functions
# ============================================================================

def _generate_value_segments(criteria: Dict[str, Any], min_size: int) -> List[CustomerSegment]:
    """Generate value-based customer segments"""
    segments = [
        CustomerSegment(
            segment_id="seg_vip_strategic",
            segment_name="VIP Strategic Accounts",
            segment_type="value_based",
            criteria={"min_arr": 100000, "strategic_value": "high"},
            characteristics={
                "typical_arr_range": "$100k-$500k+",
                "company_size": "Enterprise (500+ employees)",
                "growth_stage": "Established market leaders"
            },
            engagement_strategy={
                "csm_touch_frequency": "weekly",
                "ebr_frequency": "quarterly",
                "success_programs": ["executive_advisory", "strategic_planning", "dedicated_support"]
            },
            success_metrics={"target_health_score": 90, "target_nps": 60, "target_retention_rate": 0.98},
            customer_count=mock.random_int(max(min_size, 8), 25),
            total_arr=mock.random_float(1500000, 5000000),
            avg_health_score=mock.random_float(82, 95)
        ),
        CustomerSegment(
            segment_id="seg_high_value",
            segment_name="High-Value Growth Accounts",
            segment_type="value_based",
            criteria={"min_arr": 50000, "max_arr": 100000, "growth_potential": "high"},
            characteristics={
                "typical_arr_range": "$50k-$100k",
                "company_size": "Mid-market (100-500 employees)",
                "growth_stage": "Scaling rapidly"
            },
            engagement_strategy={
                "csm_touch_frequency": "bi-weekly",
                "ebr_frequency": "semi-annual",
                "success_programs": ["growth_acceleration", "best_practices", "peer_networking"]
            },
            success_metrics={"target_health_score": 85, "target_nps": 55, "target_retention_rate": 0.95},
            customer_count=mock.random_int(max(min_size, 15), 45),
            total_arr=mock.random_float(1000000, 3500000),
            avg_health_score=mock.random_float(78, 90)
        ),
        CustomerSegment(
            segment_id="seg_standard",
            segment_name="Standard Value Accounts",
            segment_type="value_based",
            criteria={"min_arr": 10000, "max_arr": 50000},
            characteristics={
                "typical_arr_range": "$10k-$50k",
                "company_size": "Small-medium business (10-100 employees)",
                "growth_stage": "Stable growth"
            },
            engagement_strategy={
                "csm_touch_frequency": "monthly",
                "ebr_frequency": "annual",
                "success_programs": ["automated_onboarding", "self_service", "group_training"]
            },
            success_metrics={"target_health_score": 80, "target_nps": 50, "target_retention_rate": 0.90},
            customer_count=mock.random_int(max(min_size, 30), 100),
            total_arr=mock.random_float(800000, 3000000),
            avg_health_score=mock.random_float(72, 85)
        )
    ]
    return segments



def _generate_usage_segments(criteria: Dict[str, Any], min_size: int) -> List[CustomerSegment]:
    """Generate usage-based customer segments"""
    segments = [
        CustomerSegment(
            segment_id="seg_power_users",
            segment_name="Power Users",
            segment_type="usage_based",
            criteria={"usage_percentile": 90, "feature_adoption": 0.80},
            customer_count=mock.random_int(max(min_size, 10), 30),
            total_arr=mock.random_float(500000, 2000000),
            avg_health_score=mock.random_float(85, 98)
        ),
        CustomerSegment(
            segment_id="seg_active_users",
            segment_name="Active Regular Users",
            segment_type="usage_based",
            criteria={"usage_percentile": 50, "min_engagement_rate": 0.60},
            customer_count=mock.random_int(max(min_size, 30), 80),
            total_arr=mock.random_float(1000000, 3500000),
            avg_health_score=mock.random_float(70, 85)
        ),
        CustomerSegment(
            segment_id="seg_casual_users",
            segment_name="Casual Users",
            segment_type="usage_based",
            criteria={"usage_percentile": 25, "max_engagement_rate": 0.50},
            customer_count=mock.random_int(max(min_size, 20), 50),
            total_arr=mock.random_float(400000, 1500000),
            avg_health_score=mock.random_float(55, 70)
        )
    ]
    return segments



def _generate_health_segments(criteria: Dict[str, Any], min_size: int) -> List[CustomerSegment]:
    """Generate health-based customer segments"""
    segments = [
        CustomerSegment(
            segment_id="seg_healthy",
            segment_name="Healthy & Thriving",
            segment_type="health_based",
            criteria={"min_health_score": 80},
            customer_count=mock.random_int(max(min_size, 25), 70),
            total_arr=mock.random_float(1500000, 4000000),
            avg_health_score=mock.random_float(85, 95)
        ),
        CustomerSegment(
            segment_id="seg_moderate",
            segment_name="Moderate Health",
            segment_type="health_based",
            criteria={"min_health_score": 60, "max_health_score": 80},
            customer_count=mock.random_int(max(min_size, 20), 50),
            total_arr=mock.random_float(800000, 2500000),
            avg_health_score=mock.random_float(65, 78)
        ),
        CustomerSegment(
            segment_id="seg_at_risk",
            segment_name="At Risk - Intervention Needed",
            segment_type="health_based",
            criteria={"max_health_score": 60},
            customer_count=mock.random_int(max(min_size, 5), 20),
            total_arr=mock.random_float(300000, 1000000),
            avg_health_score=mock.random_float(35, 58)
        )
    ]
    return segments



def _generate_industry_segments(criteria: Dict[str, Any], min_size: int) -> List[CustomerSegment]:
    """Generate industry-based customer segments"""
    industries = criteria.get("industries", ["SaaS", "Financial Services", "Healthcare", "Retail"])
    segments = []

    for industry in industries[:4]:
        segments.append(CustomerSegment(
            segment_id=f"seg_industry_{industry.lower().replace(' ', '_')}",
            segment_name=f"{industry} Vertical",
            segment_type="industry",
            criteria={"industry": industry},
            customer_count=mock.random_int(max(min_size, 8), 40),
            total_arr=mock.random_float(500000, 2500000),
            avg_health_score=mock.random_float(70, 88)
        ))

    return segments



def _generate_lifecycle_segments(criteria: Dict[str, Any], min_size: int) -> List[CustomerSegment]:
    """Generate lifecycle-based customer segments"""
    segments = [
        CustomerSegment(
            segment_id="seg_onboarding",
            segment_name="Onboarding",
            segment_type="lifecycle",
            criteria={"lifecycle_stage": "onboarding"},
            customer_count=mock.random_int(max(min_size, 10), 30),
            total_arr=mock.random_float(400000, 1200000),
            avg_health_score=mock.random_float(60, 75)
        ),
        CustomerSegment(
            segment_id="seg_active",
            segment_name="Active & Engaged",
            segment_type="lifecycle",
            criteria={"lifecycle_stage": "active"},
            customer_count=mock.random_int(max(min_size, 40), 100),
            total_arr=mock.random_float(2000000, 6000000),
            avg_health_score=mock.random_float(75, 90)
        ),
        CustomerSegment(
            segment_id="seg_expansion",
            segment_name="Expansion Opportunity",
            segment_type="lifecycle",
            criteria={"lifecycle_stage": "expansion"},
            customer_count=mock.random_int(max(min_size, 8), 25),
            total_arr=mock.random_float(800000, 2500000),
            avg_health_score=mock.random_float(80, 95)
        ),
        CustomerSegment(
            segment_id="seg_renewal",
            segment_name="Renewal Focus",
            segment_type="lifecycle",
            criteria={"lifecycle_stage": "renewal"},
            customer_count=mock.random_int(max(min_size, 15), 40),
            total_arr=mock.random_float(1000000, 3000000),
            avg_health_score=mock.random_float(70, 88)
        )
    ]
    return segments



def _generate_custom_segments(criteria: Dict[str, Any], min_size: int) -> List[CustomerSegment]:
    """Generate custom customer segments"""
    num_segments = criteria.get("num_segments", 3)
    segments = []

    for i in range(num_segments):
        segments.append(CustomerSegment(
            segment_id=f"seg_custom_{i+1}",
            segment_name=f"Custom Segment {i+1}",
            segment_type="custom",
            criteria=criteria.get("segment_criteria", {}),
            customer_count=mock.random_int(max(min_size, 10), 50),
            total_arr=mock.random_float(500000, 2500000),
            avg_health_score=mock.random_float(65, 88)
        ))

    return segments



def _calculate_pareto(segments: List[CustomerSegment]) -> Dict[str, Any]:
    """Calculate Pareto principle (80/20 rule) for segments"""
    total_arr = sum(seg.total_arr for seg in segments)
    sorted_segments = sorted(segments, key=lambda s: s.total_arr, reverse=True)

    cumulative_arr = 0
    top_segments_count = 0

    for seg in sorted_segments:
        cumulative_arr += seg.total_arr
        top_segments_count += 1
        if cumulative_arr >= total_arr * 0.80:
            break

    return {
        "top_20_percent_count": top_segments_count,
        "represents_80_percent_arr": True,
        "concentration_ratio": round(cumulative_arr / total_arr, 2)
    }



def _recommend_channels(segment: CustomerSegment) -> List[str]:
    """Recommend communication channels for a segment"""
    if segment.total_arr / segment.customer_count > 100000:
        return ["direct_call", "executive_email", "in_person", "video_conference"]
    elif segment.total_arr / segment.customer_count > 50000:
        return ["video_conference", "email", "in_app", "phone"]
    else:
        return ["email", "in_app", "automated_campaigns", "self_service"]



def _recommend_content(segment: CustomerSegment, seg_type: str) -> Dict[str, Any]:
    """Recommend content strategy for a segment"""
    avg_arr = segment.total_arr / segment.customer_count if segment.customer_count > 0 else 0

    if avg_arr > 100000:
        return {
            "personalization_level": "high",
            "content_types": ["custom_analysis", "strategic_insights", "executive_briefings"],
            "frequency": "weekly"
        }
    elif avg_arr > 25000:
        return {
            "personalization_level": "medium",
            "content_types": ["best_practices", "use_cases", "product_updates"],
            "frequency": "bi-weekly"
        }
    else:
        return {
            "personalization_level": "low",
            "content_types": ["newsletters", "tutorials", "community_content"],
            "frequency": "monthly"
        }



def _recommend_automation(segment: CustomerSegment) -> str:
    """Recommend automation level for a segment"""
    avg_arr = segment.total_arr / segment.customer_count if segment.customer_count > 0 else 0

    if avg_arr > 75000:
        return "low"  # High-touch, less automation
    elif avg_arr > 25000:
        return "medium"  # Balanced approach
    else:
        return "high"  # Heavy automation, tech-touch



def _define_escalation_criteria(segment: CustomerSegment) -> List[str]:
    """Define escalation criteria for a segment"""
    criteria = ["health_score_below_60", "support_ticket_severity_critical"]

    avg_arr = segment.total_arr / segment.customer_count if segment.customer_count > 0 else 0

    if avg_arr > 75000:
        criteria.extend(["any_negative_sentiment", "executive_complaint", "churn_signal"])
    elif avg_arr > 25000:
        criteria.extend(["multiple_negative_interactions", "renewal_risk"])
    else:
        criteria.append("multiple_churn_indicators")

    return criteria


# ============================================================================
# Tool 4: Track Feature Adoption (Process 90)
# ============================================================================


def _get_stage_adoption_pattern(stage: str) -> str:
    """Get typical adoption pattern for lifecycle stage"""
    patterns = {
        "onboarding": "Core features first, then expanding to advanced",
        "active": "Steady adoption across all feature categories",
        "expansion": "Heavy focus on advanced and integration features",
        "renewal": "Maintenance mode with selective new feature adoption"
    }
    return patterns.get(stage, "Varied adoption patterns")


# ============================================================================
# Tool 5: Manage Lifecycle Stages (Process 91)
# ============================================================================



# ============================================================================
# MCP Tool Registration
# ============================================================================

def register_tools(mcp):
    """Register all health & segmentation tools with the MCP instance"""

    @mcp.tool()
    def track_usage_engagement(
        ctx: Context,
        client_id: str,
        period_start: str,
        period_end: str,
        granularity: str = "daily",
        include_feature_breakdown: bool = True,
        include_user_segmentation: bool = True,
        benchmark_comparison: bool = True
    ) -> str:
        """
        Monitor usage and engagement analytics for comprehensive customer activity tracking.

        This tool provides deep insights into customer product usage patterns, user engagement
        levels, feature adoption, and activity trends. It enables CSMs to identify engagement
        opportunities, detect at-risk users, and optimize customer success strategies.

        Key Capabilities:
        - Real-time usage tracking with configurable granularity
        - Feature-level adoption and utilization analysis
        - User segmentation (power users, active, at-risk, inactive)
        - Temporal engagement patterns and activity heatmaps
        - Benchmark comparisons against industry and tier averages
        - Engagement anomaly detection and alerts
        - Actionable recommendations to improve engagement

        Args:
            ctx: MCP context for logging and operations
            client_id: Customer identifier to analyze
            period_start: Analysis start date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
            period_end: Analysis end date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
            granularity: Data granularity - "hourly", "daily", "weekly", or "monthly"
            include_feature_breakdown: Include detailed feature-level usage breakdown
            include_user_segmentation: Include user cohort and segmentation analysis
            benchmark_comparison: Compare metrics against industry benchmarks

        Returns:
            JSON string containing comprehensive usage and engagement analytics with:
            - Engagement metrics (DAU, WAU, MAU, engagement rates)
            - Usage analytics (sessions, actions, feature usage)
            - User cohorts and segmentation
            - Temporal patterns and activity heatmaps
            - Benchmark comparisons and insights
            - Recommendations and alerts

        Raises:
            ValidationError: If client_id is invalid or dates are malformed

        Example:
            >>> result = track_usage_engagement(
            ...     ctx,
            ...     "cs_1696800000_acme",
            ...     "2025-10-01T00:00:00",
            ...     "2025-10-31T23:59:59",
            ...     granularity="daily",
            ...     benchmark_comparison=True
            ... )

        MCP Process: 87 - Usage & Engagement Tracking
        """
        try:
            # Validate client_id
            validate_client_id(client_id)

            # Parse dates
            start_dt = datetime.fromisoformat(period_start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(period_end.replace('Z', '+00:00'))

            # Validate date range
            if end_dt <= start_dt:
                raise ValidationError("period_end must be after period_start")

            days_diff = (end_dt - start_dt).days
            if days_diff > 365:
                raise ValidationError("Analysis period cannot exceed 365 days")

            ctx.info(f"Tracking usage and engagement for {client_id} from {period_start} to {period_end}")

            # Initialize Mixpanel client and track this analytics query
            mixpanel = MixpanelClient()
            mixpanel.track_event(
                user_id=client_id,
                event_name="usage_engagement_tracked",
                properties={
                    "period_start": period_start,
                    "period_end": period_end,
                    "granularity": granularity,
                    "days_analyzed": days_diff,
                    "feature_breakdown": include_feature_breakdown,
                    "user_segmentation": include_user_segmentation,
                    "benchmark_comparison": benchmark_comparison
                }
            )

            # Generate mock customer account
            customer = mock.generate_customer_account(client_id=client_id)

            # Generate comprehensive engagement metrics
            engagement_metrics = EngagementMetrics(
                client_id=client_id,
                period_start=start_dt,
                period_end=end_dt,
                total_users=mock.random_int(30, 100),
                active_users=mock.random_int(25, 95),
                daily_active_users=mock.random_int(15, 60),
                weekly_active_users=mock.random_int(20, 80),
                monthly_active_users=mock.random_int(25, 95),
                activation_rate=mock.random_float(0.75, 0.98),
                engagement_rate=mock.random_float(0.65, 0.92),
                total_logins=mock.random_int(500, 3000),
                avg_logins_per_user=mock.random_float(8.0, 35.0),
                total_session_minutes=mock.random_int(8000, 50000),
                avg_session_duration_minutes=mock.random_float(10.0, 45.0),
                total_actions=mock.random_int(2000, 15000),
                avg_actions_per_session=mock.random_float(3.0, 12.0),
                feature_adoption={
                    "core_features": mock.random_float(0.80, 0.98),
                    "advanced_features": mock.random_float(0.40, 0.75),
                    "recent_features": mock.random_float(0.15, 0.50)
                },
                power_users=mock.random_int(5, 20),
                inactive_users=mock.random_int(2, 15),
                at_risk_users=mock.random_int(1, 10),
                engagement_trend=mock.random_choice([TrendDirection.UP, TrendDirection.FLAT, TrendDirection.DOWN]),
                vs_previous_period={
                    "active_users_change": mock.random_int(-5, 10),
                    "logins_change_pct": mock.random_float(-0.15, 0.25),
                    "session_duration_change_pct": mock.random_float(-0.10, 0.30)
                }
            )

            # Generate usage analytics
            usage_analytics = UsageAnalytics(
                client_id=client_id,
                period_start=start_dt,
                period_end=end_dt,
                total_usage_events=mock.random_int(10000, 80000),
                unique_features_used=mock.random_int(30, 75),
                total_features_available=mock.random_int(60, 100),
                feature_utilization_rate=mock.random_float(0.45, 0.85),
                top_features=[
                    {
                        "feature": feature,
                        "usage_count": mock.random_int(1000, 5000),
                        "user_count": mock.random_int(20, 80),
                        "adoption_rate": mock.random_float(0.60, 0.95)
                    }
                    for feature in ["dashboard", "reports", "export", "collaboration", "analytics"]
                ],
                underutilized_features=[
                    {
                        "feature": feature,
                        "usage_count": mock.random_int(10, 200),
                        "user_count": mock.random_int(2, 15),
                        "adoption_rate": mock.random_float(0.02, 0.20)
                    }
                    for feature in ["advanced_analytics", "api_access", "custom_integrations"]
                ],
                new_feature_adoption={
                    "feature_x": {
                        "launched": (start_dt - timedelta(days=45)).isoformat(),
                        "adoption_rate": mock.random_float(0.20, 0.50),
                        "days_since_launch": 45
                    }
                },
                usage_by_user_role={
                    "admin": {"users": mock.random_int(3, 8), "usage_events": mock.random_int(3000, 8000), "avg_per_user": 750},
                    "power_user": {"users": mock.random_int(10, 25), "usage_events": mock.random_int(5000, 15000), "avg_per_user": 600},
                    "standard_user": {"users": mock.random_int(20, 60), "usage_events": mock.random_int(2000, 8000), "avg_per_user": 120}
                },
                integration_usage={
                    "salesforce": {"active": True, "usage_count": mock.random_int(800, 2000), "sync_frequency": "hourly"},
                    "slack": {"active": True, "usage_count": mock.random_int(500, 1500), "sync_frequency": "real_time"}
                },
                api_usage={
                    "total_calls": mock.random_int(15000, 50000),
                    "avg_daily_calls": mock.random_int(500, 1500),
                    "error_rate": mock.random_float(0.005, 0.025),
                    "rate_limit_reached": False
                },
                usage_trend=mock.random_choice([TrendDirection.UP, TrendDirection.FLAT, TrendDirection.DOWN]),
                usage_growth_rate=mock.random_float(-0.05, 0.35)
            )

            # Generate usage trends over time
            usage_trends = {
                "daily_trends": [
                    {
                        "date": (start_dt + timedelta(days=i)).strftime("%Y-%m-%d"),
                        "active_users": mock.random_int(20, 80),
                        "sessions": mock.random_int(50, 200),
                        "total_usage_minutes": mock.random_int(500, 2000)
                    }
                    for i in range(0, days_diff, max(1, days_diff // 30))
                ],
                "trend_analysis": {
                    "overall_direction": usage_analytics.usage_trend,
                    "volatility": mock.random_float(0.1, 0.3),
                    "seasonality_detected": mock.random_choice([True, False])
                }
            }

            # Engagement patterns
            engagement_patterns = {
                "peak_usage_hours": [9, 10, 11, 14, 15, 16],
                "peak_usage_days": ["Tuesday", "Wednesday", "Thursday"],
                "weekend_engagement": mock.random_float(0.15, 0.35),
                "engagement_consistency": mock.random_float(0.65, 0.90),
                "behavioral_segments": {
                    "daily_users": engagement_metrics.daily_active_users,
                    "weekly_users": engagement_metrics.weekly_active_users - engagement_metrics.daily_active_users,
                    "monthly_users": engagement_metrics.monthly_active_users - engagement_metrics.weekly_active_users
                }
            }

            # User cohorts analysis
            user_cohorts = {
                "power_users": {
                    "count": engagement_metrics.power_users,
                    "definition": "Users in top 20% of engagement",
                    "avg_sessions_per_week": mock.random_float(15.0, 30.0),
                    "avg_features_used": mock.random_int(35, 60),
                    "health_score": mock.random_int(85, 100)
                },
                "active_users": {
                    "count": engagement_metrics.active_users - engagement_metrics.power_users,
                    "definition": "Regular users meeting minimum activity threshold",
                    "avg_sessions_per_week": mock.random_float(5.0, 12.0),
                    "avg_features_used": mock.random_int(15, 30),
                    "health_score": mock.random_int(70, 84)
                },
                "at_risk_users": {
                    "count": engagement_metrics.at_risk_users,
                    "definition": "Users with declining engagement patterns",
                    "avg_sessions_per_week": mock.random_float(1.0, 3.0),
                    "avg_features_used": mock.random_int(5, 12),
                    "health_score": mock.random_int(30, 55),
                    "risk_factors": ["Decreased login frequency", "Reduced feature usage", "No recent activity"]
                },
                "inactive_users": {
                    "count": engagement_metrics.inactive_users,
                    "definition": "Users with no activity in analysis period",
                    "days_since_last_activity": mock.random_int(30, 180),
                    "reactivation_priority": "high"
                }
            }

            # Feature adoption timeline
            feature_adoption_timeline = [
                {
                    "milestone": f"Week {i+1}",
                    "week_start": (start_dt + timedelta(weeks=i)).strftime("%Y-%m-%d"),
                    "core_adoption": min(0.98, 0.50 + (i * 0.08)),
                    "advanced_adoption": min(0.75, 0.20 + (i * 0.09)),
                    "recent_adoption": min(0.50, 0.05 + (i * 0.07))
                }
                for i in range(min(days_diff // 7, 12))
            ]

            # Activity heatmap
            activity_heatmap = {
                "by_hour": {str(hour): mock.random_int(50, 300) for hour in range(24)},
                "by_day_of_week": {
                    day: mock.random_int(200, 1500)
                    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                },
                "peak_periods": [
                    {"period": "Weekday mornings (9-12)", "engagement_index": 1.35},
                    {"period": "Weekday afternoons (14-17)", "engagement_index": 1.28},
                    {"period": "Weekend", "engagement_index": 0.42}
                ]
            }

            # Benchmark insights
            tier_average_dau = 35
            industry_average_dau = 40
            benchmark_insights = {
                "engagement_vs_tier": "above" if engagement_metrics.daily_active_users > tier_average_dau else "below",
                "engagement_vs_industry": "above" if engagement_metrics.daily_active_users > industry_average_dau else "below",
                "dau_percentile": mock.random_int(55, 90),
                "feature_adoption_percentile": mock.random_int(60, 95),
                "session_duration_percentile": mock.random_int(50, 85),
                "key_insights": [
                    f"Engagement rate {'+' if engagement_metrics.engagement_rate > 0.75 else '-'} industry average",
                    f"Feature utilization {usage_analytics.feature_utilization_rate:.1%} vs. {0.65:.1%} tier average",
                    f"Power user ratio {engagement_metrics.power_users / engagement_metrics.total_users:.1%} vs. {0.20:.1%} typical"
                ]
            } if benchmark_comparison else {}

            # Generate recommendations
            recommendations = []

            if engagement_metrics.at_risk_users > 0:
                recommendations.append(f"Re-engage {engagement_metrics.at_risk_users} at-risk users with targeted outreach and training")

            if engagement_metrics.inactive_users > 0:
                recommendations.append(f"Launch reactivation campaign for {engagement_metrics.inactive_users} inactive users")

            if usage_analytics.feature_utilization_rate < 0.60:
                recommendations.append("Increase feature adoption through guided tours and in-app messaging")

            if len(usage_analytics.underutilized_features) > 0:
                top_underutilized = usage_analytics.underutilized_features[0]["feature"]
                recommendations.append(f"Create targeted campaign to promote '{top_underutilized}' feature")

            if engagement_metrics.avg_session_duration_minutes < 15:
                recommendations.append("Improve session depth with better in-product guidance and onboarding")

            if engagement_patterns.get("weekend_engagement", 0) < 0.20:
                recommendations.append("Consider async features or resources to support weekend/off-hours usage")

            # Generate alerts
            alerts = []

            if engagement_metrics.engagement_trend == TrendDirection.DOWN:
                alerts.append({
                    "type": "engagement_decline",
                    "severity": "high",
                    "message": f"Engagement trending down: {engagement_metrics.vs_previous_period.get('logins_change_pct', 0):.1%} decrease in logins",
                    "action_required": "Investigate root cause and launch re-engagement initiatives"
                })

            if engagement_metrics.at_risk_users / engagement_metrics.total_users > 0.15:
                alerts.append({
                    "type": "high_at_risk_ratio",
                    "severity": "high",
                    "message": f"{engagement_metrics.at_risk_users / engagement_metrics.total_users:.1%} of users at risk of churn",
                    "action_required": "Prioritize at-risk user intervention and support"
                })

            if usage_analytics.api_usage.get("error_rate", 0) > 0.02:
                alerts.append({
                    "type": "api_errors",
                    "severity": "medium",
                    "message": f"API error rate at {usage_analytics.api_usage.get('error_rate', 0):.2%}",
                    "action_required": "Review API integration health and address error sources"
                })

            # Construct results
            results = UsageEngagementResults(
                client_id=client_id,
                analysis_period={
                    "start": start_dt,
                    "end": end_dt,
                    "days": days_diff,
                    "granularity": granularity
                },
                engagement_metrics=engagement_metrics,
                usage_analytics=usage_analytics,
                usage_trends=usage_trends,
                engagement_patterns=engagement_patterns,
                user_cohorts=user_cohorts,
                feature_adoption_timeline=feature_adoption_timeline,
                activity_heatmap=activity_heatmap,
                benchmark_insights=benchmark_insights,
                recommendations=recommendations,
                alerts=alerts
            )

            # Track engagement metrics to Mixpanel for analytics
            mixpanel.track_event(
                user_id=client_id,
                event_name="engagement_metrics_calculated",
                properties={
                    "total_users": engagement_metrics.total_users,
                    "active_users": engagement_metrics.active_users,
                    "daily_active_users": engagement_metrics.daily_active_users,
                    "engagement_rate": engagement_metrics.engagement_rate,
                    "power_users": engagement_metrics.power_users,
                    "at_risk_users": engagement_metrics.at_risk_users,
                    "inactive_users": engagement_metrics.inactive_users,
                    "engagement_trend": engagement_metrics.engagement_trend,
                    "feature_utilization_rate": usage_analytics.feature_utilization_rate,
                    "total_usage_events": usage_analytics.total_usage_events,
                    "alerts_count": len(alerts),
                    "has_critical_alerts": any(a["severity"] == "high" for a in alerts)
                }
            )

            # Update Mixpanel profile with latest engagement metrics
            mixpanel.set_profile(
                user_id=client_id,
                properties={
                    "last_engagement_analysis": datetime.now().isoformat(),
                    "current_engagement_rate": engagement_metrics.engagement_rate,
                    "current_active_users": engagement_metrics.active_users,
                    "engagement_trend": engagement_metrics.engagement_trend,
                    "at_risk_users": engagement_metrics.at_risk_users
                }
            )

            # Flush events to ensure immediate delivery
            mixpanel.flush()

            ctx.info(f"Successfully tracked usage and engagement for {client_id}")
            return results.model_dump_json(indent=2)

        except ValidationError as e:
            ctx.error(f"Validation error in track_usage_engagement: {str(e)}")
            raise
        except Exception as e:
            ctx.error(f"Error in track_usage_engagement: {str(e)}")
            raise


    # ============================================================================
    # Tool 2: Calculate Health Score (Process 88)
    # ============================================================================


    @mcp.tool()
    def calculate_health_score(
        ctx: Context,
        client_id: str,
        scoring_model: str = "weighted_composite",
        component_weights: Optional[Dict[str, float]] = None,
        lookback_period_days: int = 30,
        include_predictions: bool = True,
        risk_threshold: float = 60.0
    ) -> str:
        """
        Calculate automated health scores with risk alerts and churn prediction.

        This comprehensive health scoring system combines multiple data sources to generate
        accurate, actionable customer health assessments. It includes component-level scoring,
        trend analysis, risk identification, and predictive analytics to enable proactive
        customer success management.

        Key Capabilities:
        - Multi-component health scoring (usage, engagement, support, satisfaction, payment)
        - Configurable scoring models and custom weighting
        - Historical trend analysis and pattern detection
        - Automated risk indicator identification
        - ML-powered churn prediction with confidence scoring
        - Health score forecasting and predictive insights
        - Automated alert generation based on thresholds
        - Actionable recommendations for health improvement

        Args:
            ctx: MCP context for logging and operations
            client_id: Customer identifier to score
            scoring_model: Methodology - "weighted_composite", "ml_predictive", or "custom"
            component_weights: Custom weights for health components (if using custom model)
            lookback_period_days: Days of history for trend analysis (1-365)
            include_predictions: Include future health score predictions
            risk_threshold: Health score threshold for risk alerts (0-100)

        Returns:
            JSON string containing comprehensive health score analysis with:
            - Current health score and component breakdown
            - Health trend and historical scores
            - Risk indicators and churn prediction
            - Predicted future scores
            - Contributing factors and improvement opportunities
            - Automated alerts and recommended actions

        Raises:
            ValidationError: If client_id is invalid or parameters are out of range

        Example:
            >>> result = calculate_health_score(
            ...     ctx,
            ...     "cs_1696800000_acme",
            ...     scoring_model="weighted_composite",
            ...     lookback_period_days=30,
            ...     risk_threshold=65.0
            ... )

        MCP Process: 88 - Automated Health Scoring
        """
        try:
            # Validate client_id
            validate_client_id(client_id)

            # Validate parameters
            if lookback_period_days < 1 or lookback_period_days > 365:
                raise ValidationError("lookback_period_days must be between 1 and 365")

            if risk_threshold < 0 or risk_threshold > 100:
                raise ValidationError("risk_threshold must be between 0 and 100")

            if scoring_model not in ["weighted_composite", "ml_predictive", "custom"]:
                raise ValidationError("scoring_model must be 'weighted_composite', 'ml_predictive', or 'custom'")

            if scoring_model == "custom" and not component_weights:
                raise ValidationError("component_weights required when using custom scoring_model")

            ctx.info(f"Calculating health score for {client_id} using {scoring_model} model")

            # Generate mock customer account
            customer = mock.generate_customer_account(client_id=client_id)

            # Generate component scores
            usage_score = mock.random_float(60.0, 95.0)
            engagement_score = mock.random_float(55.0, 90.0)
            support_score = mock.random_float(70.0, 98.0)
            satisfaction_score = mock.random_float(65.0, 95.0)
            payment_score = mock.random_float(85.0, 100.0)

            # Use custom weights if provided, otherwise use defaults
            if component_weights:
                weights = component_weights
            else:
                weights = {
                    "usage_weight": 0.35,
                    "engagement_weight": 0.25,
                    "support_weight": 0.15,
                    "satisfaction_weight": 0.15,
                    "payment_weight": 0.10
                }

            component_scores = HealthScoreComponents(
                usage_score=usage_score,
                engagement_score=engagement_score,
                support_score=support_score,
                satisfaction_score=satisfaction_score,
                payment_score=payment_score,
                **weights
            )

            # Calculate weighted health score
            current_health_score = int(component_scores.calculate_weighted_score())

            # Determine health trend
            previous_score = mock.random_int(
                max(0, current_health_score - 15),
                min(100, current_health_score + 10)
            )
            score_change = current_health_score - previous_score

            if score_change > 3:
                health_trend = HealthTrend.IMPROVING
            elif score_change < -3:
                health_trend = HealthTrend.DECLINING
            else:
                health_trend = HealthTrend.STABLE

            # Generate historical scores
            historical_scores = []
            for i in range(lookback_period_days, 0, -max(1, lookback_period_days // 12)):
                days_ago = lookback_period_days - i
                base_score = current_health_score - (score_change * (days_ago / lookback_period_days))
                historical_scores.append({
                    "date": (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
                    "health_score": max(0, min(100, int(base_score + mock.random_int(-3, 3)))),
                    "trend": "improving" if i < lookback_period_days / 2 else "stable"
                })

            # Determine risk level
            if current_health_score >= 80:
                risk_level = "low"
            elif current_health_score >= 65:
                risk_level = "medium"
            elif current_health_score >= 50:
                risk_level = "high"
            else:
                risk_level = "critical"

            # Identify risk indicators
            risk_indicators = []

            if engagement_score < 70:
                risk_indicators.append(RiskIndicator(
                    indicator_id="risk_low_engagement",
                    indicator_name="Low Product Engagement",
                    category="engagement",
                    severity="high" if engagement_score < 60 else "medium",
                    current_value=engagement_score,
                    threshold_value=70.0,
                    description=f"Engagement score {engagement_score:.1f} below threshold of 70",
                    mitigation_actions=[
                        "Schedule check-in call with primary users",
                        "Provide targeted feature training",
                        "Launch engagement campaign with personalized content"
                    ]
                ))

            if usage_score < 75:
                risk_indicators.append(RiskIndicator(
                    indicator_id="risk_low_usage",
                    indicator_name="Below Expected Usage Levels",
                    category="usage",
                    severity="high" if usage_score < 65 else "medium",
                    current_value=usage_score,
                    threshold_value=75.0,
                    description=f"Usage score {usage_score:.1f} indicates underutilization",
                    mitigation_actions=[
                        "Review customer goals and use cases",
                        "Identify unused features with high value",
                        "Provide guided onboarding for key features"
                    ]
                ))

            if support_score < 80:
                risk_indicators.append(RiskIndicator(
                    indicator_id="risk_support_issues",
                    indicator_name="Support Experience Concerns",
                    category="support",
                    severity="medium",
                    current_value=support_score,
                    threshold_value=80.0,
                    description=f"Support score {support_score:.1f} indicates friction",
                    mitigation_actions=[
                        "Review recent support tickets and resolutions",
                        "Proactive check-in on outstanding issues",
                        "Provide additional documentation and resources"
                    ]
                ))

            if health_trend == HealthTrend.DECLINING:
                risk_indicators.append(RiskIndicator(
                    indicator_id="risk_declining_health",
                    indicator_name="Declining Health Trend",
                    category="engagement",
                    severity="high",
                    current_value=float(score_change),
                    threshold_value=0.0,
                    description=f"Health score decreased {abs(score_change)} points over {lookback_period_days} days",
                    mitigation_actions=[
                        "Immediate CSM intervention required",
                        "Schedule executive business review",
                        "Investigate root causes of decline"
                    ]
                ))

            # Generate churn prediction
            churn_probability = min(0.95, max(0.05, (100 - current_health_score) / 100 + mock.random_float(-0.15, 0.10)))

            if churn_probability < 0.25:
                churn_risk_level = "low"
            elif churn_probability < 0.50:
                churn_risk_level = "medium"
            elif churn_probability < 0.75:
                churn_risk_level = "high"
            else:
                churn_risk_level = "critical"

            churn_prediction = ChurnPrediction(
                client_id=client_id,
                churn_probability=churn_probability,
                churn_risk_level=churn_risk_level,
                confidence_score=mock.random_float(0.75, 0.95),
                contributing_factors=[
                    {"factor": "usage_decline", "weight": 0.35},
                    {"factor": "engagement_decrease", "weight": 0.28},
                    {"factor": "support_friction", "weight": 0.20},
                    {"factor": "satisfaction_decline", "weight": 0.17}
                ],
                risk_indicators=risk_indicators,
                predicted_churn_date=(datetime.now() + timedelta(days=mock.random_int(60, 180))).date() if churn_probability > 0.50 else None,
                retention_recommendations=[
                    "Increase CSM touchpoint frequency to weekly" if churn_probability > 0.60 else "Maintain regular CSM cadence",
                    "Address top support issues immediately" if support_score < 80 else "Continue proactive support",
                    "Launch targeted re-engagement campaign" if engagement_score < 70 else "Optimize engagement strategy",
                    "Executive business review to align on value" if churn_probability > 0.50 else "Regular QBR to showcase ROI"
                ]
            )

            # Generate predicted future scores
            predicted_scores = []
            if include_predictions:
                for weeks_ahead in range(1, 13):
                    prediction_date = datetime.now() + timedelta(weeks=weeks_ahead)
                    # Trend-based prediction with some uncertainty
                    if health_trend == HealthTrend.IMPROVING:
                        predicted_change = weeks_ahead * 0.5
                    elif health_trend == HealthTrend.DECLINING:
                        predicted_change = -weeks_ahead * 0.7
                    else:
                        predicted_change = 0

                    predicted_score = max(0, min(100, current_health_score + predicted_change + mock.random_int(-2, 2)))

                    predicted_scores.append({
                        "date": prediction_date.strftime("%Y-%m-%d"),
                        "predicted_score": int(predicted_score),
                        "confidence": mock.random_float(0.70, 0.90) - (weeks_ahead * 0.03),
                        "scenario": "baseline"
                    })

            # Contributing factors analysis
            contributing_factors = {
                "positive_factors": [],
                "negative_factors": [],
                "neutral_factors": []
            }

            for component, score in [
                ("usage", usage_score),
                ("engagement", engagement_score),
                ("support", support_score),
                ("satisfaction", satisfaction_score),
                ("payment", payment_score)
            ]:
                factor = {
                    "component": component,
                    "score": score,
                    "weight": weights.get(f"{component}_weight", 0.10),
                    "contribution": score * weights.get(f"{component}_weight", 0.10)
                }

                if score >= 80:
                    contributing_factors["positive_factors"].append(factor)
                elif score < 70:
                    contributing_factors["negative_factors"].append(factor)
                else:
                    contributing_factors["neutral_factors"].append(factor)

            # Improvement opportunities
            improvement_opportunities = []

            sorted_components = sorted(
                [
                    ("usage", usage_score, "Increase product usage and feature adoption"),
                    ("engagement", engagement_score, "Improve user engagement and activity levels"),
                    ("support", support_score, "Enhance support experience and resolution quality"),
                    ("satisfaction", satisfaction_score, "Boost customer satisfaction through value delivery"),
                    ("payment", payment_score, "Ensure payment health and contract compliance")
                ],
                key=lambda x: x[1]
            )

            for component, score, description in sorted_components[:3]:
                if score < 85:
                    potential_impact = (85 - score) * weights.get(f"{component}_weight", 0.10)
                    improvement_opportunities.append({
                        "component": component,
                        "current_score": score,
                        "target_score": 85,
                        "potential_health_impact": round(potential_impact, 1),
                        "description": description,
                        "priority": "high" if score < 70 else "medium"
                    })

            # Generate automated alerts
            automated_alerts = []

            if current_health_score < risk_threshold:
                automated_alerts.append({
                    "alert_type": "health_below_threshold",
                    "severity": "high" if current_health_score < 50 else "medium",
                    "message": f"Health score {current_health_score} below threshold of {risk_threshold}",
                    "triggered_at": datetime.now().isoformat(),
                    "action_required": True
                })

            if health_trend == HealthTrend.DECLINING:
                automated_alerts.append({
                    "alert_type": "declining_health_trend",
                    "severity": "high",
                    "message": f"Health declining: {abs(score_change)} point decrease over {lookback_period_days} days",
                    "triggered_at": datetime.now().isoformat(),
                    "action_required": True
                })

            if churn_probability > 0.60:
                automated_alerts.append({
                    "alert_type": "high_churn_risk",
                    "severity": "critical",
                    "message": f"Churn probability {churn_probability:.1%} - immediate intervention required",
                    "triggered_at": datetime.now().isoformat(),
                    "action_required": True
                })

            if len(risk_indicators) >= 3:
                automated_alerts.append({
                    "alert_type": "multiple_risk_indicators",
                    "severity": "high",
                    "message": f"{len(risk_indicators)} risk indicators detected requiring attention",
                    "triggered_at": datetime.now().isoformat(),
                    "action_required": True
                })

            # Recommended actions
            recommended_actions = []

            if current_health_score < 70:
                recommended_actions.append("URGENT: Schedule immediate check-in call with customer stakeholders")
                recommended_actions.append("Conduct root cause analysis of health decline with cross-functional team")

            if len(risk_indicators) > 0:
                recommended_actions.append(f"Address {len(risk_indicators)} identified risk indicators with targeted interventions")

            if churn_probability > 0.50:
                recommended_actions.append("Escalate to senior leadership for executive engagement and retention strategy")

            for opp in improvement_opportunities[:2]:
                if opp["potential_health_impact"] > 5:
                    recommended_actions.append(f"Focus on improving {opp['component']} score (potential +{opp['potential_health_impact']:.1f} impact)")

            if health_trend == HealthTrend.IMPROVING:
                recommended_actions.append("Maintain successful strategies - health trending positively")
                recommended_actions.append("Identify expansion opportunities given improving engagement")

            # Generate comprehensive health metrics
            health_metrics = HealthMetrics(
                client_id=client_id,
                period_start=datetime.now() - timedelta(days=lookback_period_days),
                period_end=datetime.now(),
                overall_health_score=current_health_score,
                health_score_trend=TrendDirection.UP if health_trend == HealthTrend.IMPROVING else (
                    TrendDirection.DOWN if health_trend == HealthTrend.DECLINING else TrendDirection.FLAT
                ),
                health_score_change=score_change,
                health_components={
                    "usage_score": usage_score,
                    "engagement_score": engagement_score,
                    "support_score": support_score,
                    "satisfaction_score": satisfaction_score,
                    "payment_score": payment_score
                },
                component_trends={
                    "usage_score": "up" if usage_score > 75 else "flat",
                    "engagement_score": "up" if engagement_score > 70 else ("down" if engagement_score < 60 else "flat"),
                    "support_score": "flat",
                    "satisfaction_score": "up" if satisfaction_score > 80 else "flat",
                    "payment_score": "flat"
                },
                risk_indicators=[
                    {
                        "indicator": ri.indicator_name,
                        "severity": ri.severity,
                        "detected_date": ri.detected_at.strftime("%Y-%m-%d")
                    }
                    for ri in risk_indicators
                ],
                positive_indicators=[
                    {
                        "indicator": f"strong_{component}",
                        "strength": "strong",
                        "detected_date": datetime.now().strftime("%Y-%m-%d")
                    }
                    for component, score in [("usage", usage_score), ("engagement", engagement_score), ("satisfaction", satisfaction_score)]
                    if score >= 85
                ],
                benchmark_comparison={
                    "overall_health": "above" if current_health_score > 75 else "below",
                    "vs_tier_average": current_health_score - 70,
                    "vs_industry_average": current_health_score - 72,
                    "percentile": min(95, max(10, current_health_score - 20))
                },
                predicted_next_period_score=predicted_scores[3]["predicted_score"] if predicted_scores else None,
                confidence=predicted_scores[3]["confidence"] if predicted_scores else 0.0
            )

            # Construct results
            results = HealthScoreResults(
                client_id=client_id,
                current_health_score=current_health_score,
                health_trend=health_trend,
                score_change=score_change,
                component_scores=component_scores,
                health_metrics=health_metrics,
                risk_level=risk_level,
                risk_indicators=risk_indicators,
                churn_prediction=churn_prediction,
                historical_scores=historical_scores,
                predicted_scores=predicted_scores,
                contributing_factors=contributing_factors,
                improvement_opportunities=improvement_opportunities,
                automated_alerts=automated_alerts,
                recommended_actions=recommended_actions
            )

            ctx.info(f"Successfully calculated health score for {client_id}: {current_health_score} ({risk_level} risk)")
            return results.model_dump_json(indent=2)

        except ValidationError as e:
            ctx.error(f"Validation error in calculate_health_score: {str(e)}")
            raise
        except Exception as e:
            ctx.error(f"Error in calculate_health_score: {str(e)}")
            raise


    # ============================================================================
    # Tool 3: Segment Customers (Process 89)
    # ============================================================================


    @mcp.tool()
    def segment_customers(
        ctx: Context,
        segmentation_type: str,
        criteria: Dict[str, Any],
        min_segment_size: int = 5,
        include_recommendations: bool = True,
        benchmark_analysis: bool = True
    ) -> str:
        """
        Perform value-based customer segmentation for targeted engagement strategies.

        This powerful segmentation engine enables sophisticated customer grouping based on
        multiple dimensions including value, usage, health, industry, lifecycle, and custom
        criteria. It provides detailed segment profiles, performance metrics, and tailored
        engagement recommendations to optimize customer success resources.

        Key Capabilities:
        - Multi-dimensional segmentation (value, usage, health, industry, lifecycle, custom)
        - Dynamic segment creation based on configurable criteria
        - Comprehensive segment profiling and characteristics
        - Performance benchmarking across segments
        - Cross-segment comparative analysis
        - Segment-specific engagement strategy recommendations
        - Resource allocation optimization
        - Segment migration tracking and analysis

        Args:
            ctx: MCP context for logging and operations
            segmentation_type: Type of segmentation - "value_based", "usage_based",
                              "health_based", "industry", "lifecycle", or "custom"
            criteria: Segmentation criteria and rules (structure varies by type)
            min_segment_size: Minimum customers per segment (default: 5)
            include_recommendations: Include segment-specific engagement recommendations
            benchmark_analysis: Include benchmark analysis per segment

        Returns:
            JSON string containing comprehensive segmentation results with:
            - Detailed segment definitions and metrics
            - Customer distribution across segments
            - Segment characteristics and performance
            - Cross-segment analysis and insights
            - Engagement strategies per segment
            - Resource allocation recommendations
            - Migration patterns and opportunities

        Raises:
            ValidationError: If segmentation_type is invalid or criteria is malformed

        Example:
            >>> result = segment_customers(
            ...     ctx,
            ...     segmentation_type="value_based",
            ...     criteria={
            ...         "dimensions": ["arr", "ltv", "expansion_potential"],
            ...         "tier_boundaries": {"vip": 100000, "strategic": 50000, "growth": 25000}
            ...     }
            ... )

        MCP Process: 89 - Value-Based Customer Segmentation
        """
        try:
            # Validate segmentation_type
            valid_types = ["value_based", "usage_based", "health_based", "industry", "lifecycle", "custom"]
            if segmentation_type not in valid_types:
                raise ValidationError(f"segmentation_type must be one of: {', '.join(valid_types)}")

            if min_segment_size < 1:
                raise ValidationError("min_segment_size must be at least 1")

            ctx.info(f"Performing {segmentation_type} customer segmentation")

            # Generate segmentation results based on type
            if segmentation_type == "value_based":
                segments = _generate_value_segments(criteria, min_segment_size)
            elif segmentation_type == "usage_based":
                segments = _generate_usage_segments(criteria, min_segment_size)
            elif segmentation_type == "health_based":
                segments = _generate_health_segments(criteria, min_segment_size)
            elif segmentation_type == "industry":
                segments = _generate_industry_segments(criteria, min_segment_size)
            elif segmentation_type == "lifecycle":
                segments = _generate_lifecycle_segments(criteria, min_segment_size)
            else:  # custom
                segments = _generate_custom_segments(criteria, min_segment_size)

            # Calculate overall statistics
            total_customers = sum(seg.customer_count for seg in segments)
            total_arr = sum(seg.total_arr for seg in segments)

            # Segment distribution
            segment_distribution = {
                "by_count": {seg.segment_name: seg.customer_count for seg in segments},
                "by_arr": {seg.segment_name: seg.total_arr for seg in segments},
                "by_percentage": {
                    seg.segment_name: round((seg.customer_count / total_customers * 100), 1)
                    for seg in segments
                }
            }

            # Segment characteristics
            segment_characteristics = {}
            for seg in segments:
                segment_characteristics[seg.segment_name] = {
                    "typical_profile": seg.characteristics,
                    "defining_traits": list(seg.criteria.values())[:3],
                    "avg_arr": seg.total_arr / seg.customer_count if seg.customer_count > 0 else 0,
                    "avg_health": seg.avg_health_score,
                    "segment_maturity": mock.random_choice(["emerging", "established", "mature"])
                }

            # Segment performance metrics
            segment_performance = {}
            for seg in segments:
                segment_performance[seg.segment_name] = {
                    "health_score": seg.avg_health_score,
                    "retention_rate": mock.random_float(0.80, 0.98),
                    "nps": mock.random_int(30, 75),
                    "expansion_rate": mock.random_float(0.10, 0.40),
                    "engagement_score": mock.random_float(65.0, 92.0),
                    "ltv": seg.total_arr / seg.customer_count * mock.random_float(2.5, 5.0) if seg.customer_count > 0 else 0
                }

            # Cross-segment analysis
            cross_segment_analysis = {
                "concentration_analysis": {
                    "top_segment_by_count": max(segments, key=lambda s: s.customer_count).segment_name,
                    "top_segment_by_arr": max(segments, key=lambda s: s.total_arr).segment_name,
                    "pareto_principle": _calculate_pareto(segments),
                },
                "performance_spread": {
                    "health_range": {
                        "min": min(seg.avg_health_score for seg in segments),
                        "max": max(seg.avg_health_score for seg in segments),
                        "spread": max(seg.avg_health_score for seg in segments) - min(seg.avg_health_score for seg in segments)
                    },
                    "arr_range": {
                        "min": min(seg.total_arr for seg in segments),
                        "max": max(seg.total_arr for seg in segments)
                    }
                },
                "segment_correlations": {
                    "health_value_correlation": mock.random_float(0.45, 0.75),
                    "size_engagement_correlation": mock.random_float(0.30, 0.60)
                }
            }

            # Engagement strategies per segment
            engagement_strategies = {}
            for seg in segments:
                engagement_strategies[seg.segment_name] = {
                    "recommended_csm_model": seg.engagement_strategy.get("csm_touch_frequency", "monthly"),
                    "communication_channels": _recommend_channels(seg),
                    "content_strategy": _recommend_content(seg, segmentation_type),
                    "success_programs": seg.engagement_strategy.get("success_programs", []),
                    "automation_level": _recommend_automation(seg),
                    "escalation_criteria": _define_escalation_criteria(seg)
                }

            # Resource allocation recommendations
            resource_allocation = {
                "csm_allocation": {},
                "budget_allocation": {},
                "priority_ranking": []
            }

            # Sort segments by strategic importance (ARR * health score)
            segments_by_priority = sorted(
                segments,
                key=lambda s: (s.total_arr * (s.avg_health_score / 100)) if s.customer_count > 0 else 0,
                reverse=True
            )

            for i, seg in enumerate(segments_by_priority):
                resource_allocation["csm_allocation"][seg.segment_name] = {
                    "recommended_fte": round(seg.customer_count / 30, 1),  # Assume 30:1 ratio baseline
                    "csm_skill_level": "senior" if i < 2 else ("mid" if i < 4 else "junior"),
                    "support_tier": "premium" if i < 2 else "standard"
                }

                arr_percentage = (seg.total_arr / total_arr * 100) if total_arr > 0 else 0
                resource_allocation["budget_allocation"][seg.segment_name] = {
                    "percentage": round(arr_percentage, 1),
                    "focus_areas": ["retention", "expansion"] if i < 2 else ["efficiency", "automation"]
                }

                resource_allocation["priority_ranking"].append({
                    "rank": i + 1,
                    "segment": seg.segment_name,
                    "priority_score": round((s.total_arr * (seg.avg_health_score / 100)) / 1000, 2),
                    "rationale": f"Represents {arr_percentage:.1f}% of ARR with {seg.avg_health_score:.0f} health score"
                })

            # Segment migration analysis
            segment_migration = {
                "migration_patterns": [
                    {
                        "from_segment": seg.segment_name,
                        "to_segment": mock.random_choice([s.segment_name for s in segments if s.segment_id != seg.segment_id]),
                        "migration_rate": mock.random_float(0.05, 0.20),
                        "common_triggers": ["contract_expansion", "usage_increase", "feature_adoption"]
                    }
                    for seg in segments[:min(3, len(segments))]
                ],
                "upgrade_opportunities": mock.random_int(5, 20),
                "downgrade_risks": mock.random_int(2, 10),
                "migration_velocity": "moderate"
            }

            # Strategic recommendations
            recommendations = []

            # Highest value segment
            top_segment = max(segments, key=lambda s: s.total_arr)
            recommendations.append(
                f"Prioritize '{top_segment.segment_name}' segment - represents "
                f"${top_segment.total_arr:,.0f} ARR ({top_segment.total_arr / total_arr * 100:.1f}% of total)"
            )

            # Segment with lowest health
            lowest_health_segment = min(segments, key=lambda s: s.avg_health_score)
            if lowest_health_segment.avg_health_score < 70:
                recommendations.append(
                    f"Intervention required for '{lowest_health_segment.segment_name}' segment - "
                    f"average health score {lowest_health_segment.avg_health_score:.0f}"
                )

            # Segment-specific opportunities
            for seg in segments:
                if seg.customer_count >= min_segment_size * 2:
                    recommendations.append(
                        f"Consider sub-segmentation of '{seg.segment_name}' ({seg.customer_count} customers) "
                        f"for more targeted engagement"
                    )

            if include_recommendations:
                recommendations.append("Implement segment-specific playbooks based on engagement strategies")
                recommendations.append("Monitor segment migration patterns for early expansion/churn signals")
                recommendations.append("Align CSM specialization with high-value segment needs")

            # Construct results
            results = SegmentationResults(
                segmentation_id=f"seg_{int(datetime.now().timestamp())}_{segmentation_type}",
                segmentation_type=segmentation_type,
                total_customers_analyzed=total_customers,
                segments_created=len(segments),
                segments=segments,
                segment_distribution=segment_distribution,
                segment_characteristics=segment_characteristics,
                segment_performance=segment_performance,
                cross_segment_analysis=cross_segment_analysis,
                engagement_strategies=engagement_strategies,
                resource_allocation=resource_allocation,
                segment_migration=segment_migration,
                recommendations=recommendations
            )

            ctx.info(f"Successfully segmented {total_customers} customers into {len(segments)} segments")
            return results.model_dump_json(indent=2)

        except ValidationError as e:
            ctx.error(f"Validation error in segment_customers: {str(e)}")
            raise
        except Exception as e:
            ctx.error(f"Error in segment_customers: {str(e)}")
            raise


    # Helper functions for segmentation

    @mcp.tool()
    def track_feature_adoption(
        ctx: Context,
        client_id: Optional[str] = None,
        feature_id: Optional[str] = None,
        time_period_days: int = 90,
        adoption_threshold: float = 0.20,
        include_user_personas: bool = True,
        optimization_recommendations: bool = True
    ) -> str:
        """
        Track feature adoption and optimize feature utilization across customers.

        This comprehensive feature adoption tracking system provides deep insights into which
        features are being adopted, by whom, at what velocity, and identifies opportunities
        to increase utilization. It enables product and CS teams to optimize feature rollouts,
        identify adoption barriers, and drive product value realization.

        Key Capabilities:
        - Feature-level adoption metrics and trends
        - Adoption velocity and time-to-value analysis
        - User persona-based adoption patterns
        - Tier and lifecycle stage adoption segmentation
        - Feature stickiness and retention metrics
        - Identification of high-value vs. underutilized features
        - Adoption barrier analysis with mitigation strategies
        - Success factor identification for fast adopters
        - Optimization recommendations to increase adoption

        Args:
            ctx: MCP context for logging and operations
            client_id: Specific customer to analyze (None for all customers)
            feature_id: Specific feature to track (None for all features)
            time_period_days: Analysis time period in days (1-365)
            adoption_threshold: Adoption rate threshold (0-1) for classification
            include_user_personas: Include adoption analysis by user persona/role
            optimization_recommendations: Include optimization recommendations

        Returns:
            JSON string containing comprehensive feature adoption analysis with:
            - Overall adoption rates and metrics
            - Feature-by-feature adoption breakdown
            - Adoption by tier, lifecycle, and persona
            - Adoption velocity and patterns
            - High-value and underutilized features
            - Adoption barriers and success factors
            - Optimization opportunities and recommendations

        Raises:
            ValidationError: If parameters are out of range or invalid

        Example:
            >>> result = track_feature_adoption(
            ...     ctx,
            ...     client_id=None,  # All customers
            ...     feature_id=None,  # All features
            ...     time_period_days=90,
            ...     adoption_threshold=0.25
            ... )

        MCP Process: 90 - Feature Adoption Tracking
        """
        try:
            # Validate parameters
            if time_period_days < 1 or time_period_days > 365:
                raise ValidationError("time_period_days must be between 1 and 365")

            if adoption_threshold < 0 or adoption_threshold > 1:
                raise ValidationError("adoption_threshold must be between 0 and 1")

            if client_id:
                validate_client_id(client_id)
                scope_description = f"customer {client_id}"
            elif feature_id:
                scope_description = f"feature {feature_id}"
            else:
                scope_description = "all customers and features"

            ctx.info(f"Tracking feature adoption for {scope_description} over {time_period_days} days")

            # Define scope
            scope = {
                "client_id": client_id,
                "feature_id": feature_id,
                "time_period_days": time_period_days,
                "period_start": (datetime.now() - timedelta(days=time_period_days)).strftime("%Y-%m-%d"),
                "period_end": datetime.now().strftime("%Y-%m-%d"),
                "customers_in_scope": 1 if client_id else mock.random_int(50, 200),
                "features_in_scope": 1 if feature_id else mock.random_int(40, 80)
            }

            # Calculate overall adoption rate
            overall_adoption_rate = mock.random_float(0.45, 0.85)

            # Generate feature adoption breakdown
            feature_categories = ["core", "advanced", "integration", "analytics", "collaboration"]
            features = []

            num_features = 1 if feature_id else mock.random_int(15, 30)

            for i in range(num_features):
                feature_name = feature_id or f"feature_{i+1}"
                category = mock.random_choice(feature_categories)
                adoption_rate = mock.random_float(0.10, 0.95)

                # Core features have higher adoption
                if category == "core":
                    adoption_rate = mock.random_float(0.70, 0.98)
                elif category == "advanced":
                    adoption_rate = mock.random_float(0.30, 0.70)

                features.append({
                    "feature_id": f"feat_{i+1}",
                    "feature_name": feature_name,
                    "category": category,
                    "adoption_rate": adoption_rate,
                    "active_users": int(scope["customers_in_scope"] * adoption_rate) if not client_id else mock.random_int(10, 80),
                    "total_usage_events": mock.random_int(500, 10000),
                    "avg_usage_per_adopter": mock.random_float(5.0, 50.0),
                    "first_use_to_regular_use_days": mock.random_int(3, 30),
                    "adoption_trend": mock.random_choice(["increasing", "stable", "decreasing"]),
                    "launched_date": (datetime.now() - timedelta(days=mock.random_int(30, 730))).strftime("%Y-%m-%d"),
                    "adoption_classification": (
                        "high" if adoption_rate >= adoption_threshold * 2 else
                        ("moderate" if adoption_rate >= adoption_threshold else "low")
                    )
                })

            feature_adoption_breakdown = sorted(features, key=lambda x: x["adoption_rate"], reverse=True)

            # Adoption by tier
            tiers = ["enterprise", "professional", "standard", "starter"]
            adoption_by_tier = {}

            for tier in tiers:
                tier_adoption_rate = overall_adoption_rate * mock.random_float(0.85, 1.25)
                tier_adoption_rate = min(1.0, tier_adoption_rate)

                adoption_by_tier[tier] = {
                    "overall_adoption_rate": tier_adoption_rate,
                    "customer_count": mock.random_int(10, 50),
                    "top_features": [f["feature_name"] for f in features[:3]],
                    "avg_features_adopted": mock.random_int(15, 45),
                    "adoption_velocity": mock.random_float(0.5, 2.5)  # features per week
                }

            # Adoption by lifecycle stage
            lifecycle_stages = ["onboarding", "active", "expansion", "renewal"]
            adoption_by_lifecycle = {}

            for stage in lifecycle_stages:
                stage_multiplier = {
                    "onboarding": 0.6,
                    "active": 1.1,
                    "expansion": 1.3,
                    "renewal": 0.9
                }.get(stage, 1.0)

                stage_adoption = overall_adoption_rate * stage_multiplier
                stage_adoption = min(1.0, stage_adoption)

                adoption_by_lifecycle[stage] = {
                    "overall_adoption_rate": stage_adoption,
                    "customer_count": mock.random_int(10, 60),
                    "avg_features_adopted": int(len(features) * stage_adoption),
                    "typical_adoption_pattern": _get_stage_adoption_pattern(stage),
                    "key_features": [f["feature_name"] for f in features[:5] if mock.random_choice([True, False])]
                }

            # Adoption velocity (speed of adoption over time)
            adoption_velocity = {
                "overall_velocity": mock.random_float(0.8, 2.5),  # features adopted per week
                "velocity_by_tier": {
                    tier: mock.random_float(0.5, 3.0) for tier in tiers
                },
                "velocity_trend": mock.random_choice(["accelerating", "stable", "decelerating"]),
                "time_to_first_adoption": {
                    "avg_days": mock.random_int(3, 14),
                    "median_days": mock.random_int(2, 10),
                    "p90_days": mock.random_int(7, 21)
                },
                "time_to_proficiency": {
                    "avg_days": mock.random_int(14, 45),
                    "median_days": mock.random_int(10, 30),
                    "p90_days": mock.random_int(30, 60)
                }
            }

            # Adoption patterns
            adoption_patterns = {
                "sequential_adoption": {
                    "detected": True,
                    "typical_sequence": ["core_feature_1", "core_feature_2", "advanced_feature_1"],
                    "completion_rate": mock.random_float(0.60, 0.85)
                },
                "parallel_adoption": {
                    "detected": True,
                    "common_pairs": [
                        ["dashboard", "reports"],
                        ["collaboration", "notifications"],
                        ["api", "integrations"]
                    ]
                },
                "seasonal_patterns": {
                    "detected": False,
                    "peak_months": []
                },
                "cohort_differences": {
                    "newer_cohorts_faster": mock.random_choice([True, False]),
                    "adoption_delta": mock.random_float(-0.15, 0.25)
                }
            }

            # High-value features (high adoption + high correlation with success)
            high_value_features = [
                {
                    "feature": f["feature_name"],
                    "adoption_rate": f["adoption_rate"],
                    "correlation_with_retention": mock.random_float(0.60, 0.90),
                    "correlation_with_expansion": mock.random_float(0.45, 0.80),
                    "value_score": f["adoption_rate"] * mock.random_float(0.70, 0.95),
                    "recommendation": "Continue promoting and expanding"
                }
                for f in features[:5] if f["adoption_rate"] > 0.70
            ]

            # Underutilized features (low adoption despite high potential value)
            underutilized_features = [
                {
                    "feature": f["feature_name"],
                    "adoption_rate": f["adoption_rate"],
                    "potential_value": mock.random_float(0.70, 0.95),
                    "adoption_gap": mock.random_float(0.30, 0.60),
                    "primary_barrier": mock.random_choice([
                        "Lack of awareness",
                        "Complexity/learning curve",
                        "Unclear value proposition",
                        "Technical barriers"
                    ]),
                    "recommendation": f"Launch targeted campaign to increase adoption from {f['adoption_rate']:.1%}"
                }
                for f in features if f["adoption_rate"] < adoption_threshold
            ][:5]

            # Feature stickiness (continued usage after initial adoption)
            feature_stickiness = {}
            for f in features[:10]:
                feature_stickiness[f["feature_name"]] = mock.random_float(0.65, 0.95)

            # Adoption barriers
            adoption_barriers = [
                {
                    "barrier_type": "awareness",
                    "affected_features": [f["feature_name"] for f in underutilized_features[:3]],
                    "impact": "high",
                    "affected_customers_pct": mock.random_float(0.30, 0.60),
                    "mitigation": "Increase in-app messaging and feature highlights"
                },
                {
                    "barrier_type": "complexity",
                    "affected_features": [f["feature_name"] for f in features if f["category"] == "advanced"][:2],
                    "impact": "medium",
                    "affected_customers_pct": mock.random_float(0.20, 0.45),
                    "mitigation": "Create guided tutorials and simplify UX"
                },
                {
                    "barrier_type": "value_unclear",
                    "affected_features": [f["feature_name"] for f in underutilized_features[2:4]],
                    "impact": "medium",
                    "affected_customers_pct": mock.random_float(0.25, 0.50),
                    "mitigation": "Develop clear use cases and ROI messaging"
                }
            ]

            # Success factors (characteristics of fast/successful adopters)
            success_factors = [
                {
                    "factor": "strong_onboarding_engagement",
                    "correlation": mock.random_float(0.70, 0.90),
                    "description": "Customers who complete onboarding adopt 2.3x more features",
                    "actionable_insight": "Improve onboarding completion rates"
                },
                {
                    "factor": "executive_sponsorship",
                    "correlation": mock.random_float(0.60, 0.85),
                    "description": "Executive involvement increases adoption velocity by 40%",
                    "actionable_insight": "Engage executives early in customer journey"
                },
                {
                    "factor": "csm_proactive_guidance",
                    "correlation": mock.random_float(0.55, 0.80),
                    "description": "Regular CSM feature walkthroughs drive adoption",
                    "actionable_insight": "Implement feature showcase in CSM playbooks"
                },
                {
                    "factor": "peer_network_effects",
                    "correlation": mock.random_float(0.50, 0.75),
                    "description": "Customers in peer groups adopt features 30% faster",
                    "actionable_insight": "Foster customer communities and peer learning"
                }
            ]

            # Optimization opportunities
            optimization_opportunities = []

            if len(underutilized_features) > 0:
                optimization_opportunities.append({
                    "opportunity_type": "increase_underutilized_adoption",
                    "priority": "high",
                    "potential_impact": f"+{mock.random_int(15, 40)}% overall adoption",
                    "features_affected": len(underutilized_features),
                    "recommended_actions": [
                        "Launch targeted feature awareness campaign",
                        "Create compelling use case documentation",
                        "Add in-app contextual prompts",
                        "Include in CSM playbooks"
                    ],
                    "estimated_effort": "medium",
                    "timeline": "30-60 days"
                })

            if adoption_velocity["velocity_trend"] == "decelerating":
                optimization_opportunities.append({
                    "opportunity_type": "accelerate_adoption_velocity",
                    "priority": "high",
                    "potential_impact": "+1.5 features/week adoption velocity",
                    "recommended_actions": [
                        "Simplify feature onboarding flows",
                        "Implement progressive disclosure",
                        "Add feature success metrics dashboard",
                        "Gamify feature discovery"
                    ],
                    "estimated_effort": "high",
                    "timeline": "60-90 days"
                })

            # Compare adoption across customer segments
            if overall_adoption_rate < 0.60:
                optimization_opportunities.append({
                    "opportunity_type": "improve_overall_adoption",
                    "priority": "critical",
                    "potential_impact": f"Increase from {overall_adoption_rate:.1%} to 70%+",
                    "recommended_actions": [
                        "Conduct user research on adoption barriers",
                        "Redesign feature discovery experience",
                        "Implement adaptive feature recommendations",
                        "Create role-based feature pathways"
                    ],
                    "estimated_effort": "high",
                    "timeline": "90-120 days"
                })

            # Recommended actions
            recommended_actions = []

            if optimization_recommendations:
                recommended_actions.append("Prioritize increasing adoption of high-value, underutilized features")

                if len(adoption_barriers) > 0:
                    recommended_actions.append(f"Address top {min(3, len(adoption_barriers))} adoption barriers through targeted interventions")

                recommended_actions.append("Replicate success factors from fast-adopting customers across customer base")

                if feature_id:
                    feature_data = features[0] if features else None
                    if feature_data and feature_data["adoption_rate"] < 0.50:
                        recommended_actions.append(f"Launch focused campaign to double '{feature_data['feature_name']}' adoption")

                recommended_actions.append("Implement adoption milestone celebrations to drive engagement")
                recommended_actions.append("Integrate feature adoption metrics into health scoring")

            # Construct results
            results = FeatureAdoptionResults(
                analysis_id=f"adopt_{int(datetime.now().timestamp())}",
                scope=scope,
                overall_adoption_rate=overall_adoption_rate,
                feature_adoption_breakdown=feature_adoption_breakdown,
                adoption_by_tier=adoption_by_tier,
                adoption_by_lifecycle=adoption_by_lifecycle,
                adoption_velocity=adoption_velocity,
                adoption_patterns=adoption_patterns,
                high_value_features=high_value_features,
                underutilized_features=underutilized_features,
                feature_stickiness=feature_stickiness,
                adoption_barriers=adoption_barriers,
                success_factors=success_factors,
                optimization_opportunities=optimization_opportunities,
                recommended_actions=recommended_actions
            )

            ctx.info(f"Successfully tracked feature adoption: {overall_adoption_rate:.1%} overall rate across {len(features)} features")
            return results.model_dump_json(indent=2)

        except ValidationError as e:
            ctx.error(f"Validation error in track_feature_adoption: {str(e)}")
            raise
        except Exception as e:
            ctx.error(f"Error in track_feature_adoption: {str(e)}")
            raise



    @mcp.tool()
    def manage_lifecycle_stages(
        ctx: Context,
        client_id: Optional[str] = None,
        current_stage: Optional[str] = None,
        include_transitions: bool = True,
        intervention_planning: bool = True,
        automation_rules: bool = True
    ) -> str:
        """
        Manage customer lifecycle stages with automated interventions and playbooks.

        This comprehensive lifecycle management system tracks customers across their journey,
        identifies transition opportunities and risks, and provides stage-specific playbooks
        and interventions. It enables CSMs to deliver the right engagement at the right time
        based on where customers are in their lifecycle.

        Key Capabilities:
        - Real-time lifecycle stage tracking and classification
        - Historical stage transition analysis and patterns
        - Trigger identification for stage movements
        - Average duration analysis per stage
        - Stage-specific success metrics and benchmarks
        - At-risk transition detection (e.g., active to at-risk)
        - Expansion opportunity identification
        - Stage-specific intervention playbooks
        - Automated workflow recommendations
        - Stage optimization strategies

        Args:
            ctx: MCP context for logging and operations
            client_id: Specific customer to analyze (None for all customers)
            current_stage: Filter by lifecycle stage - "onboarding", "active", "at_risk",
                          "expansion", "renewal", or None for all
            include_transitions: Include historical transition analysis
            intervention_planning: Include intervention recommendations
            automation_rules: Include automated workflow rules

        Returns:
            JSON string containing comprehensive lifecycle management data with:
            - Customer distribution across lifecycle stages
            - Stage characteristics and metrics
            - Transition patterns and triggers
            - At-risk and expansion opportunities
            - Intervention playbooks by stage
            - Automated workflow recommendations
            - Prioritized action items

        Raises:
            ValidationError: If client_id is invalid or current_stage is unrecognized

        Example:
            >>> result = manage_lifecycle_stages(
            ...     ctx,
            ...     client_id=None,
            ...     current_stage="at_risk",
            ...     intervention_planning=True
            ... )

        MCP Process: 91 - Lifecycle Stage Management
        """
        try:
            # Validate inputs
            if client_id:
                validate_client_id(client_id)

            valid_stages = ["onboarding", "active", "at_risk", "expansion", "renewal", "churned"]
            if current_stage and current_stage not in valid_stages:
                raise ValidationError(f"current_stage must be one of: {', '.join(valid_stages)}")

            scope = "all customers" if not client_id else f"customer {client_id}"
            stage_filter = f" in {current_stage} stage" if current_stage else ""
            ctx.info(f"Managing lifecycle stages for {scope}{stage_filter}")

            # Generate stage distribution
            total_customers = 1 if client_id else mock.random_int(100, 300)

            if current_stage:
                stage_distribution = {current_stage: total_customers}
            else:
                stage_distribution = {
                    "onboarding": mock.random_int(15, 35),
                    "active": mock.random_int(120, 200),
                    "at_risk": mock.random_int(8, 25),
                    "expansion": mock.random_int(10, 30),
                    "renewal": mock.random_int(20, 50)
                }
                total_customers = sum(stage_distribution.values())

            # Stage characteristics and metrics
            stage_characteristics = {}

            for stage in (["onboarding", "active", "at_risk", "expansion", "renewal"] if not current_stage else [current_stage]):
                if stage == "onboarding":
                    characteristics = {
                        "definition": "New customers in first 90 days post-sale",
                        "typical_duration_days": mock.random_int(30, 90),
                        "avg_health_score": mock.random_float(60, 75),
                        "key_activities": ["kickoff", "training", "configuration", "first_value_milestone"],
                        "success_criteria": ["90% feature adoption", "primary use case activated", "user training complete"],
                        "common_challenges": ["slow activation", "change management", "technical setup issues"],
                        "resource_intensity": "high"
                    }
                elif stage == "active":
                    characteristics = {
                        "definition": "Healthy, engaged customers post-onboarding",
                        "typical_duration_days": mock.random_int(180, 1095),
                        "avg_health_score": mock.random_float(75, 88),
                        "key_activities": ["regular_check_ins", "qbrs", "feature_adoption", "value_realization"],
                        "success_criteria": ["consistent usage", "high satisfaction", "renewal on track"],
                        "common_challenges": ["maintaining engagement", "evolving needs", "competitive pressures"],
                        "resource_intensity": "medium"
                    }
                elif stage == "at_risk":
                    characteristics = {
                        "definition": "Customers showing churn indicators",
                        "typical_duration_days": mock.random_int(14, 60),
                        "avg_health_score": mock.random_float(30, 55),
                        "key_activities": ["intervention_calls", "executive_escalation", "recovery_plan", "win_back"],
                        "success_criteria": ["stabilize health score", "address root causes", "recommit to success"],
                        "common_challenges": ["lack of engagement", "unresolved issues", "lost executive sponsor"],
                        "resource_intensity": "very_high"
                    }
                elif stage == "expansion":
                    characteristics = {
                        "definition": "Customers ready for upsell/cross-sell",
                        "typical_duration_days": mock.random_int(30, 120),
                        "avg_health_score": mock.random_float(80, 95),
                        "key_activities": ["opportunity_qualification", "expansion_proposal", "negotiation", "deployment"],
                        "success_criteria": ["expansion closed", "smooth deployment", "value demonstration"],
                        "common_challenges": ["timing", "budget constraints", "stakeholder alignment"],
                        "resource_intensity": "medium"
                    }
                else:  # renewal
                    characteristics = {
                        "definition": "Customers approaching contract renewal",
                        "typical_duration_days": mock.random_int(60, 180),
                        "avg_health_score": mock.random_float(70, 90),
                        "key_activities": ["renewal_discussion", "value_review", "contract_negotiation", "commitment"],
                        "success_criteria": ["renewal secured", "no downsell", "on-time renewal"],
                        "common_challenges": ["budget scrutiny", "competitive evaluation", "changing requirements"],
                        "resource_intensity": "high"
                    }

                stage_characteristics[stage] = characteristics

            # Stage transitions (if requested)
            stage_transitions = {}
            if include_transitions:
                stage_transitions = {
                    "transition_matrix": {
                        "onboarding_to_active": {"count": mock.random_int(20, 50), "avg_days": mock.random_int(45, 90), "success_rate": mock.random_float(0.85, 0.95)},
                        "onboarding_to_at_risk": {"count": mock.random_int(2, 8), "avg_days": mock.random_int(20, 60), "success_rate": 0.0},
                        "active_to_expansion": {"count": mock.random_int(10, 30), "avg_days": mock.random_int(120, 365), "success_rate": mock.random_float(0.70, 0.90)},
                        "active_to_renewal": {"count": mock.random_int(15, 40), "avg_days": mock.random_int(300, 400), "success_rate": mock.random_float(0.88, 0.98)},
                        "active_to_at_risk": {"count": mock.random_int(5, 15), "avg_days": mock.random_int(60, 180), "success_rate": 0.0},
                        "at_risk_to_active": {"count": mock.random_int(3, 10), "avg_days": mock.random_int(14, 45), "success_rate": mock.random_float(0.60, 0.80)},
                        "renewal_to_active": {"count": mock.random_int(18, 45), "avg_days": mock.random_int(30, 90), "success_rate": mock.random_float(0.90, 0.98)}
                    },
                    "most_common_paths": [
                        ["onboarding", "active", "renewal", "active"],
                        ["onboarding", "active", "expansion", "active"],
                        ["active", "at_risk", "active"]
                    ],
                    "transition_velocity": mock.random_float(0.8, 1.5)  # stages per year
                }

            # Transition triggers
            transition_triggers = {
                "to_active": ["onboarding_complete", "first_value_achieved", "90_day_milestone", "health_score_above_70"],
                "to_at_risk": ["health_score_below_60", "usage_decline_30pct", "support_escalation", "executive_complaint", "payment_issues"],
                "to_expansion": ["health_score_above_85", "usage_at_capacity", "new_use_case_identified", "executive_engagement_high"],
                "to_renewal": ["contract_within_180_days", "annual_renewal_date_approaching"],
                "to_churned": ["renewal_lost", "contract_cancelled", "migration_to_competitor"]
            }

            # Average stage duration
            average_stage_duration = {
                stage: characteristics["typical_duration_days"]
                for stage, characteristics in stage_characteristics.items()
            }

            # Stage success metrics
            stage_success_metrics = {}
            for stage in stage_characteristics.keys():
                stage_success_metrics[stage] = {
                    "health_score": stage_characteristics[stage]["avg_health_score"],
                    "completion_rate": mock.random_float(0.75, 0.95) if stage != "at_risk" else mock.random_float(0.50, 0.75),
                    "time_in_stage_vs_target": mock.random_float(0.85, 1.15),
                    "progression_rate": mock.random_float(0.70, 0.92),
                    "satisfaction_score": mock.random_float(3.8, 4.7)
                }

            # At-risk transitions (customers likely to move to at-risk)
            at_risk_transitions = []
            if not current_stage or current_stage != "at_risk":
                num_at_risk = mock.random_int(5, 15)
                for i in range(num_at_risk):
                    at_risk_transitions.append({
                        "client_id": f"cs_{int(datetime.now().timestamp())}_{mock.random_string(6)}",
                        "client_name": f"Customer {i+1}",
                        "current_stage": mock.random_choice(["onboarding", "active", "renewal"]),
                        "risk_score": mock.random_float(0.60, 0.90),
                        "primary_risk_factors": mock.random_choices(
                            ["declining_usage", "low_engagement", "support_issues", "payment_delays", "executive_turnover"],
                            k=2
                        ),
                        "days_until_predicted_transition": mock.random_int(7, 45),
                        "intervention_priority": mock.random_choice(["critical", "high", "medium"]),
                        "recommended_action": "Immediate CSM intervention with executive engagement"
                    })

            # Expansion opportunities
            expansion_opportunities = []
            if not current_stage or current_stage in ["active", "expansion"]:
                num_expansion = mock.random_int(8, 20)
                for i in range(num_expansion):
                    expansion_opportunities.append({
                        "client_id": f"cs_{int(datetime.now().timestamp())}_{mock.random_string(6)}",
                        "client_name": f"Growth Customer {i+1}",
                        "current_stage": "active",
                        "expansion_readiness_score": mock.random_float(0.70, 0.95),
                        "expansion_type": mock.random_choice(["user_growth", "feature_upgrade", "additional_products", "services"]),
                        "estimated_expansion_value": mock.random_int(10000, 75000),
                        "readiness_indicators": ["high_health_score", "capacity_reached", "positive_roi", "executive_advocacy"],
                        "recommended_timing": f"{mock.random_int(14, 60)} days",
                        "recommended_action": "Qualify opportunity and present expansion proposal"
                    })

            # Intervention playbooks
            intervention_playbooks = {}
            if intervention_planning:
                for stage in stage_characteristics.keys():
                    if stage == "onboarding":
                        playbook = {
                            "playbook_name": "Onboarding Success Framework",
                            "objectives": ["Activate primary use case", "Complete user training", "Achieve first value milestone"],
                            "timeline": "Days 1-90",
                            "touchpoints": [
                                {"day": 1, "activity": "Welcome call and kickoff", "owner": "CSM"},
                                {"day": 7, "activity": "Configuration checkpoint", "owner": "CSM"},
                                {"day": 14, "activity": "User training session", "owner": "Training Team"},
                                {"day": 30, "activity": "30-day check-in", "owner": "CSM"},
                                {"day": 60, "activity": "Value realization review", "owner": "CSM"},
                                {"day": 90, "activity": "Onboarding completion review", "owner": "CSM"}
                            ],
                            "success_metrics": ["Time to first value", "Feature adoption rate", "User satisfaction"],
                            "escalation_triggers": ["No activity within 14 days", "Training not scheduled by day 21", "No value milestone by day 60"]
                        }
                    elif stage == "active":
                        playbook = {
                            "playbook_name": "Active Customer Engagement",
                            "objectives": ["Maintain high engagement", "Drive feature adoption", "Identify expansion opportunities"],
                            "timeline": "Ongoing",
                            "touchpoints": [
                                {"frequency": "monthly", "activity": "Check-in call", "owner": "CSM"},
                                {"frequency": "quarterly", "activity": "QBR/EBR", "owner": "CSM"},
                                {"frequency": "semi-annual", "activity": "Strategic planning session", "owner": "CSM + Leadership"}
                            ],
                            "success_metrics": ["Health score >75", "Engagement rate >70%", "NPS >50"],
                            "escalation_triggers": ["Health score drop >10 points", "Usage decline >20%", "Executive concern raised"]
                        }
                    elif stage == "at_risk":
                        playbook = {
                            "playbook_name": "Customer Recovery & Win-Back",
                            "objectives": ["Identify root causes", "Implement recovery plan", "Restore customer health"],
                            "timeline": "14-60 days",
                            "touchpoints": [
                                {"day": 1, "activity": "Immediate assessment call", "owner": "CSM + Manager"},
                                {"day": 3, "activity": "Root cause analysis complete", "owner": "CSM"},
                                {"day": 7, "activity": "Recovery plan presentation", "owner": "CSM + Executive"},
                                {"day": 14, "activity": "Progress checkpoint", "owner": "CSM"},
                                {"day": 30, "activity": "Health reassessment", "owner": "CSM"}
                            ],
                            "success_metrics": ["Health score improvement", "Issue resolution rate", "Engagement recovery"],
                            "escalation_triggers": ["No improvement in 14 days", "Customer non-responsive", "Competitive threat identified"]
                        }
                    elif stage == "expansion":
                        playbook = {
                            "playbook_name": "Expansion Opportunity Development",
                            "objectives": ["Qualify expansion opportunity", "Present business case", "Close expansion deal"],
                            "timeline": "30-120 days",
                            "touchpoints": [
                                {"day": 1, "activity": "Opportunity discovery", "owner": "CSM"},
                                {"day": 14, "activity": "Expansion proposal", "owner": "CSM + Sales"},
                                {"day": 30, "activity": "Stakeholder presentation", "owner": "CSM + Sales + Executive"},
                                {"day": 60, "activity": "Negotiation", "owner": "Sales"},
                                {"day": 90, "activity": "Close and deployment planning", "owner": "CSM + Sales"}
                            ],
                            "success_metrics": ["Expansion close rate", "Average deal size", "Time to deployment"],
                            "escalation_triggers": ["Stalled for >30 days", "Budget concerns", "Competitive threat"]
                        }
                    else:  # renewal
                        playbook = {
                            "playbook_name": "Renewal Success & Expansion",
                            "objectives": ["Demonstrate ROI", "Secure renewal", "Identify expansion opportunities"],
                            "timeline": "180 days pre-renewal",
                            "touchpoints": [
                                {"day": -180, "activity": "Renewal kickoff", "owner": "CSM"},
                                {"day": -120, "activity": "Value review and ROI analysis", "owner": "CSM"},
                                {"day": -90, "activity": "Renewal discussion", "owner": "CSM + Sales"},
                                {"day": -60, "activity": "Proposal presentation", "owner": "CSM + Sales"},
                                {"day": -30, "activity": "Contract finalization", "owner": "Sales"},
                                {"day": 0, "activity": "Renewal celebration", "owner": "CSM"}
                            ],
                            "success_metrics": ["Renewal rate", "On-time renewal %", "Expansion attached %"],
                            "escalation_triggers": ["Customer expresses concerns", "Budget scrutiny", "Competitive evaluation"]
                        }

                    intervention_playbooks[stage] = playbook

            # Automated workflows
            automated_workflows = {}
            if automation_rules:
                for stage in stage_characteristics.keys():
                    workflows = []

                    if stage == "onboarding":
                        workflows = [
                            {
                                "workflow_name": "Welcome Sequence",
                                "trigger": "Customer created",
                                "actions": ["Send welcome email", "Schedule kickoff", "Create onboarding tasks", "Assign CSM"],
                                "automation_level": "full"
                            },
                            {
                                "workflow_name": "Training Reminder",
                                "trigger": "Day 14 no training scheduled",
                                "actions": ["Email training reminder", "CSM task created", "Training team notification"],
                                "automation_level": "full"
                            },
                            {
                                "workflow_name": "30-Day Check-in",
                                "trigger": "Day 30 post-kickoff",
                                "actions": ["Schedule check-in", "Prepare health snapshot", "Send survey"],
                                "automation_level": "semi-automated"
                            }
                        ]
                    elif stage == "active":
                        workflows = [
                            {
                                "workflow_name": "Monthly Touch Base",
                                "trigger": "30 days since last contact",
                                "actions": ["Create CSM task", "Prepare engagement report", "Send check-in email"],
                                "automation_level": "semi-automated"
                            },
                            {
                                "workflow_name": "QBR Preparation",
                                "trigger": "90 days before QBR",
                                "actions": ["Generate QBR deck", "Compile metrics", "Schedule meeting", "Send pre-read"],
                                "automation_level": "semi-automated"
                            }
                        ]
                    elif stage == "at_risk":
                        workflows = [
                            {
                                "workflow_name": "At-Risk Alert",
                                "trigger": "Health score drops below 60",
                                "actions": ["Alert CSM", "Alert manager", "Create intervention task", "Generate risk report"],
                                "automation_level": "full"
                            },
                            {
                                "workflow_name": "Recovery Progress Tracking",
                                "trigger": "Recovery plan activated",
                                "actions": ["Daily health monitoring", "Weekly progress reports", "Escalation alerts"],
                                "automation_level": "full"
                            }
                        ]
                    elif stage == "expansion":
                        workflows = [
                            {
                                "workflow_name": "Expansion Opportunity Alert",
                                "trigger": "Expansion criteria met",
                                "actions": ["Alert CSM", "Alert sales", "Create opportunity record", "Generate proposal template"],
                                "automation_level": "full"
                            }
                        ]
                    else:  # renewal
                        workflows = [
                            {
                                "workflow_name": "Renewal Countdown",
                                "trigger": "180 days to renewal",
                                "actions": ["Alert CSM", "Create renewal tasks", "Generate value report", "Schedule renewal discussion"],
                                "automation_level": "full"
                            },
                            {
                                "workflow_name": "Renewal at Risk",
                                "trigger": "60 days to renewal AND health <70",
                                "actions": ["Executive escalation", "Create recovery plan", "Alert renewals team"],
                                "automation_level": "full"
                            }
                        ]

                    automated_workflows[stage] = workflows

            # Stage optimization recommendations
            stage_optimization = {}
            for stage in stage_characteristics.keys():
                optimizations = []

                if stage == "onboarding":
                    optimizations = [
                        "Reduce time to first value from 45 to 30 days through improved activation",
                        "Increase training completion rate to 95%+ with better scheduling automation",
                        "Implement automated milestone celebrations to drive engagement"
                    ]
                elif stage == "active":
                    optimizations = [
                        "Increase QBR attendance and engagement through better preparation and executive involvement",
                        "Drive feature adoption through targeted campaigns and in-app guidance",
                        "Identify expansion opportunities earlier through predictive signals"
                    ]
                elif stage == "at_risk":
                    optimizations = [
                        "Reduce time to intervention from 14 to 7 days with better early warning system",
                        "Increase recovery rate from 65% to 80% through executive engagement",
                        "Implement automated escalation to prevent silent churn"
                    ]
                elif stage == "expansion":
                    optimizations = [
                        "Increase expansion attach rate from 60% to 75% through better qualification",
                        "Reduce sales cycle from 90 to 60 days with pre-built business cases",
                        "Identify expansion signals earlier through usage analytics"
                    ]
                else:  # renewal
                    optimizations = [
                        "Increase on-time renewal rate to 95%+ through earlier engagement",
                        "Attach expansion to 40% of renewals through value demonstration",
                        "Reduce renewal cycle time through automation and pre-negotiation"
                    ]

                stage_optimization[stage] = optimizations

            # Recommended actions (prioritized)
            recommended_actions = []

            if len(at_risk_transitions) > 0:
                critical_at_risk = [ar for ar in at_risk_transitions if ar["intervention_priority"] == "critical"]
                if critical_at_risk:
                    recommended_actions.append({
                        "priority": "critical",
                        "action": f"Immediate intervention required for {len(critical_at_risk)} customers at critical risk",
                        "customers": [ar["client_id"] for ar in critical_at_risk],
                        "timeline": "Within 48 hours"
                    })

            if len(expansion_opportunities) > 0:
                high_readiness = [eo for eo in expansion_opportunities if eo["expansion_readiness_score"] > 0.85]
                if high_readiness:
                    total_value = sum([eo["estimated_expansion_value"] for eo in high_readiness])
                    recommended_actions.append({
                        "priority": "high",
                        "action": f"Pursue {len(high_readiness)} high-readiness expansion opportunities (${total_value:,} potential)",
                        "customers": [eo["client_id"] for eo in high_readiness],
                        "timeline": "Next 30 days"
                    })

            if "onboarding" in stage_distribution and stage_distribution["onboarding"] > 20:
                recommended_actions.append({
                    "priority": "high",
                    "action": f"Scale onboarding operations - {stage_distribution['onboarding']} customers in onboarding",
                    "timeline": "Next 60 days"
                })

            if intervention_planning:
                recommended_actions.append({
                    "priority": "medium",
                    "action": "Implement stage-specific playbooks for consistent customer experience",
                    "timeline": "Next 90 days"
                })

            if automation_rules:
                recommended_actions.append({
                    "priority": "medium",
                    "action": "Deploy automated workflows to improve efficiency and consistency",
                    "timeline": "Next 90 days"
                })

            # Construct results
            results = LifecycleManagementResults(
                management_id=f"lifecycle_{int(datetime.now().timestamp())}",
                total_customers=total_customers,
                stage_distribution=stage_distribution,
                stage_characteristics=stage_characteristics,
                stage_transitions=stage_transitions,
                transition_triggers=transition_triggers,
                average_stage_duration=average_stage_duration,
                stage_success_metrics=stage_success_metrics,
                at_risk_transitions=at_risk_transitions,
                expansion_opportunities=expansion_opportunities,
                intervention_playbooks=intervention_playbooks,
                automated_workflows=automated_workflows,
                stage_optimization=stage_optimization,
                recommended_actions=recommended_actions
            )

            ctx.info(f"Successfully managed lifecycle stages: {total_customers} customers across {len(stage_distribution)} stages")
            return results.model_dump_json(indent=2)

        except ValidationError as e:
            ctx.error(f"Validation error in manage_lifecycle_stages: {str(e)}")
            raise
        except Exception as e:
            ctx.error(f"Error in manage_lifecycle_stages: {str(e)}")
            raise


    # ============================================================================
    # Tool 6: Track Adoption Milestones (Process 92)
    # ============================================================================


    @mcp.tool()
    def track_adoption_milestones(
        ctx: Context,
        client_id: Optional[str] = None,
        milestone_framework: str = "standard",
        custom_milestones: Optional[List[Dict[str, Any]]] = None,
        include_benchmarks: bool = True,
        celebration_recommendations: bool = True
    ) -> str:
        """
        Track product adoption milestones with celebration and recognition opportunities.

        This milestone tracking system measures customer progress through key adoption
        stages, identifies stuck customers, and provides opportunities for celebration
        and positive reinforcement. It helps CSMs guide customers through their journey
        and recognize achievements that drive long-term success.

        Key Capabilities:
        - Comprehensive milestone framework (standard or custom)
        - Customer-level progress tracking across all milestones
        - Completion rate analysis by milestone
        - Time-to-milestone benchmarking (average, median, percentiles)
        - Correlation analysis between milestones and success outcomes
        - Identification of stuck customers needing intervention
        - Fast-track customer recognition
        - Common blocker identification per milestone
        - Success factor analysis for fast completers
        - Celebration opportunity planning
        - Intervention recommendations for delayed customers

        Args:
            ctx: MCP context for logging and operations
            client_id: Specific customer to track (None for all customers)
            milestone_framework: Framework to use - "standard", "custom", "industry_specific"
            custom_milestones: Custom milestone definitions (required if framework is "custom")
            include_benchmarks: Include benchmark time-to-milestone data
            celebration_recommendations: Include customer celebration recommendations

        Returns:
            JSON string containing comprehensive milestone tracking with:
            - Milestone definitions and criteria
            - Customer progress across milestones
            - Completion rates and timing benchmarks
            - Milestone correlation with success outcomes
            - Stuck and fast-track customers
            - Blockers and success factors
            - Celebration opportunities
            - Intervention recommendations

        Raises:
            ValidationError: If client_id is invalid or custom_milestones malformed

        Example:
            >>> result = track_adoption_milestones(
            ...     ctx,
            ...     client_id=None,
            ...     milestone_framework="standard",
            ...     celebration_recommendations=True
            ... )

        MCP Process: 92 - Product Adoption Milestone Tracking
        """
        try:
            # Validate inputs
            if client_id:
                validate_client_id(client_id)

            valid_frameworks = ["standard", "custom", "industry_specific"]
            if milestone_framework not in valid_frameworks:
                raise ValidationError(f"milestone_framework must be one of: {', '.join(valid_frameworks)}")

            if milestone_framework == "custom" and not custom_milestones:
                raise ValidationError("custom_milestones required when using custom framework")

            ctx.info(f"Tracking adoption milestones using {milestone_framework} framework")

            # Define milestone definitions
            if milestone_framework == "standard":
                milestone_definitions = [
                    {
                        "milestone_id": "m1",
                        "milestone_name": "Account Activated",
                        "description": "Initial account setup and first user login completed",
                        "criteria": ["account_configured", "first_user_login", "initial_data_loaded"],
                        "category": "activation",
                        "typical_timeframe_days": 3,
                        "importance": "critical"
                    },
                    {
                        "milestone_id": "m2",
                        "milestone_name": "First Value Achieved",
                        "description": "Customer experiences initial value from the product",
                        "criteria": ["primary_use_case_active", "first_workflow_completed", "positive_feedback"],
                        "category": "activation",
                        "typical_timeframe_days": 14,
                        "importance": "critical"
                    },
                    {
                        "milestone_id": "m3",
                        "milestone_name": "Team Onboarded",
                        "description": "Core team members trained and active",
                        "criteria": ["5_plus_active_users", "training_completed", "team_collaboration_active"],
                        "category": "adoption",
                        "typical_timeframe_days": 30,
                        "importance": "high"
                    },
                    {
                        "milestone_id": "m4",
                        "milestone_name": "Core Features Adopted",
                        "description": "70% of core features actively used",
                        "criteria": ["core_feature_adoption_70pct", "regular_usage_pattern", "multiple_use_cases"],
                        "category": "adoption",
                        "typical_timeframe_days": 60,
                        "importance": "high"
                    },
                    {
                        "milestone_id": "m5",
                        "milestone_name": "Integration Connected",
                        "description": "Key integrations configured and operational",
                        "criteria": ["1_plus_integration_active", "data_syncing", "workflow_automation"],
                        "category": "integration",
                        "typical_timeframe_days": 45,
                        "importance": "medium"
                    },
                    {
                        "milestone_id": "m6",
                        "milestone_name": "Advanced Features Explored",
                        "description": "Customer exploring advanced capabilities",
                        "criteria": ["advanced_feature_usage", "customization_active", "api_or_automation"],
                        "category": "expansion",
                        "typical_timeframe_days": 90,
                        "importance": "medium"
                    },
                    {
                        "milestone_id": "m7",
                        "milestone_name": "Business Impact Measured",
                        "description": "ROI or business impact quantified and documented",
                        "criteria": ["roi_calculated", "success_metrics_met", "executive_validation"],
                        "category": "value_realization",
                        "typical_timeframe_days": 120,
                        "importance": "critical"
                    },
                    {
                        "milestone_id": "m8",
                        "milestone_name": "Champion Developed",
                        "description": "Internal champion advocating for product",
                        "criteria": ["executive_sponsor_engaged", "positive_testimony", "reference_customer"],
                        "category": "advocacy",
                        "typical_timeframe_days": 180,
                        "importance": "high"
                    }
                ]
            elif milestone_framework == "custom":
                milestone_definitions = custom_milestones
            else:  # industry_specific
                milestone_definitions = [
                    {
                        "milestone_id": "m1",
                        "milestone_name": "Industry-Specific Setup Complete",
                        "description": "Industry-specific configurations and templates activated",
                        "criteria": ["industry_template_selected", "compliance_configured", "data_model_active"],
                        "category": "activation",
                        "typical_timeframe_days": 7,
                        "importance": "critical"
                    }
                    # Would include more industry-specific milestones
                ]

            total_milestones = len(milestone_definitions)

            # Generate customer progress
            num_customers = 1 if client_id else mock.random_int(80, 150)
            customer_progress = []

            for i in range(num_customers):
                cust_id = client_id if client_id else f"cs_{int(datetime.now().timestamp())}_{mock.random_string(6)}"
                milestones_completed = mock.random_int(0, total_milestones)

                progress = {
                    "client_id": cust_id,
                    "client_name": f"Customer {i+1}",
                    "milestones_completed": milestones_completed,
                    "completion_percentage": round(milestones_completed / total_milestones * 100, 1),
                    "current_milestone": milestone_definitions[min(milestones_completed, total_milestones - 1)]["milestone_name"],
                    "days_since_activation": mock.random_int(10, 365),
                    "milestone_details": []
                }

                # Add details for each milestone
                for j, milestone in enumerate(milestone_definitions):
                    if j < milestones_completed:
                        status = "completed"
                        completed_date = (datetime.now() - timedelta(days=mock.random_int(1, 300))).strftime("%Y-%m-%d")
                        days_to_complete = mock.random_int(
                            int(milestone["typical_timeframe_days"] * 0.5),
                            int(milestone["typical_timeframe_days"] * 2.0)
                        )
                    elif j == milestones_completed:
                        status = "in_progress"
                        completed_date = None
                        days_to_complete = None
                    else:
                        status = "pending"
                        completed_date = None
                        days_to_complete = None

                    progress["milestone_details"].append({
                        "milestone_id": milestone["milestone_id"],
                        "milestone_name": milestone["milestone_name"],
                        "status": status,
                        "completed_date": completed_date,
                        "days_to_complete": days_to_complete
                    })

                customer_progress.append(progress)

            # Calculate completion rates
            completion_rates = {}
            for milestone in milestone_definitions:
                completed_count = sum(
                    1 for cp in customer_progress
                    if any(m["milestone_id"] == milestone["milestone_id"] and m["status"] == "completed"
                           for m in cp["milestone_details"])
                )
                completion_rates[milestone["milestone_name"]] = round(completed_count / num_customers, 3)

            # Time to milestone benchmarks
            time_to_milestone = {}
            if include_benchmarks:
                for milestone in milestone_definitions:
                    all_times = []
                    for cp in customer_progress:
                        milestone_detail = next(
                            (m for m in cp["milestone_details"] if m["milestone_id"] == milestone["milestone_id"]),
                            None
                        )
                        if milestone_detail and milestone_detail.get("days_to_complete"):
                            all_times.append(milestone_detail["days_to_complete"])

                    if all_times:
                        all_times_sorted = sorted(all_times)
                        time_to_milestone[milestone["milestone_name"]] = {
                            "average_days": round(sum(all_times) / len(all_times), 1),
                            "median_days": all_times_sorted[len(all_times_sorted) // 2],
                            "p25_days": all_times_sorted[len(all_times_sorted) // 4],
                            "p75_days": all_times_sorted[3 * len(all_times_sorted) // 4],
                            "p90_days": all_times_sorted[int(len(all_times_sorted) * 0.9)],
                            "fastest_days": min(all_times),
                            "slowest_days": max(all_times),
                            "sample_size": len(all_times)
                        }

            # Milestone correlation with success outcomes
            milestone_correlation = {}
            for milestone in milestone_definitions[:5]:  # Top 5 milestones
                milestone_correlation[milestone["milestone_name"]] = {
                    "retention_correlation": mock.random_float(0.55, 0.90),
                    "expansion_correlation": mock.random_float(0.45, 0.80),
                    "nps_correlation": mock.random_float(0.50, 0.85),
                    "health_score_correlation": mock.random_float(0.60, 0.92),
                    "interpretation": "Strong positive correlation with customer success" if mock.random_choice([True, False]) else "Moderate correlation with outcomes"
                }

            # Stuck customers (not progressing through milestones)
            stuck_customers = []
            for cp in customer_progress:
                # Customers who haven't completed a milestone in 60+ days or are significantly behind
                if cp["days_since_activation"] > 60 and cp["completion_percentage"] < 50:
                    current_milestone = cp["current_milestone"]
                    days_stuck = mock.random_int(30, 120)

                    stuck_customers.append({
                        "client_id": cp["client_id"],
                        "client_name": cp["client_name"],
                        "stuck_at_milestone": current_milestone,
                        "days_stuck": days_stuck,
                        "completion_percentage": cp["completion_percentage"],
                        "likely_blockers": mock.random_choices([
                            "Resource constraints",
                            "Technical complexity",
                            "Lack of executive sponsorship",
                            "Change management challenges",
                            "Training gaps"
                        ], k=2),
                        "intervention_priority": "high" if days_stuck > 60 else "medium",
                        "recommended_action": f"CSM intervention: Address blockers and create acceleration plan"
                    })

            stuck_customers = stuck_customers[:15]  # Limit to top 15

            # Fast-track customers (progressing faster than benchmarks)
            fast_track_customers = []
            for cp in customer_progress:
                # Customers completing milestones faster than average
                if cp["completion_percentage"] > 70 and cp["days_since_activation"] < 120:
                    fast_track_customers.append({
                        "client_id": cp["client_id"],
                        "client_name": cp["client_name"],
                        "milestones_completed": cp["milestones_completed"],
                        "completion_percentage": cp["completion_percentage"],
                        "days_since_activation": cp["days_since_activation"],
                        "velocity": round(cp["milestones_completed"] / (cp["days_since_activation"] / 30), 2),
                        "success_factors": [
                            "Strong executive sponsorship",
                            "Dedicated resources",
                            "Clear use cases",
                            "Proactive engagement"
                        ][:mock.random_int(2, 4)],
                        "recognition": "Excellent candidate for case study or reference"
                    })

            fast_track_customers = fast_track_customers[:10]  # Top 10

            # Common milestone blockers
            milestone_blockers = {}
            for milestone in milestone_definitions:
                milestone_blockers[milestone["milestone_name"]] = [
                    mock.random_choice([
                        "Insufficient training or documentation",
                        "Technical integration challenges",
                        "Resource bandwidth constraints",
                        "Executive buy-in missing",
                        "Change management resistance",
                        "Competing priorities",
                        "Data quality issues",
                        "Unclear success criteria"
                    ])
                    for _ in range(mock.random_int(2, 4))
                ]

            # Success factors for fast milestone completion
            success_factors = {}
            for milestone in milestone_definitions:
                success_factors[milestone["milestone_name"]] = [
                    mock.random_choice([
                        "Executive champion actively engaged",
                        "Dedicated project resources allocated",
                        "Clear success metrics defined upfront",
                        "Regular CSM guidance and support",
                        "Strong technical foundation",
                        "Proactive user adoption",
                        "Effective change management",
                        "Quick decision-making process"
                    ])
                    for _ in range(mock.random_int(2, 4))
                ]

            # Celebration opportunities
            celebration_opportunities = []
            if celebration_recommendations:
                # Recent milestone completions worthy of celebration
                for cp in customer_progress:
                    recent_completions = [
                        m for m in cp["milestone_details"]
                        if m["status"] == "completed" and m["completed_date"] and
                        (datetime.now() - datetime.fromisoformat(m["completed_date"])).days <= 14
                    ]

                    if recent_completions:
                        for completion in recent_completions[:2]:  # Up to 2 per customer
                            milestone_info = next(
                                (m for m in milestone_definitions if m["milestone_id"] == completion["milestone_id"]),
                                None
                            )

                            if milestone_info and milestone_info["importance"] in ["critical", "high"]:
                                celebration_opportunities.append({
                                    "client_id": cp["client_id"],
                                    "client_name": cp["client_name"],
                                    "milestone_completed": completion["milestone_name"],
                                    "completed_date": completion["completed_date"],
                                    "celebration_type": mock.random_choice([
                                        "Congratulatory email from leadership",
                                        "Success story feature",
                                        "Certificate of achievement",
                                        "Executive recognition call",
                                        "Social media shoutout (with permission)"
                                    ]),
                                    "internal_recognition": "Feature in internal newsletter and team celebration",
                                    "next_milestone_encouragement": f"On track to complete '{milestone_definitions[milestone_definitions.index(milestone_info) + 1]['milestone_name']}' next!"
                                        if milestone_definitions.index(milestone_info) < len(milestone_definitions) - 1 else "Journey complete!"
                                })

            celebration_opportunities = celebration_opportunities[:20]  # Top 20 opportunities

            # Intervention recommendations
            intervention_recommendations = []

            if len(stuck_customers) > 0:
                high_priority_stuck = [sc for sc in stuck_customers if sc["intervention_priority"] == "high"]
                intervention_recommendations.append({
                    "recommendation_type": "stuck_customer_intervention",
                    "priority": "high",
                    "affected_customers": len(stuck_customers),
                    "critical_count": len(high_priority_stuck),
                    "action": "Implement dedicated acceleration programs for stuck customers",
                    "approach": [
                        "1:1 CSM intervention calls to identify root causes",
                        "Custom acceleration plans with clear timelines",
                        "Executive engagement if needed",
                        "Additional training or resources as required",
                        "Weekly progress checkpoints"
                    ],
                    "expected_outcome": f"Move {len(stuck_customers)} customers through milestone blockers within 30-60 days"
                })

            if len(fast_track_customers) > 0:
                intervention_recommendations.append({
                    "recommendation_type": "fast_track_recognition",
                    "priority": "medium",
                    "affected_customers": len(fast_track_customers),
                    "action": "Recognize and leverage fast-track customers",
                    "approach": [
                        "Celebrate achievements and capture success stories",
                        "Request case studies and references",
                        "Identify expansion opportunities",
                        "Invite to customer advisory board",
                        "Feature in marketing materials (with permission)"
                    ],
                    "expected_outcome": "Strengthen relationships and create advocacy opportunities"
                })

            # If overall completion rates are low
            avg_completion_rate = sum(completion_rates.values()) / len(completion_rates) if completion_rates else 0
            if avg_completion_rate < 0.60:
                intervention_recommendations.append({
                    "recommendation_type": "overall_adoption_improvement",
                    "priority": "high",
                    "action": "Improve overall milestone completion rates",
                    "approach": [
                        "Review and simplify milestone criteria",
                        "Enhance onboarding and training programs",
                        "Implement milestone tracking in CSM playbooks",
                        "Add automated milestone nudges and guidance",
                        "Create milestone achievement incentives"
                    ],
                    "expected_outcome": f"Increase average completion rate from {avg_completion_rate:.1%} to 75%+"
                })

            # Recommended actions
            recommended_actions = []

            if len(stuck_customers) > 0:
                recommended_actions.append(f"Priority intervention: {len(stuck_customers)} customers stuck at milestones")

            if len(celebration_opportunities) > 0:
                recommended_actions.append(f"Celebrate {len(celebration_opportunities)} recent milestone achievements")

            if len(fast_track_customers) > 0:
                recommended_actions.append(f"Capture success stories from {len(fast_track_customers)} fast-track customers")

            recommended_actions.extend([
                "Integrate milestone tracking into regular CSM activities",
                "Identify and address common blockers systematically",
                "Replicate success factors from fast-adopting customers"
            ])

            # Construct results
            results = AdoptionMilestoneResults(
                tracking_id=f"milestone_{int(datetime.now().timestamp())}",
                milestone_framework=milestone_framework,
                total_milestones=total_milestones,
                milestone_definitions=milestone_definitions,
                customer_progress=customer_progress,
                completion_rates=completion_rates,
                time_to_milestone=time_to_milestone,
                milestone_correlation=milestone_correlation,
                stuck_customers=stuck_customers,
                fast_track_customers=fast_track_customers,
                milestone_blockers=milestone_blockers,
                success_factors=success_factors,
                benchmark_comparison={
                    "avg_completion_rate": round(avg_completion_rate, 3),
                    "industry_benchmark": 0.68,
                    "vs_benchmark": "above" if avg_completion_rate > 0.68 else "below"
                } if include_benchmarks else {},
                celebration_opportunities=celebration_opportunities,
                intervention_recommendations=intervention_recommendations,
                recommended_actions=recommended_actions
            )

            ctx.info(f"Successfully tracked adoption milestones: {num_customers} customers across {total_milestones} milestones")
            return results.model_dump_json(indent=2)

        except ValidationError as e:
            ctx.error(f"Validation error in track_adoption_milestones: {str(e)}")
            raise
        except Exception as e:
            ctx.error(f"Error in track_adoption_milestones: {str(e)}")
            raise


    # ============================================================================
    # Tool 7: Segment by Value Tier (Process 93)
    # ============================================================================


    @mcp.tool()
    def segment_by_value_tier(
        ctx: Context,
        segmentation_criteria: Dict[str, Any],
        tier_definitions: Optional[Dict[str, Dict[str, Any]]] = None,
        service_level_mapping: bool = True,
        vip_identification: bool = True,
        resource_planning: bool = True
    ) -> str:
        """
        Segment customers by value tier for VIP treatment and tiered service levels.

        This value-based segmentation system classifies customers into strategic tiers
        based on multiple value dimensions, enabling differentiated service delivery,
        resource optimization, and VIP account identification. It provides clear tier
        definitions, service level recommendations, and resource allocation guidance.

        Key Capabilities:
        - Multi-dimensional value assessment (ARR, LTV, potential, strategic value)
        - Configurable tier definitions and thresholds
        - Customer distribution and metrics by tier
        - Value concentration analysis (Pareto principle)
        - VIP account identification and flagging
        - Tier-specific characteristics and profiles
        - Service level recommendations per tier
        - CSM resource allocation optimization
        - Tier performance tracking (retention, NPS, expansion)
        - Upgrade candidate identification
        - Downgrade risk detection
        - Tier-specific optimization strategies

        Args:
            ctx: MCP context for logging and operations
            segmentation_criteria: Criteria for value segmentation (ARR, LTV, potential, etc.)
            tier_definitions: Custom tier definitions (uses defaults if None)
            service_level_mapping: Include service level recommendations per tier
            vip_identification: Identify and flag VIP accounts
            resource_planning: Include CSM resource allocation planning

        Returns:
            JSON string containing comprehensive value tier segmentation with:
            - Tier definitions and criteria
            - Customer distribution by tier
            - Tier metrics and performance
            - Value concentration analysis
            - VIP accounts requiring special attention
            - Service level recommendations
            - CSM resource allocation guidance
            - Upgrade candidates and downgrade risks
            - Tier optimization strategies

        Raises:
            ValidationError: If segmentation_criteria is malformed

        Example:
            >>> result = segment_by_value_tier(
            ...     ctx,
            ...     segmentation_criteria={
            ...         "primary_dimension": "arr",
            ...         "secondary_dimensions": ["ltv", "expansion_potential"]
            ...     },
            ...     vip_identification=True
            ... )

        MCP Process: 93 - VIP Treatment & Tiered Service Levels
        """
        try:
            ctx.info("Segmenting customers by value tier")

            # Use provided tier definitions or defaults
            if not tier_definitions:
                tier_definitions = {
                    "strategic": {
                        "name": "Strategic Enterprise",
                        "criteria": {
                            "min_arr": 200000,
                            "strategic_importance": "critical",
                            "expansion_potential": "high"
                        },
                        "color": "platinum",
                        "priority_level": 1
                    },
                    "enterprise": {
                        "name": "Enterprise",
                        "criteria": {
                            "min_arr": 100000,
                            "max_arr": 200000,
                            "account_complexity": "high"
                        },
                        "color": "gold",
                        "priority_level": 2
                    },
                    "professional": {
                        "name": "Professional",
                        "criteria": {
                            "min_arr": 50000,
                            "max_arr": 100000
                        },
                        "color": "silver",
                        "priority_level": 3
                    },
                    "standard": {
                        "name": "Standard",
                        "criteria": {
                            "min_arr": 10000,
                            "max_arr": 50000
                        },
                        "color": "bronze",
                        "priority_level": 4
                    },
                    "starter": {
                        "name": "Starter",
                        "criteria": {
                            "max_arr": 10000
                        },
                        "color": "standard",
                        "priority_level": 5
                    }
                }

            # Generate customer distribution by tier
            total_customers = mock.random_int(150, 400)

            tier_distribution = {
                "strategic": mock.random_int(5, 15),
                "enterprise": mock.random_int(15, 40),
                "professional": mock.random_int(40, 80),
                "standard": mock.random_int(60, 150),
                "starter": mock.random_int(30, 115)
            }

            # Adjust to match total
            adjustment_factor = total_customers / sum(tier_distribution.values())
            tier_distribution = {k: int(v * adjustment_factor) for k, v in tier_distribution.items()}

            # Calculate tier metrics
            tier_metrics = {}
            total_arr = 0

            for tier, count in tier_distribution.items():
                tier_def = tier_definitions[tier]
                min_arr = tier_def["criteria"].get("min_arr", 0)
                max_arr = tier_def["criteria"].get("max_arr", 1000000)

                # Generate realistic ARR for tier
                if tier == "strategic":
                    avg_arr = mock.random_float(250000, 500000)
                elif tier == "enterprise":
                    avg_arr = mock.random_float(120000, 180000)
                elif tier == "professional":
                    avg_arr = mock.random_float(60000, 90000)
                elif tier == "standard":
                    avg_arr = mock.random_float(20000, 40000)
                else:  # starter
                    avg_arr = mock.random_float(5000, 9000)

                tier_arr = avg_arr * count
                total_arr += tier_arr

                # Calculate LTV (typically 3-5x ARR depending on tier)
                ltv_multiplier = {
                    "strategic": mock.random_float(4.5, 6.0),
                    "enterprise": mock.random_float(4.0, 5.5),
                    "professional": mock.random_float(3.5, 4.5),
                    "standard": mock.random_float(2.5, 3.5),
                    "starter": mock.random_float(2.0, 3.0)
                }.get(tier, 3.0)

                tier_metrics[tier] = {
                    "customer_count": count,
                    "total_arr": round(tier_arr, 2),
                    "avg_arr": round(avg_arr, 2),
                    "avg_ltv": round(avg_arr * ltv_multiplier, 2),
                    "avg_health_score": mock.random_float(70, 92),
                    "avg_nps": mock.random_int(35, 75),
                    "retention_rate": mock.random_float(0.85, 0.98),
                    "expansion_rate": mock.random_float(0.15, 0.45),
                    "avg_contract_length_months": mock.random_int(12, 36)
                }

            # Value concentration analysis
            value_concentration = {
                "total_customers": total_customers,
                "total_arr": round(total_arr, 2),
                "pareto_analysis": {
                    "top_20_percent_customers": int(total_customers * 0.20),
                    "arr_from_top_20": round(
                        tier_metrics["strategic"]["total_arr"] + tier_metrics["enterprise"]["total_arr"],
                        2
                    ),
                    "percentage_from_top_20": round(
                        (tier_metrics["strategic"]["total_arr"] + tier_metrics["enterprise"]["total_arr"]) / total_arr * 100,
                        1
                    )
                },
                "tier_concentration": {
                    tier: {
                        "arr_percentage": round(metrics["total_arr"] / total_arr * 100, 1),
                        "customer_percentage": round(metrics["customer_count"] / total_customers * 100, 1)
                    }
                    for tier, metrics in tier_metrics.items()
                },
                "concentration_ratio": "High" if tier_metrics["strategic"]["total_arr"] / total_arr > 0.30 else "Moderate"
            }

            # VIP accounts (if requested)
            vip_accounts = []
            if vip_identification:
                num_vips = mock.random_int(8, 20)
                for i in range(num_vips):
                    vip_accounts.append({
                        "client_id": f"cs_{int(datetime.now().timestamp())}_{mock.random_string(6)}",
                        "client_name": f"VIP Strategic Account {i+1}",
                        "tier": "strategic",
                        "arr": mock.random_float(250000, 750000),
                        "ltv": mock.random_float(1250000, 4500000),
                        "health_score": mock.random_int(75, 98),
                        "vip_reasons": mock.random_choices([
                            "Top 10 by ARR",
                            "Strategic industry leader",
                            "High expansion potential",
                            "Executive relationship",
                            "Reference account",
                            "Industry influencer"
                        ], k=3),
                        "special_treatment": [
                            "Dedicated senior CSM",
                            "Quarterly executive business reviews",
                            "24/7 priority support",
                            "Product roadmap preview access",
                            "Custom success programs"
                        ],
                        "relationship_owner": f"Senior CSM {mock.random_int(1, 5)}",
                        "executive_sponsor": f"VP Customer Success" if i < 5 else "Director Customer Success"
                    })

            # Tier characteristics (typical customer profiles)
            tier_characteristics = {}
            for tier, tier_def in tier_definitions.items():
                if tier == "strategic":
                    characteristics = {
                        "typical_company_size": "1000+ employees",
                        "typical_industry": ["Enterprise Tech", "Financial Services", "Healthcare"],
                        "decision_complexity": "Very High (multiple stakeholders)",
                        "sales_cycle": "6-12 months",
                        "typical_use_cases": ["Enterprise-wide deployment", "Mission-critical workflows", "Complex integrations"],
                        "support_expectations": "24/7 with SLA",
                        "customization_needs": "High",
                        "user_count_range": "500-5000+"
                    }
                elif tier == "enterprise":
                    characteristics = {
                        "typical_company_size": "500-1000 employees",
                        "typical_industry": ["Technology", "Manufacturing", "Professional Services"],
                        "decision_complexity": "High (departmental/multi-department)",
                        "sales_cycle": "3-6 months",
                        "typical_use_cases": ["Department-wide deployment", "Core business processes", "Standard integrations"],
                        "support_expectations": "Business hours with priority",
                        "customization_needs": "Medium-High",
                        "user_count_range": "100-500"
                    }
                elif tier == "professional":
                    characteristics = {
                        "typical_company_size": "100-500 employees",
                        "typical_industry": ["SaaS", "Consulting", "E-commerce"],
                        "decision_complexity": "Medium (team/department level)",
                        "sales_cycle": "1-3 months",
                        "typical_use_cases": ["Team collaboration", "Process optimization", "Basic integrations"],
                        "support_expectations": "Business hours support",
                        "customization_needs": "Medium",
                        "user_count_range": "25-100"
                    }
                elif tier == "standard":
                    characteristics = {
                        "typical_company_size": "20-100 employees",
                        "typical_industry": ["SMB", "Startups", "Agencies"],
                        "decision_complexity": "Low-Medium (team lead decision)",
                        "sales_cycle": "2-4 weeks",
                        "typical_use_cases": ["Team productivity", "Basic workflows", "Essential features"],
                        "support_expectations": "Email/chat support",
                        "customization_needs": "Low-Medium",
                        "user_count_range": "5-25"
                    }
                else:  # starter
                    characteristics = {
                        "typical_company_size": "1-20 employees",
                        "typical_industry": ["Small Business", "Freelancers", "Early Startups"],
                        "decision_complexity": "Low (individual/small team)",
                        "sales_cycle": "Days to 2 weeks",
                        "typical_use_cases": ["Individual/small team use", "Core features only"],
                        "support_expectations": "Self-service + email",
                        "customization_needs": "Low",
                        "user_count_range": "1-5"
                    }

                tier_characteristics[tier] = characteristics

            # Service level recommendations
            service_level_recommendations = {}
            if service_level_mapping:
                for tier in tier_definitions.keys():
                    if tier == "strategic":
                        service_level = {
                            "csm_model": "Dedicated Senior CSM (1:5-10 ratio)",
                            "touch_frequency": "Weekly proactive outreach",
                            "ebr_frequency": "Quarterly with executive participation",
                            "support_tier": "Platinum - 24/7 with 1-hour SLA",
                            "success_programs": [
                                "Dedicated success planning",
                                "Executive advisory board access",
                                "Custom training programs",
                                "Strategic roadmap reviews",
                                "Annual on-site visits"
                            ],
                            "communication_channels": ["Direct phone", "Dedicated Slack channel", "Video conference", "In-person"],
                            "escalation_path": "Direct to VP/C-level",
                            "automation_level": "Low (high-touch)",
                            "additional_services": ["Technical account manager", "Solution architect access", "Priority feature requests"]
                        }
                    elif tier == "enterprise":
                        service_level = {
                            "csm_model": "Named CSM (1:15-20 ratio)",
                            "touch_frequency": "Bi-weekly check-ins",
                            "ebr_frequency": "Quarterly",
                            "support_tier": "Gold - Business hours with 2-hour SLA",
                            "success_programs": [
                                "Success planning",
                                "Training programs",
                                "Best practices workshops",
                                "Peer networking events"
                            ],
                            "communication_channels": ["Video conference", "Email", "Phone"],
                            "escalation_path": "CSM Manager",
                            "automation_level": "Low-Medium",
                            "additional_services": ["Quarterly health reviews", "Custom reporting"]
                        }
                    elif tier == "professional":
                        service_level = {
                            "csm_model": "Pooled CSM (1:40-50 ratio)",
                            "touch_frequency": "Monthly check-ins",
                            "ebr_frequency": "Semi-annual",
                            "support_tier": "Silver - Business hours with 4-hour SLA",
                            "success_programs": [
                                "Group training sessions",
                                "Office hours",
                                "Self-service resources",
                                "Community access"
                            ],
                            "communication_channels": ["Email", "Video conference (scheduled)", "In-app messaging"],
                            "escalation_path": "Support escalation team",
                            "automation_level": "Medium",
                            "additional_services": ["Usage analytics dashboards"]
                        }
                    elif tier == "standard":
                        service_level = {
                            "csm_model": "Digital/Tech-touch (1:100+ ratio)",
                            "touch_frequency": "Quarterly automated check-ins + milestone-based",
                            "ebr_frequency": "Annual (optional)",
                            "support_tier": "Standard - Email/chat with 8-hour SLA",
                            "success_programs": [
                                "Automated onboarding",
                                "Webinar training",
                                "Knowledge base",
                                "Community forum"
                            ],
                            "communication_channels": ["Email", "In-app messaging", "Chat"],
                            "escalation_path": "Support ticket system",
                            "automation_level": "High",
                            "additional_services": ["Basic analytics"]
                        }
                    else:  # starter
                        service_level = {
                            "csm_model": "Full self-service (no dedicated CSM)",
                            "touch_frequency": "Automated milestone congratulations",
                            "ebr_frequency": "None",
                            "support_tier": "Basic - Email with 24-hour SLA",
                            "success_programs": [
                                "Self-service onboarding",
                                "Video tutorials",
                                "Documentation",
                                "Community forum"
                            ],
                            "communication_channels": ["Email", "In-app help"],
                            "escalation_path": "Support ticket system",
                            "automation_level": "Very High",
                            "additional_services": ["Basic product usage tips"]
                        }

                    service_level_recommendations[tier] = service_level

            # CSM allocation and resource planning
            csm_allocation = {}
            if resource_planning:
                total_csm_fte = 0

                for tier in tier_definitions.keys():
                    count = tier_distribution.get(tier, 0)

                    if tier == "strategic":
                        ratio = 8  # 1 CSM : 8 customers
                        csm_level = "Senior CSM"
                    elif tier == "enterprise":
                        ratio = 18
                        csm_level = "CSM"
                    elif tier == "professional":
                        ratio = 45
                        csm_level = "CSM"
                    elif tier == "standard":
                        ratio = 120
                        csm_level = "Digital CSM"
                    else:  # starter
                        ratio = 0  # Self-service
                        csm_level = "N/A (Self-service)"

                    required_fte = round(count / ratio, 2) if ratio > 0 else 0
                    total_csm_fte += required_fte

                    csm_allocation[tier] = {
                        "customer_count": count,
                        "csm_to_customer_ratio": f"1:{ratio}" if ratio > 0 else "Self-service",
                        "required_fte": required_fte,
                        "csm_level": csm_level,
                        "annual_cost_per_fte": 120000 if "Senior" in csm_level else (100000 if csm_level == "CSM" else 80000),
                        "total_annual_cost": required_fte * (120000 if "Senior" in csm_level else (100000 if csm_level == "CSM" else 80000))
                    }

                csm_allocation["summary"] = {
                    "total_fte_required": round(total_csm_fte, 1),
                    "total_annual_cost": sum([tier["total_annual_cost"] for tier in csm_allocation.values() if isinstance(tier, dict) and "total_annual_cost" in tier]),
                    "cost_per_customer": round(sum([tier["total_annual_cost"] for tier in csm_allocation.values() if isinstance(tier, dict) and "total_annual_cost" in tier]) / total_customers, 2),
                    "arr_coverage_ratio": round(total_arr / sum([tier["total_annual_cost"] for tier in csm_allocation.values() if isinstance(tier, dict) and "total_annual_cost" in tier]), 1)
                }

            # Tier performance comparison
            tier_performance = {}
            for tier, metrics in tier_metrics.items():
                tier_performance[tier] = {
                    "health_score": metrics["avg_health_score"],
                    "retention_rate": metrics["retention_rate"],
                    "nps": metrics["avg_nps"],
                    "expansion_rate": metrics["expansion_rate"],
                    "ltv_to_cac_ratio": mock.random_float(3.0, 8.0),
                    "performance_rating": "Excellent" if metrics["avg_health_score"] > 85 else ("Good" if metrics["avg_health_score"] > 75 else "Needs Improvement")
                }

            # Upgrade candidates (customers ready to move to higher tier)
            upgrade_candidates = []
            num_upgrades = mock.random_int(8, 20)
            for i in range(num_upgrades):
                current_tier = mock.random_choice(["starter", "standard", "professional", "enterprise"])
                next_tier_map = {
                    "starter": "standard",
                    "standard": "professional",
                    "professional": "enterprise",
                    "enterprise": "strategic"
                }

                upgrade_candidates.append({
                    "client_id": f"cs_{int(datetime.now().timestamp())}_{mock.random_string(6)}",
                    "client_name": f"Growth Customer {i+1}",
                    "current_tier": current_tier,
                    "recommended_tier": next_tier_map[current_tier],
                    "upgrade_readiness_score": mock.random_float(0.75, 0.95),
                    "upgrade_indicators": mock.random_choices([
                        "ARR approaching tier threshold",
                        "User growth exceeding tier capacity",
                        "Feature usage indicating higher needs",
                        "Multiple expansion discussions",
                        "Executive engagement increasing"
                    ], k=3),
                    "estimated_timeline": f"{mock.random_int(30, 120)} days",
                    "estimated_arr_increase": mock.random_int(15000, 75000),
                    "recommended_action": "Present tier upgrade benefits and value proposition"
                })

            # Downgrade risks (customers at risk of moving to lower tier)
            downgrade_risks = []
            num_downgrades = mock.random_int(3, 12)
            for i in range(num_downgrades):
                current_tier = mock.random_choice(["strategic", "enterprise", "professional", "standard"])
                downgrade_risks.append({
                    "client_id": f"cs_{int(datetime.now().timestamp())}_{mock.random_string(6)}",
                    "client_name": f"At-Risk Premium Customer {i+1}",
                    "current_tier": current_tier,
                    "risk_score": mock.random_float(0.60, 0.90),
                    "downgrade_indicators": mock.random_choices([
                        "Usage declining significantly",
                        "Budget cuts announced",
                        "User seat reduction requests",
                        "Downgrade inquiries",
                        "Feature usage below tier expectations"
                    ], k=2),
                    "potential_arr_loss": mock.random_int(20000, 150000),
                    "intervention_priority": "critical" if mock.random_choice([True, False]) else "high",
                    "recommended_action": "Immediate retention intervention to prevent downgrade/churn"
                })

            # Tier optimization strategies
            tier_optimization = {}
            for tier in tier_definitions.keys():
                strategies = []

                if tier == "strategic":
                    strategies = [
                        "Maximize retention through unparalleled service and executive relationships",
                        "Identify expansion opportunities through strategic planning sessions",
                        "Develop into advocates and reference accounts",
                        "Ensure executive-level relationships at multiple levels"
                    ]
                elif tier == "enterprise":
                    strategies = [
                        "Increase retention through consistent value delivery and engagement",
                        "Identify opportunities to upgrade to strategic tier",
                        "Optimize CSM efficiency while maintaining quality",
                        "Drive feature adoption to increase stickiness"
                    ]
                elif tier == "professional":
                    strategies = [
                        "Balance high-touch and tech-touch for efficiency",
                        "Drive self-service adoption to improve margins",
                        "Identify high-potential accounts for upgrade",
                        "Implement scalable success programs"
                    ]
                elif tier == "standard":
                    strategies = [
                        "Maximize automation and digital engagement",
                        "Focus on activation and early value",
                        "Identify upgrade candidates early",
                        "Implement community-driven support model"
                    ]
                else:  # starter
                    strategies = [
                        "Full self-service model with excellent onboarding",
                        "Nurture towards upgrade through success and growth",
                        "Minimal cost to serve while maintaining satisfaction",
                        "Use as pipeline for higher tiers"
                    ]

                tier_optimization[tier] = strategies

            # Strategic recommendations
            recommendations = []

            recommendations.append(
                f"Prioritize retention of {tier_distribution.get('strategic', 0)} strategic accounts "
                f"representing {value_concentration['tier_concentration']['strategic']['arr_percentage']:.1f}% of ARR"
            )

            if len(vip_accounts) > 0:
                recommendations.append(f"Implement VIP treatment protocols for {len(vip_accounts)} strategic accounts")

            if len(upgrade_candidates) > 0:
                potential_arr = sum([uc["estimated_arr_increase"] for uc in upgrade_candidates])
                recommendations.append(
                    f"Pursue {len(upgrade_candidates)} tier upgrade opportunities (${potential_arr:,} potential ARR)"
                )

            if len(downgrade_risks) > 0:
                at_risk_arr = sum([dr["potential_arr_loss"] for dr in downgrade_risks])
                recommendations.append(
                    f"URGENT: Prevent {len(downgrade_risks)} downgrades at risk (${at_risk_arr:,} ARR at risk)"
                )

            if resource_planning:
                recommendations.append(
                    f"Allocate {csm_allocation['summary']['total_fte_required']:.1f} FTE across tiers "
                    f"for optimal coverage"
                )

            recommendations.append("Regularly review tier classifications and adjust service delivery")
            recommendations.append("Benchmark tier performance against industry standards")

            # Construct results
            results = ValueTierResults(
                segmentation_id=f"tier_{int(datetime.now().timestamp())}",
                total_customers=total_customers,
                tier_definitions=tier_definitions,
                tier_distribution=tier_distribution,
                tier_metrics=tier_metrics,
                value_concentration=value_concentration,
                vip_accounts=vip_accounts,
                tier_characteristics=tier_characteristics,
                service_level_recommendations=service_level_recommendations,
                csm_allocation=csm_allocation,
                tier_performance=tier_performance,
                upgrade_candidates=upgrade_candidates,
                downgrade_risks=downgrade_risks,
                tier_optimization=tier_optimization,
                recommended_actions=recommendations
            )

            ctx.info(f"Successfully segmented {total_customers} customers into {len(tier_definitions)} value tiers")
            return results.model_dump_json(indent=2)

        except ValidationError as e:
            ctx.error(f"Validation error in segment_by_value_tier: {str(e)}")
            raise
        except Exception as e:
            ctx.error(f"Error in segment_by_value_tier: {str(e)}")
            raise


    # ============================================================================
    # Tool 8: Analyze Engagement Patterns (Process 94)
    # ============================================================================


    @mcp.tool()
    def analyze_engagement_patterns(
        ctx: Context,
        analysis_scope: str = "all_customers",
        scope_filter: Optional[Dict[str, Any]] = None,
        pattern_types: List[str] = None,
        lookback_period_days: int = 90,
        anomaly_detection: bool = True,
        predictive_insights: bool = True
    ) -> str:
        """
        Analyze behavioral engagement patterns to optimize customer success strategies.

        This advanced pattern analysis system identifies behavioral trends, user personas,
        temporal patterns, and engagement anomalies across the customer base. It provides
        actionable insights to optimize engagement strategies, predict outcomes, and
        personalize customer success approaches based on behavioral data.

        Key Capabilities:
        - Multi-dimensional pattern identification (temporal, feature, communication, support)
        - User persona development based on behavior
        - Temporal engagement pattern analysis (day, time, seasonality)
        - Feature usage pattern recognition
        - Communication and response pattern analysis
        - Support interaction pattern tracking
        - Success pattern correlation (what drives positive outcomes)
        - Risk pattern identification (early churn indicators)
        - Anomaly detection and alerting
        - Pattern transition analysis across lifecycle
        - Predictive insights based on historical patterns
        - Engagement optimization recommendations

        Args:
            ctx: MCP context for logging and operations
            analysis_scope: Scope of analysis - "all_customers", "segment", or "individual"
            scope_filter: Filter criteria for scoped analysis (e.g., {"tier": "enterprise"})
            pattern_types: Types of patterns to analyze (default: all types)
            lookback_period_days: Days of historical data to analyze (7-365)
            anomaly_detection: Include anomaly detection in patterns
            predictive_insights: Include predictive pattern insights

        Returns:
            JSON string containing comprehensive engagement pattern analysis with:
            - Identified patterns with detailed descriptions
            - Temporal engagement patterns
            - Feature usage patterns
            - Communication and support patterns
            - User persona definitions
            - Success and risk pattern correlations
            - Detected anomalies
            - Pattern transitions across lifecycle
            - Predictive insights
            - Optimization recommendations

        Raises:
            ValidationError: If parameters are out of range

        Example:
            >>> result = analyze_engagement_patterns(
            ...     ctx,
            ...     analysis_scope="segment",
            ...     scope_filter={"tier": "enterprise"},
            ...     lookback_period_days=90,
            ...     anomaly_detection=True
            ... )

        MCP Process: 94 - Behavioral Pattern Analysis
        """
        try:
            # Validate parameters
            if lookback_period_days < 7 or lookback_period_days > 365:
                raise ValidationError("lookback_period_days must be between 7 and 365")

            if analysis_scope not in ["all_customers", "segment", "individual"]:
                raise ValidationError("analysis_scope must be 'all_customers', 'segment', or 'individual'")

            if not pattern_types:
                pattern_types = ["temporal", "feature_usage", "communication", "support"]

            ctx.info(f"Analyzing engagement patterns for {analysis_scope} over {lookback_period_days} days")

            # Determine customers analyzed based on scope
            if analysis_scope == "individual":
                customers_analyzed = 1
            elif analysis_scope == "segment":
                customers_analyzed = mock.random_int(30, 100)
            else:  # all_customers
                customers_analyzed = mock.random_int(100, 300)

            # Analysis scope summary
            scope_summary = {
                "scope_type": analysis_scope,
                "filter_applied": scope_filter if scope_filter else {},
                "customers_analyzed": customers_analyzed,
                "analysis_period": {
                    "start_date": (datetime.now() - timedelta(days=lookback_period_days)).strftime("%Y-%m-%d"),
                    "end_date": datetime.now().strftime("%Y-%m-%d"),
                    "days": lookback_period_days
                },
                "pattern_types_analyzed": pattern_types,
                "data_points_analyzed": customers_analyzed * lookback_period_days * mock.random_int(5, 20)
            }

            # Identified patterns
            identified_patterns = [
                {
                    "pattern_id": "pat_001",
                    "pattern_name": "Monday Morning Surge",
                    "pattern_type": "temporal",
                    "description": "Significant increase in activity on Monday mornings (9-11am)",
                    "prevalence": mock.random_float(0.65, 0.85),
                    "strength": "strong",
                    "business_impact": "High engagement window for proactive outreach",
                    "recommendation": "Schedule important communications and check-ins for Monday mornings"
                },
                {
                    "pattern_id": "pat_002",
                    "pattern_name": "Friday Afternoon Drop",
                    "pattern_type": "temporal",
                    "description": "Sharp decline in engagement after 2pm on Fridays",
                    "prevalence": mock.random_float(0.70, 0.90),
                    "strength": "strong",
                    "business_impact": "Avoid Friday afternoon engagement initiatives",
                    "recommendation": "Schedule critical activities Monday-Thursday"
                },
                {
                    "pattern_id": "pat_003",
                    "pattern_name": "Sequential Feature Adoption",
                    "pattern_type": "feature_usage",
                    "description": "Users adopt features in predictable sequence: Core -> Collaboration -> Advanced",
                    "prevalence": mock.random_float(0.55, 0.75),
                    "strength": "moderate",
                    "business_impact": "Predictable adoption path enables proactive guidance",
                    "recommendation": "Implement staged feature introduction based on adoption sequence"
                },
                {
                    "pattern_id": "pat_004",
                    "pattern_name": "Support-Driven Churn Signal",
                    "pattern_type": "support",
                    "description": "3+ support tickets in 30 days correlates with increased churn risk",
                    "prevalence": mock.random_float(0.40, 0.65),
                    "strength": "strong",
                    "business_impact": "Early churn warning indicator",
                    "recommendation": "Automatic CSM escalation after 3rd ticket in 30 days"
                },
                {
                    "pattern_id": "pat_005",
                    "pattern_name": "Executive Engagement Booster",
                    "pattern_type": "communication",
                    "description": "Executive-level communication increases overall team engagement by 40%",
                    "prevalence": mock.random_float(0.60, 0.80),
                    "strength": "strong",
                    "business_impact": "Executive engagement drives team activation",
                    "recommendation": "Prioritize executive relationship building"
                },
                {
                    "pattern_id": "pat_006",
                    "pattern_name": "Weekend Warrior Persona",
                    "pattern_type": "temporal",
                    "description": "~15% of users highly active on weekends (use for time-sensitive work)",
                    "prevalence": mock.random_float(0.12, 0.18),
                    "strength": "moderate",
                    "business_impact": "Identifies power users with unique usage patterns",
                    "recommendation": "Recognize and support weekend users with async resources"
                }
            ]

            # Temporal patterns
            temporal_patterns = {
                "daily_patterns": {
                    "peak_activity_hours": [9, 10, 11, 14, 15, 16],
                    "low_activity_hours": [0, 1, 2, 3, 4, 5, 6, 22, 23],
                    "hour_distribution": {str(h): mock.random_int(50, 300) if h in [9, 10, 11, 14, 15, 16] else mock.random_int(5, 80) for h in range(24)},
                    "consistency_score": mock.random_float(0.70, 0.90)
                },
                "weekly_patterns": {
                    "peak_days": ["Tuesday", "Wednesday", "Thursday"],
                    "low_days": ["Saturday", "Sunday"],
                    "day_distribution": {
                        "Monday": mock.random_int(800, 1200),
                        "Tuesday": mock.random_int(1000, 1400),
                        "Wednesday": mock.random_int(1000, 1400),
                        "Thursday": mock.random_int(900, 1300),
                        "Friday": mock.random_int(700, 1100),
                        "Saturday": mock.random_int(200, 400),
                        "Sunday": mock.random_int(150, 350)
                    },
                    "weekday_vs_weekend_ratio": mock.random_float(4.0, 7.0)
                },
                "monthly_patterns": {
                    "peak_periods": ["Month start (1-5)", "Mid-month (15-20)"],
                    "low_periods": ["Month end (28-31)", "Holiday periods"],
                    "seasonality_detected": mock.random_choice([True, False]),
                    "fiscal_calendar_correlation": mock.random_choice([True, False])
                },
                "session_patterns": {
                    "avg_session_duration_minutes": mock.random_float(15.0, 35.0),
                    "typical_session_frequency": "Daily for 60%, Weekly for 30%, Monthly for 10%",
                    "session_clustering": "Most users have consistent session times (habit formation)"
                }
            }

            # Feature usage patterns
            feature_usage_patterns = {
                "adoption_sequences": {
                    "common_path_1": ["Dashboard", "Basic Reports", "Data Export", "Advanced Analytics"],
                    "common_path_2": ["Setup", "Team Invite", "Collaboration Tools", "Integrations"],
                    "common_path_3": ["Quick Start", "Templates", "Customization", "Automation"],
                    "sequence_completion_rate": mock.random_float(0.55, 0.75)
                },
                "feature_stickiness": {
                    "highly_sticky": ["Dashboard (95%)", "Core Workflow (88%)", "Notifications (82%)"],
                    "moderately_sticky": ["Reports (65%)", "Analytics (58%)"],
                    "low_stickiness": ["Advanced Config (28%)", "API (15%)"]
                },
                "feature_abandonment": {
                    "abandoned_after_trial": ["Feature X (45%)", "Feature Y (38%)"],
                    "never_adopted": ["Feature Z (70%)"],
                    "abandonment_reasons": ["Too complex", "Unclear value", "Alternative solution"]
                },
                "power_user_features": {
                    "features": ["API", "Advanced Automation", "Custom Integrations"],
                    "power_user_identification": "10-15% of users account for 60% of advanced feature usage"
                },
                "feature_combination_patterns": {
                    "common_combos": [
                        ["Dashboard + Reports + Export"],
                        ["Collaboration + Notifications + Chat"],
                        ["Data Import + Transformation + Automation"]
                    ],
                    "combo_success_rate": "Users adopting feature combinations show 2.3x higher retention"
                }
            }

            # Communication patterns
            communication_patterns = {
                "email_engagement": {
                    "avg_open_rate": mock.random_float(0.35, 0.55),
                    "avg_click_rate": mock.random_float(0.08, 0.18),
                    "best_send_times": ["Tuesday 10am", "Thursday 2pm"],
                    "worst_send_times": ["Monday early morning", "Friday afternoon"],
                    "subject_line_patterns": "Action-oriented subjects perform 35% better",
                    "personalization_impact": "+42% engagement with personalized content"
                },
                "response_patterns": {
                    "avg_response_time_to_csm": f"{mock.random_int(2, 24)} hours",
                    "response_rate": mock.random_float(0.65, 0.88),
                    "preferred_channels": ["Email (60%)", "In-app (25%)", "Phone (15%)"],
                    "executive_vs_user_response": "Executives respond 2x faster than end users"
                },
                "proactive_vs_reactive": {
                    "proactive_engagement": mock.random_float(0.55, 0.75),
                    "reactive_engagement": mock.random_float(0.25, 0.45),
                    "pattern": "Customers with >60% proactive engagement show higher satisfaction"
                },
                "content_preferences": {
                    "preferred_formats": ["Short video (48%)", "Written guide (32%)", "Webinar (20%)"],
                    "preferred_topics": ["Best practices", "Use cases", "Product updates"],
                    "content_engagement_correlation": "Regular content consumers have 30% higher health scores"
                }
            }

            # Support patterns
            support_patterns = {
                "ticket_patterns": {
                    "avg_tickets_per_customer": mock.random_float(1.5, 4.5),
                    "peak_ticket_times": ["Monday mornings", "After product releases"],
                    "common_ticket_types": ["Configuration questions (35%)", "Bug reports (25%)", "How-to questions (40%)"],
                    "repeat_ticket_rate": mock.random_float(0.15, 0.35)
                },
                "resolution_patterns": {
                    "avg_resolution_time_hours": mock.random_float(6.0, 24.0),
                    "first_response_time_hours": mock.random_float(1.0, 4.0),
                    "self_service_resolution_rate": mock.random_float(0.35, 0.55),
                    "escalation_rate": mock.random_float(0.08, 0.18)
                },
                "satisfaction_patterns": {
                    "avg_csat_score": mock.random_float(4.2, 4.8),
                    "resolution_speed_impact": "Quick resolution (<4 hours) drives 25% higher CSAT",
                    "first_contact_resolution_rate": mock.random_float(0.60, 0.80)
                },
                "predictive_patterns": {
                    "ticket_volume_trends": "Declining ticket volume correlates with better health",
                    "support_to_churn_correlation": "3+ tickets in 30 days = 3x churn risk",
                    "proactive_support_impact": "Proactive outreach reduces ticket volume by 40%"
                }
            }

            # User personas based on behavior
            user_personas = [
                {
                    "persona_name": "Power User",
                    "percentage_of_base": mock.random_float(0.10, 0.20),
                    "behavioral_traits": [
                        "Daily active usage (7 days/week)",
                        "High feature adoption (80%+ features used)",
                        "Advanced feature usage",
                        "API/integration usage",
                        "Low support ticket volume",
                        "Weekend and after-hours activity"
                    ],
                    "engagement_characteristics": {
                        "avg_session_duration": f"{mock.random_int(30, 60)} minutes",
                        "sessions_per_week": mock.random_int(15, 25),
                        "features_used": mock.random_int(45, 70)
                    },
                    "value_to_business": "High - champions, references, expansion candidates",
                    "recommended_treatment": "Invest heavily, beta access, advisory board, recognition"
                },
                {
                    "persona_name": "Regular User",
                    "percentage_of_base": mock.random_float(0.50, 0.65),
                    "behavioral_traits": [
                        "Consistent usage (3-5 days/week)",
                        "Core feature adoption (60-80%)",
                        "Business hours only",
                        "Moderate support usage",
                        "Responsive to outreach"
                    ],
                    "engagement_characteristics": {
                        "avg_session_duration": f"{mock.random_int(15, 30)} minutes",
                        "sessions_per_week": mock.random_int(8, 15),
                        "features_used": mock.random_int(25, 45)
                    },
                    "value_to_business": "Medium-High - core customer base, stable revenue",
                    "recommended_treatment": "Standard engagement, growth opportunities, efficiency"
                },
                {
                    "persona_name": "Casual User",
                    "percentage_of_base": mock.random_float(0.20, 0.30),
                    "behavioral_traits": [
                        "Sporadic usage (1-2 days/week or less)",
                        "Limited feature adoption (30-50%)",
                        "Basic features only",
                        "Higher support needs",
                        "Low email engagement"
                    ],
                    "engagement_characteristics": {
                        "avg_session_duration": f"{mock.random_int(5, 15)} minutes",
                        "sessions_per_week": mock.random_int(2, 6),
                        "features_used": mock.random_int(10, 25)
                    },
                    "value_to_business": "Low-Medium - churn risk, activation opportunity",
                    "recommended_treatment": "Re-engagement campaigns, simplified onboarding, upgrade or consolidate"
                },
                {
                    "persona_name": "At-Risk Dormant",
                    "percentage_of_base": mock.random_float(0.05, 0.15),
                    "behavioral_traits": [
                        "No activity for 30+ days",
                        "Declining usage trend",
                        "Login but no action",
                        "Unresponsive to outreach",
                        "Possible executive turnover"
                    ],
                    "engagement_characteristics": {
                        "avg_session_duration": f"{mock.random_int(2, 8)} minutes",
                        "sessions_per_week": mock.random_int(0, 2),
                        "features_used": mock.random_int(3, 12)
                    },
                    "value_to_business": "High Risk - immediate intervention needed",
                    "recommended_treatment": "Urgent CSM intervention, executive escalation, win-back program"
                }
            ]

            # Success patterns (correlated with positive outcomes)
            success_patterns = {
                "early_adoption_velocity": {
                    "pattern": "Customers activating 5+ features in first 30 days show 80% higher retention",
                    "correlation_strength": mock.random_float(0.75, 0.90),
                    "actionable_insight": "Accelerate early feature adoption through guided onboarding"
                },
                "executive_engagement": {
                    "pattern": "Executive participation in QBRs correlates with 95%+ renewal rates",
                    "correlation_strength": mock.random_float(0.70, 0.88),
                    "actionable_insight": "Prioritize executive relationship building and engagement"
                },
                "consistent_usage": {
                    "pattern": "Daily active users (vs. weekly/monthly) have 3x lower churn rate",
                    "correlation_strength": mock.random_float(0.65, 0.85),
                    "actionable_insight": "Drive daily habit formation through notifications and workflows"
                },
                "integration_adoption": {
                    "pattern": "Customers with 2+ active integrations show 60% higher expansion rates",
                    "correlation_strength": mock.random_float(0.60, 0.80),
                    "actionable_insight": "Promote integration adoption as expansion prerequisite"
                },
                "community_participation": {
                    "pattern": "Community participants have 40% higher NPS and advocacy rates",
                    "correlation_strength": mock.random_float(0.55, 0.75),
                    "actionable_insight": "Foster customer community and peer learning"
                }
            }

            # Risk patterns (correlated with churn/downsell)
            risk_patterns = {
                "usage_decline": {
                    "pattern": "30%+ usage decline over 60 days predicts churn with 75% accuracy",
                    "correlation_strength": mock.random_float(0.70, 0.88),
                    "early_warning_threshold": "20% decline",
                    "actionable_insight": "Automated alert and immediate CSM intervention"
                },
                "support_escalation": {
                    "pattern": "3+ support tickets in 30 days increases churn risk 3x",
                    "correlation_strength": mock.random_float(0.65, 0.82),
                    "early_warning_threshold": "2 tickets in 30 days",
                    "actionable_insight": "Proactive CSM outreach after 2nd ticket"
                },
                "executive_turnover": {
                    "pattern": "Loss of executive sponsor predicts 50% churn increase",
                    "correlation_strength": mock.random_float(0.60, 0.78),
                    "early_warning_threshold": "Executive contact change",
                    "actionable_insight": "Rapid executive re-engagement within 14 days"
                },
                "feature_abandonment": {
                    "pattern": "Core feature abandonment (30+ days no use) signals disengagement",
                    "correlation_strength": mock.random_float(0.55, 0.75),
                    "early_warning_threshold": "14 days no core feature use",
                    "actionable_insight": "Feature re-onboarding campaign"
                },
                "communication_drop": {
                    "pattern": "Unresponsive to 3+ consecutive outreaches indicates disengagement",
                    "correlation_strength": mock.random_float(0.58, 0.76),
                    "early_warning_threshold": "2 consecutive non-responses",
                    "actionable_insight": "Escalate communication channel and intensity"
                }
            }

            # Anomaly detection
            anomalies = []
            if anomaly_detection:
                anomalies = [
                    {
                        "anomaly_id": "anom_001",
                        "anomaly_type": "usage_spike",
                        "description": "Unusual 300% increase in API calls for customer cs_abc123",
                        "detected_date": (datetime.now() - timedelta(days=mock.random_int(1, 14))).strftime("%Y-%m-%d"),
                        "severity": "medium",
                        "potential_causes": ["New integration deployment", "Automation testing", "Data migration"],
                        "recommended_action": "Monitor for errors, check-in with customer on new use case"
                    },
                    {
                        "anomaly_id": "anom_002",
                        "anomaly_type": "sudden_disengagement",
                        "description": "Power user went from daily usage to zero activity for 7 days",
                        "detected_date": (datetime.now() - timedelta(days=mock.random_int(1, 7))).strftime("%Y-%m-%d"),
                        "severity": "high",
                        "potential_causes": ["Vacation", "Internal system issues", "Early churn signal"],
                        "recommended_action": "Immediate outreach to understand situation"
                    },
                    {
                        "anomaly_id": "anom_003",
                        "anomaly_type": "feature_pattern_change",
                        "description": "Multiple customers stopped using Feature X simultaneously",
                        "detected_date": (datetime.now() - timedelta(days=mock.random_int(1, 5))).strftime("%Y-%m-%d"),
                        "severity": "high",
                        "potential_causes": ["Product bug", "Feature change", "Competing feature"],
                        "recommended_action": "Product team investigation required"
                    }
                ]

            # Pattern transitions across lifecycle
            pattern_transitions = {
                "onboarding_to_active": {
                    "typical_pattern_evolution": "Low usage frequency → Daily habit formation",
                    "key_transition_indicators": ["5+ consecutive days of usage", "Core features adopted", "Team collaboration active"],
                    "avg_transition_time_days": mock.random_int(30, 60),
                    "success_rate": mock.random_float(0.80, 0.92)
                },
                "active_to_power_user": {
                    "typical_pattern_evolution": "Regular usage → Advanced feature exploration → API/automation",
                    "key_transition_indicators": ["Advanced feature adoption", "Integration usage", "Weekend activity"],
                    "avg_transition_time_days": mock.random_int(90, 180),
                    "success_rate": mock.random_float(0.15, 0.25)
                },
                "active_to_at_risk": {
                    "typical_pattern_evolution": "Consistent usage → Declining frequency → Sporadic/dormant",
                    "key_transition_indicators": ["Usage decline >30%", "Support ticket increase", "Low email engagement"],
                    "avg_transition_time_days": mock.random_int(45, 90),
                    "intervention_window": "First 14-30 days of decline"
                },
                "at_risk_to_recovered": {
                    "typical_pattern_evolution": "Low engagement → CSM intervention → Increased usage → Stabilization",
                    "key_transition_indicators": ["Usage recovery", "Support resolution", "Executive re-engagement"],
                    "avg_transition_time_days": mock.random_int(30, 60),
                    "success_rate": mock.random_float(0.55, 0.75)
                }
            }

            # Predictive insights
            predictive_insights_data = {}
            if predictive_insights:
                predictive_insights_data = {
                    "churn_prediction_patterns": {
                        "high_accuracy_signals": [
                            "30-day usage decline >40% (85% prediction accuracy)",
                            "Zero activity for 21+ days (80% accuracy)",
                            "Support ticket escalation pattern (75% accuracy)"
                        ],
                        "lead_time": "Patterns typically appear 30-90 days before churn",
                        "intervention_effectiveness": "Early intervention (30+ days before churn) shows 65% save rate"
                    },
                    "expansion_prediction_patterns": {
                        "high_accuracy_signals": [
                            "API usage growth >50% (70% expansion prediction)",
                            "Executive engagement increase (65% accuracy)",
                            "User seat growth >20% (60% accuracy)"
                        ],
                        "lead_time": "Patterns typically appear 60-120 days before expansion",
                        "conversion_rate": "Proactive expansion discussion increases close rate by 40%"
                    },
                    "advocacy_prediction_patterns": {
                        "high_accuracy_signals": [
                            "Power user + high NPS (80% reference probability)",
                            "Community participation + executive engagement (75% accuracy)",
                            "Success story sharing (70% case study likelihood)"
                        ],
                        "optimal_timing": "Request references after major milestone achievement"
                    },
                    "pattern_based_segmentation": {
                        "insight": "Behavior-based segmentation outperforms firmographic segmentation by 35%",
                        "recommendation": "Incorporate engagement patterns into segmentation models"
                    }
                }

            # Engagement optimization opportunities
            engagement_optimization = [
                {
                    "opportunity": "Optimize outreach timing",
                    "current_state": "Outreach distributed evenly across week",
                    "opportunity_state": "Concentrate outreach during peak engagement windows (Tue-Thu, 9-11am)",
                    "potential_impact": "+25% engagement rate improvement",
                    "effort": "Low",
                    "priority": "High"
                },
                {
                    "opportunity": "Accelerate feature adoption sequence",
                    "current_state": "60-day average to core feature adoption",
                    "opportunity_state": "Guided onboarding reduces to 30-day average",
                    "potential_impact": "+15% retention rate, faster time-to-value",
                    "effort": "Medium",
                    "priority": "High"
                },
                {
                    "opportunity": "Early at-risk intervention",
                    "current_state": "Average intervention at 60 days of decline",
                    "opportunity_state": "Automated alert and intervention at 14 days",
                    "potential_impact": "+20% save rate, reduce churn by 12%",
                    "effort": "Medium",
                    "priority": "Critical"
                },
                {
                    "opportunity": "Power user recognition program",
                    "current_state": "No formal recognition",
                    "opportunity_state": "Automated identification and recognition of power users",
                    "potential_impact": "Increase advocacy, create expansion pipeline",
                    "effort": "Low",
                    "priority": "Medium"
                },
                {
                    "opportunity": "Personalized content delivery",
                    "current_state": "Generic content calendar",
                    "opportunity_state": "Pattern-based personalized content (persona, stage, behavior)",
                    "potential_impact": "+40% content engagement, improved satisfaction",
                    "effort": "High",
                    "priority": "Medium"
                }
            ]

            # Recommended actions
            recommended_actions = [
                "Implement automated alerts for top 5 risk patterns identified",
                "Optimize communication timing based on temporal patterns (focus on Tue-Thu mornings)",
                "Deploy pattern-based customer segmentation for personalized engagement",
                "Create power user recognition and advocacy program",
                "Accelerate feature adoption through guided, sequential onboarding",
                "Establish early warning system for usage decline (>20% drop over 30 days)",
                "Develop persona-specific playbooks based on behavioral segments",
                "Monitor and address anomalies within 48 hours of detection"
            ]

            # Construct results
            results = EngagementPatternResults(
                analysis_id=f"pattern_{int(datetime.now().timestamp())}",
                analysis_scope=scope_summary,
                customers_analyzed=customers_analyzed,
                identified_patterns=identified_patterns,
                temporal_patterns=temporal_patterns,
                feature_usage_patterns=feature_usage_patterns,
                communication_patterns=communication_patterns,
                support_patterns=support_patterns,
                user_personas=user_personas,
                success_patterns=success_patterns,
                risk_patterns=risk_patterns,
                anomalies=anomalies,
                pattern_transitions=pattern_transitions,
                predictive_insights=predictive_insights_data,
                engagement_optimization=engagement_optimization,
                recommended_actions=recommended_actions
            )

            ctx.info(f"Successfully analyzed engagement patterns: {len(identified_patterns)} patterns identified across {customers_analyzed} customers")
            return results.model_dump_json(indent=2)

        except ValidationError as e:
            ctx.error(f"Validation error in analyze_engagement_patterns: {str(e)}")
            raise
        except Exception as e:
            ctx.error(f"Error in analyze_engagement_patterns: {str(e)}")
            raise


    # ============================================================================
    # Export all tools
    # ============================================================================



__all__ = [
    'register_tools',
    'track_usage_engagement',
    'calculate_health_score',
    'segment_customers',
    'track_feature_adoption',
    'manage_lifecycle_stages',
    'track_adoption_milestones',
    'segment_by_value_tier',
    'analyze_engagement_patterns'
]

