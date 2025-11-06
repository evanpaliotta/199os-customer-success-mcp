"""
Customer Models
Pydantic models for customer success core entities
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from enum import Enum


class CustomerTier(str, Enum):
    """Customer tier classification"""
    STARTER = "starter"
    STANDARD = "standard"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class LifecycleStage(str, Enum):
    """Customer lifecycle stages"""
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    AT_RISK = "at_risk"
    CHURNED = "churned"
    EXPANSION = "expansion"
    RENEWAL = "renewal"


class HealthTrend(str, Enum):
    """Health score trend directions"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class AccountStatus(str, Enum):
    """Customer account status"""
    ACTIVE = "active"
    PAUSED = "paused"
    CHURNED = "churned"
    PENDING = "pending"


class CustomerAccount(BaseModel):
    """
    Primary customer account model for CS operations.

    This model represents the core customer entity with contract details,
    health scoring, and engagement tracking.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
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
    })

    # Identification
    client_id: str = Field(
        ...,
        description="Unique client identifier (format: cs_{timestamp}_{name})",
        pattern=r"^cs_[0-9]+_[a-z0-9_]+$"
    )
    client_name: str = Field(
        ...,
        description="Customer account display name",
        min_length=1,
        max_length=200
    )
    company_name: str = Field(
        ...,
        description="Legal company name",
        min_length=1,
        max_length=200
    )
    industry: str = Field(
        default="Technology",
        description="Industry vertical or sector",
        max_length=100
    )

    # Classification
    tier: CustomerTier = Field(
        default=CustomerTier.STANDARD,
        description="Customer tier level determining service model"
    )
    lifecycle_stage: LifecycleStage = Field(
        default=LifecycleStage.ONBOARDING,
        description="Current stage in customer lifecycle"
    )

    # Contract details
    contract_value: float = Field(
        default=0.0,
        description="Annual recurring revenue (ARR) in USD",
        ge=0
    )
    contract_start_date: date = Field(
        ...,
        description="Contract start date"
    )
    contract_end_date: Optional[date] = Field(
        None,
        description="Contract end date (None for ongoing)"
    )
    renewal_date: Optional[date] = Field(
        None,
        description="Next renewal date"
    )

    # Contact information
    primary_contact_email: Optional[str] = Field(
        None,
        description="Primary customer contact email",
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    primary_contact_name: Optional[str] = Field(
        None,
        description="Primary customer contact name",
        max_length=200
    )
    csm_assigned: Optional[str] = Field(
        None,
        description="Assigned Customer Success Manager name",
        max_length=200
    )

    # Health and engagement
    health_score: int = Field(
        default=50,
        description="Overall customer health score (0-100)",
        ge=0,
        le=100
    )
    health_trend: HealthTrend = Field(
        default=HealthTrend.STABLE,
        description="Recent health score trend direction"
    )
    last_engagement_date: Optional[datetime] = Field(
        None,
        description="Timestamp of last customer engagement"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Account creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )
    status: AccountStatus = Field(
        default=AccountStatus.ACTIVE,
        description="Current account status"
    )

    @field_validator('contract_end_date')
    @classmethod
    def validate_contract_end_date(cls, v: Optional[date], info) -> Optional[date]:
        """Validate contract end date is after start date"""
        if v is not None and 'contract_start_date' in info.data:
            if v <= info.data['contract_start_date']:
                raise ValueError('contract_end_date must be after contract_start_date')
        return v


class HealthScoreComponents(BaseModel):
    """
    Health score breakdown by component with configurable weights.

    This model allows for detailed health score calculation with
    customizable weights for different business models.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "usage_score": 85.0,
            "engagement_score": 78.0,
            "support_score": 92.0,
            "satisfaction_score": 88.0,
            "payment_score": 100.0,
            "usage_weight": 0.35,
            "engagement_weight": 0.25,
            "support_weight": 0.15,
            "satisfaction_weight": 0.15,
            "payment_weight": 0.10
        }
    })

    # Component scores
    usage_score: float = Field(
        ...,
        description="Product usage score (0-100)",
        ge=0,
        le=100
    )
    engagement_score: float = Field(
        ...,
        description="Customer engagement score (0-100)",
        ge=0,
        le=100
    )
    support_score: float = Field(
        ...,
        description="Support experience score (0-100)",
        ge=0,
        le=100
    )
    satisfaction_score: float = Field(
        ...,
        description="Customer satisfaction score (0-100)",
        ge=0,
        le=100
    )
    payment_score: float = Field(
        ...,
        description="Payment and billing health score (0-100)",
        ge=0,
        le=100
    )

    # Weights (must sum to 1.0)
    usage_weight: float = Field(
        default=0.35,
        description="Weight for usage score component",
        ge=0,
        le=1
    )
    engagement_weight: float = Field(
        default=0.25,
        description="Weight for engagement score component",
        ge=0,
        le=1
    )
    support_weight: float = Field(
        default=0.15,
        description="Weight for support score component",
        ge=0,
        le=1
    )
    satisfaction_weight: float = Field(
        default=0.15,
        description="Weight for satisfaction score component",
        ge=0,
        le=1
    )
    payment_weight: float = Field(
        default=0.10,
        description="Weight for payment score component",
        ge=0,
        le=1
    )

    @field_validator('payment_weight')
    @classmethod
    def validate_weights_sum(cls, v: float, info) -> float:
        """Validate that all weights sum to 1.0"""
        weights = [
            info.data.get('usage_weight', 0),
            info.data.get('engagement_weight', 0),
            info.data.get('support_weight', 0),
            info.data.get('satisfaction_weight', 0),
            v
        ]
        total = sum(weights)
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            raise ValueError(f'Weights must sum to 1.0, got {total:.3f}')
        return v

    def calculate_weighted_score(self) -> float:
        """
        Calculate weighted health score from components.

        Returns:
            float: Weighted health score (0-100)
        """
        return (
            self.usage_score * self.usage_weight +
            self.engagement_score * self.engagement_weight +
            self.support_score * self.support_weight +
            self.satisfaction_score * self.satisfaction_weight +
            self.payment_score * self.payment_weight
        )


class CustomerSegment(BaseModel):
    """
    Customer segmentation data for targeted engagement.

    Enables multi-dimensional segmentation for personalized
    customer success strategies.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
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
            "success_metrics": {
                "target_health_score": 85,
                "target_nps": 50,
                "target_retention_rate": 0.95
            },
            "customer_count": 47,
            "total_arr": 4235000.0,
            "avg_health_score": 82.3
        }
    })

    segment_id: str = Field(
        ...,
        description="Unique segment identifier",
        pattern=r"^seg_[a-z0-9_]+$"
    )
    segment_name: str = Field(
        ...,
        description="Human-readable segment name",
        min_length=1,
        max_length=200
    )
    segment_type: str = Field(
        ...,
        description="Segmentation type (value_based, usage_based, industry, etc.)",
        max_length=50
    )
    criteria: Dict[str, Any] = Field(
        ...,
        description="Segmentation criteria and rules"
    )
    characteristics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Common characteristics of segment members"
    )
    engagement_strategy: Dict[str, Any] = Field(
        default_factory=dict,
        description="Recommended engagement approach for this segment"
    )
    success_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Target success metrics for this segment"
    )
    customer_count: int = Field(
        default=0,
        description="Number of customers in this segment",
        ge=0
    )
    total_arr: float = Field(
        default=0.0,
        description="Total ARR represented by this segment",
        ge=0
    )
    avg_health_score: float = Field(
        default=50.0,
        description="Average health score for segment",
        ge=0,
        le=100
    )


class RiskIndicator(BaseModel):
    """
    Individual risk indicator for churn prediction.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "indicator_id": "risk_low_engagement",
            "indicator_name": "Low Product Engagement",
            "category": "engagement",
            "severity": "high",
            "current_value": 2.3,
            "threshold_value": 5.0,
            "description": "Weekly active users below threshold",
            "detected_at": "2025-10-10T09:00:00Z",
            "mitigation_actions": [
                "Schedule check-in call",
                "Provide training resources",
                "Activate engagement campaign"
            ]
        }
    })

    indicator_id: str = Field(
        ...,
        description="Unique risk indicator identifier"
    )
    indicator_name: str = Field(
        ...,
        description="Human-readable indicator name"
    )
    category: str = Field(
        ...,
        description="Risk category (usage, engagement, support, payment, etc.)"
    )
    severity: str = Field(
        ...,
        description="Risk severity level (low, medium, high, critical)",
        pattern=r"^(low|medium|high|critical)$"
    )
    current_value: float = Field(
        ...,
        description="Current measured value"
    )
    threshold_value: float = Field(
        ...,
        description="Threshold value that triggered the indicator"
    )
    description: str = Field(
        ...,
        description="Detailed description of the risk"
    )
    detected_at: datetime = Field(
        default_factory=datetime.now,
        description="When the risk was detected"
    )
    mitigation_actions: List[str] = Field(
        default_factory=list,
        description="Recommended mitigation actions"
    )


class ChurnPrediction(BaseModel):
    """
    Churn prediction model output for a customer.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "client_id": "cs_1696800000_acme",
            "prediction_date": "2025-10-10T09:00:00Z",
            "churn_probability": 0.23,
            "churn_risk_level": "low",
            "confidence_score": 0.87,
            "contributing_factors": [
                {"factor": "decreased_login_frequency", "weight": 0.35},
                {"factor": "support_ticket_volume_increase", "weight": 0.25},
                {"factor": "feature_adoption_decline", "weight": 0.20}
            ],
            "risk_indicators": [],
            "predicted_churn_date": "2026-01-15",
            "retention_recommendations": [
                "Increase CSM touchpoints to weekly",
                "Provide advanced feature training",
                "Address support ticket backlog"
            ],
            "model_version": "v2.3.1"
        }
    })

    client_id: str = Field(
        ...,
        description="Customer identifier"
    )
    prediction_date: datetime = Field(
        default_factory=datetime.now,
        description="When prediction was generated"
    )
    churn_probability: float = Field(
        ...,
        description="Probability of churn (0-1)",
        ge=0,
        le=1
    )
    churn_risk_level: str = Field(
        ...,
        description="Risk level classification (low, medium, high, critical)",
        pattern=r"^(low|medium|high|critical)$"
    )
    confidence_score: float = Field(
        ...,
        description="Model confidence in prediction (0-1)",
        ge=0,
        le=1
    )
    contributing_factors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Factors contributing to churn risk with weights"
    )
    risk_indicators: List[RiskIndicator] = Field(
        default_factory=list,
        description="Detected risk indicators"
    )
    predicted_churn_date: Optional[date] = Field(
        None,
        description="Estimated churn date if risk not mitigated"
    )
    retention_recommendations: List[str] = Field(
        default_factory=list,
        description="Recommended retention actions"
    )
    model_version: str = Field(
        default="v1.0.0",
        description="Prediction model version"
    )


__all__ = [
    'CustomerTier',
    'LifecycleStage',
    'HealthTrend',
    'AccountStatus',
    'CustomerAccount',
    'HealthScoreComponents',
    'CustomerSegment',
    'RiskIndicator',
    'ChurnPrediction'
]
