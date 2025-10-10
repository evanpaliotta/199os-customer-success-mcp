"""
Renewal Models
Pydantic models for contract renewal and expansion processes
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from enum import Enum


class RenewalStatus(str, Enum):
    """Renewal opportunity status"""
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    HIGH_RISK = "high_risk"
    WON = "won"
    LOST = "lost"
    CHURNED = "churned"


class ExpansionType(str, Enum):
    """Types of expansion opportunities"""
    UPSELL = "upsell"              # Higher tier
    CROSS_SELL = "cross_sell"      # Additional products
    USER_EXPANSION = "user_expansion"  # More licenses
    USAGE_EXPANSION = "usage_expansion"  # Higher usage tier
    PROFESSIONAL_SERVICES = "professional_services"
    TRAINING = "training"


class ContractType(str, Enum):
    """Contract types"""
    ANNUAL = "annual"
    MULTI_YEAR = "multi_year"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class PaymentStatus(str, Enum):
    """Payment health status"""
    CURRENT = "current"
    OVERDUE = "overdue"
    PAYMENT_PLAN = "payment_plan"
    AT_RISK = "at_risk"


class RenewalForecast(BaseModel):
    """
    Renewal forecast for a customer contract.

    Predicts renewal likelihood with risk factors
    and recommended actions.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "forecast_id": "rnw_cs_1696800000_acme_2026q1",
            "client_id": "cs_1696800000_acme",
            "contract_id": "CNT-12345",
            "renewal_date": "2026-01-15",
            "current_arr": 72000.0,
            "forecasted_arr": 78000.0,
            "renewal_probability": 0.87,
            "renewal_status": "on_track",
            "confidence_score": 0.82,
            "health_score": 82,
            "risk_factors": [
                {"factor": "decreased_feature_usage", "severity": "low", "weight": 0.15}
            ],
            "positive_indicators": [
                {"indicator": "high_engagement", "strength": "high", "weight": 0.35},
                {"indicator": "executive_sponsorship", "strength": "high", "weight": 0.30}
            ],
            "expansion_probability": 0.64,
            "estimated_expansion_value": 18000.0,
            "days_until_renewal": 97,
            "last_csm_touchpoint": "2025-10-08",
            "next_scheduled_touchpoint": "2025-10-17",
            "recommended_actions": [
                "Schedule Executive Business Review for Q4",
                "Present expansion opportunities during renewal discussion",
                "Address feature usage decline through training"
            ],
            "forecast_created_at": "2025-10-10T09:00:00Z",
            "forecast_updated_at": "2025-10-10T09:00:00Z",
            "model_version": "v2.1.0"
        }
    })

    # Identification
    forecast_id: str = Field(
        ...,
        description="Unique forecast identifier",
        pattern=r"^rnw_[a-z0-9_]+$"
    )
    client_id: str = Field(
        ...,
        description="Customer identifier"
    )
    contract_id: str = Field(
        ...,
        description="Contract identifier"
    )

    # Renewal details
    renewal_date: date = Field(
        ...,
        description="Contract renewal date"
    )
    current_arr: float = Field(
        ...,
        description="Current annual recurring revenue",
        ge=0
    )
    forecasted_arr: float = Field(
        ...,
        description="Forecasted ARR at renewal (including expansion)",
        ge=0
    )

    # Prediction
    renewal_probability: float = Field(
        ...,
        description="Probability of renewal (0-1)",
        ge=0,
        le=1
    )
    renewal_status: RenewalStatus = Field(
        ...,
        description="Renewal risk status"
    )
    confidence_score: float = Field(
        ...,
        description="Confidence in forecast (0-1)",
        ge=0,
        le=1
    )
    health_score: int = Field(
        ...,
        description="Current customer health score (0-100)",
        ge=0,
        le=100
    )

    # Risk and opportunity factors
    risk_factors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Factors that increase churn risk"
    )
    positive_indicators: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Factors that support renewal"
    )

    # Expansion forecast
    expansion_probability: float = Field(
        default=0.0,
        description="Probability of expansion sale (0-1)",
        ge=0,
        le=1
    )
    estimated_expansion_value: float = Field(
        default=0.0,
        description="Estimated expansion ARR",
        ge=0
    )

    # Timeline
    days_until_renewal: int = Field(
        ...,
        description="Days until renewal date",
        ge=0
    )
    last_csm_touchpoint: Optional[date] = Field(
        None,
        description="Date of last CSM interaction"
    )
    next_scheduled_touchpoint: Optional[date] = Field(
        None,
        description="Next scheduled CSM interaction"
    )

    # Recommendations
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Recommended actions to secure renewal"
    )

    # Metadata
    forecast_created_at: datetime = Field(
        default_factory=datetime.now,
        description="Forecast creation timestamp"
    )
    forecast_updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last forecast update"
    )
    model_version: str = Field(
        default="v1.0.0",
        description="Forecasting model version"
    )


class ContractDetails(BaseModel):
    """
    Contract details for a customer.

    Comprehensive contract information including terms,
    value, and renewal tracking.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "contract_id": "CNT-12345",
            "client_id": "cs_1696800000_acme",
            "contract_type": "annual",
            "contract_value": 72000.0,
            "billing_frequency": "annual",
            "currency": "USD",
            "start_date": "2025-01-15",
            "end_date": "2026-01-15",
            "renewal_date": "2026-01-15",
            "auto_renew": True,
            "notice_period_days": 30,
            "payment_terms": "Net 30",
            "payment_status": "current",
            "included_users": 50,
            "included_usage": {"api_calls": 100000, "storage_gb": 100},
            "tier": "professional",
            "products_included": ["Core Platform", "Advanced Analytics", "API Access"],
            "addons": ["Premium Support"],
            "discount_percentage": 0.10,
            "discount_reason": "Annual commitment discount",
            "signed_by": "John Smith, VP of Operations",
            "owner_csm": "Sarah Johnson",
            "last_modified": "2025-10-10T09:00:00Z",
            "contract_url": "https://contracts.example.com/CNT-12345"
        }
    })

    # Identification
    contract_id: str = Field(
        ...,
        description="Unique contract identifier",
        pattern=r"^CNT-[0-9]+$"
    )
    client_id: str = Field(
        ...,
        description="Customer identifier"
    )

    # Contract type and value
    contract_type: ContractType = Field(
        ...,
        description="Contract duration type"
    )
    contract_value: float = Field(
        ...,
        description="Total contract value in contract period",
        ge=0
    )
    billing_frequency: str = Field(
        ...,
        description="Billing frequency (monthly, quarterly, annual)",
        pattern=r"^(monthly|quarterly|annual)$"
    )
    currency: str = Field(
        default="USD",
        description="Contract currency code",
        pattern=r"^[A-Z]{3}$"
    )

    # Dates
    start_date: date = Field(
        ...,
        description="Contract start date"
    )
    end_date: date = Field(
        ...,
        description="Contract end date"
    )
    renewal_date: date = Field(
        ...,
        description="Next renewal date"
    )
    auto_renew: bool = Field(
        default=False,
        description="Whether contract auto-renews"
    )
    notice_period_days: int = Field(
        default=30,
        description="Required notice period for cancellation (days)",
        ge=0
    )

    # Payment terms
    payment_terms: str = Field(
        ...,
        description="Payment terms (e.g., 'Net 30', 'Due on receipt')"
    )
    payment_status: PaymentStatus = Field(
        default=PaymentStatus.CURRENT,
        description="Current payment status"
    )

    # Entitlements
    included_users: Optional[int] = Field(
        None,
        description="Number of user licenses included",
        ge=0
    )
    included_usage: Dict[str, Any] = Field(
        default_factory=dict,
        description="Usage limits included in contract"
    )
    tier: str = Field(
        ...,
        description="Product tier (starter, standard, professional, enterprise)"
    )
    products_included: List[str] = Field(
        ...,
        description="Products included in contract",
        min_length=1
    )
    addons: List[str] = Field(
        default_factory=list,
        description="Add-ons and optional features"
    )

    # Pricing
    discount_percentage: float = Field(
        default=0.0,
        description="Applied discount percentage (0-1)",
        ge=0,
        le=1
    )
    discount_reason: Optional[str] = Field(
        None,
        description="Reason for discount"
    )

    # Ownership
    signed_by: Optional[str] = Field(
        None,
        description="Customer signatory name and title"
    )
    owner_csm: Optional[str] = Field(
        None,
        description="Assigned Customer Success Manager"
    )

    # Metadata
    last_modified: datetime = Field(
        default_factory=datetime.now,
        description="Last modification timestamp"
    )
    contract_url: Optional[str] = Field(
        None,
        description="URL to contract document"
    )

    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v: date, info) -> date:
        """Validate end date is after start date"""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('end_date must be after start_date')
        return v


class ExpansionOpportunity(BaseModel):
    """
    Revenue expansion opportunity for an existing customer.

    Identifies and tracks upsell, cross-sell, and expansion
    opportunities.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "opportunity_id": "EXP-67890",
            "client_id": "cs_1696800000_acme",
            "opportunity_name": "Enterprise Tier Upgrade",
            "expansion_type": "upsell",
            "estimated_value": 28000.0,
            "probability": 0.65,
            "confidence_score": 0.78,
            "expected_close_date": "2025-12-15",
            "current_stage": "qualification",
            "requirements": [
                "Advanced security features",
                "Custom integrations",
                "Dedicated support"
            ],
            "value_drivers": [
                "Growing team (50 -> 150 users)",
                "Enterprise security requirements",
                "Need for advanced analytics"
            ],
            "blockers": [
                "Budget approval required",
                "Security review pending"
            ],
            "champion": "John Smith, VP of Operations",
            "decision_makers": ["Jane Doe, CTO", "Bob Wilson, CFO"],
            "competitive_pressure": "low",
            "assigned_to": "Sarah Johnson",
            "next_action": "Schedule value assessment with CTO",
            "next_action_date": "2025-10-15",
            "created_at": "2025-10-01T10:00:00Z",
            "updated_at": "2025-10-10T09:00:00Z"
        }
    })

    # Identification
    opportunity_id: str = Field(
        ...,
        description="Unique opportunity identifier",
        pattern=r"^EXP-[0-9]+$"
    )
    client_id: str = Field(
        ...,
        description="Customer identifier"
    )
    opportunity_name: str = Field(
        ...,
        description="Opportunity name/description",
        min_length=1,
        max_length=200
    )
    expansion_type: ExpansionType = Field(
        ...,
        description="Type of expansion opportunity"
    )

    # Value and probability
    estimated_value: float = Field(
        ...,
        description="Estimated additional ARR from opportunity",
        ge=0
    )
    probability: float = Field(
        ...,
        description="Win probability (0-1)",
        ge=0,
        le=1
    )
    confidence_score: float = Field(
        default=0.5,
        description="Confidence in estimate (0-1)",
        ge=0,
        le=1
    )
    expected_close_date: Optional[date] = Field(
        None,
        description="Expected close date"
    )
    current_stage: str = Field(
        ...,
        description="Current opportunity stage (awareness, qualification, proposal, negotiation, closed)"
    )

    # Details
    requirements: List[str] = Field(
        default_factory=list,
        description="Customer requirements driving this opportunity"
    )
    value_drivers: List[str] = Field(
        default_factory=list,
        description="Key value drivers for this expansion"
    )
    blockers: List[str] = Field(
        default_factory=list,
        description="Current blockers or objections"
    )

    # Stakeholders
    champion: Optional[str] = Field(
        None,
        description="Internal champion at customer"
    )
    decision_makers: List[str] = Field(
        default_factory=list,
        description="Key decision makers"
    )
    competitive_pressure: str = Field(
        default="unknown",
        description="Competitive pressure (none, low, medium, high)",
        pattern=r"^(none|low|medium|high|unknown)$"
    )

    # Ownership and actions
    assigned_to: Optional[str] = Field(
        None,
        description="CSM or Account Executive assigned"
    )
    next_action: Optional[str] = Field(
        None,
        description="Next action to progress opportunity"
    )
    next_action_date: Optional[date] = Field(
        None,
        description="Date for next action"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Opportunity creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )


class RenewalCampaign(BaseModel):
    """
    Renewal campaign tracking for proactive renewal management.
    """
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "campaign_id": "CAMP-2026Q1",
            "campaign_name": "Q1 2026 Renewals",
            "start_date": "2025-10-01",
            "end_date": "2026-01-31",
            "target_renewal_date_range": {
                "start": "2026-01-01",
                "end": "2026-03-31"
            },
            "total_customers": 47,
            "total_arr_at_risk": 2840000.0,
            "customers_contacted": 42,
            "customers_committed": 28,
            "customers_at_risk": 8,
            "win_rate": 0.67,
            "expansion_opportunities_identified": 12,
            "expansion_value_identified": 485000.0,
            "campaign_activities": [
                "Renewal reminder emails (90, 60, 30 days)",
                "Executive Business Reviews",
                "Value assessment sessions",
                "Contract negotiation support"
            ],
            "success_metrics": {
                "renewal_rate_target": 0.92,
                "current_renewal_rate": 0.67,
                "expansion_rate_target": 0.25,
                "current_expansion_rate": 0.26
            }
        }
    })

    campaign_id: str = Field(..., description="Unique campaign identifier")
    campaign_name: str = Field(..., description="Campaign name")
    start_date: date = Field(..., description="Campaign start date")
    end_date: date = Field(..., description="Campaign end date")
    target_renewal_date_range: Dict[str, date] = Field(
        ...,
        description="Range of renewal dates targeted"
    )

    # Volume metrics
    total_customers: int = Field(..., description="Total customers in campaign", ge=0)
    total_arr_at_risk: float = Field(..., description="Total ARR in renewal cycle", ge=0)
    customers_contacted: int = Field(default=0, description="Customers contacted", ge=0)
    customers_committed: int = Field(default=0, description="Customers committed to renew", ge=0)
    customers_at_risk: int = Field(default=0, description="High-risk customers", ge=0)

    # Performance metrics
    win_rate: float = Field(
        default=0.0,
        description="Renewal win rate (committed / contacted)",
        ge=0,
        le=1
    )
    expansion_opportunities_identified: int = Field(
        default=0,
        description="Expansion opportunities identified",
        ge=0
    )
    expansion_value_identified: float = Field(
        default=0.0,
        description="Total expansion ARR identified",
        ge=0
    )

    # Campaign details
    campaign_activities: List[str] = Field(
        default_factory=list,
        description="Campaign activities and touchpoints"
    )
    success_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Campaign success metrics and targets"
    )


__all__ = [
    'RenewalStatus',
    'ExpansionType',
    'ContractType',
    'PaymentStatus',
    'RenewalForecast',
    'ContractDetails',
    'ExpansionOpportunity',
    'RenewalCampaign'
]
