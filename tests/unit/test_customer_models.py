"""
Unit Tests for Customer Models

Tests for all customer-related Pydantic models including enums, validators,
and calculated methods.
"""

import pytest
from datetime import datetime, date, timedelta
from pydantic import ValidationError

from src.models.customer_models import (
    CustomerTier, LifecycleStage, HealthTrend, AccountStatus,
    CustomerAccount, HealthScoreComponents, CustomerSegment,
    RiskIndicator, ChurnPrediction
)


# ============================================================================
# CustomerTier Enum Tests
# ============================================================================

@pytest.mark.unit
def test_customer_tier_enum_values():
    """Test that CustomerTier enum has all expected values."""
    assert CustomerTier.STARTER == "starter"
    assert CustomerTier.STANDARD == "standard"
    assert CustomerTier.PROFESSIONAL == "professional"
    assert CustomerTier.ENTERPRISE == "enterprise"


@pytest.mark.unit
def test_customer_tier_enum_count():
    """Test that CustomerTier has exactly 4 tiers."""
    assert len(list(CustomerTier)) == 4


# ============================================================================
# LifecycleStage Enum Tests
# ============================================================================

@pytest.mark.unit
def test_lifecycle_stage_enum_values():
    """Test that LifecycleStage enum has all expected values."""
    assert LifecycleStage.ONBOARDING == "onboarding"
    assert LifecycleStage.ACTIVE == "active"
    assert LifecycleStage.AT_RISK == "at_risk"
    assert LifecycleStage.CHURNED == "churned"
    assert LifecycleStage.EXPANSION == "expansion"
    assert LifecycleStage.RENEWAL == "renewal"


@pytest.mark.unit
def test_lifecycle_stage_enum_count():
    """Test that LifecycleStage has exactly 6 stages."""
    assert len(list(LifecycleStage)) == 6


# ============================================================================
# HealthTrend Enum Tests
# ============================================================================

@pytest.mark.unit
def test_health_trend_enum_values():
    """Test that HealthTrend enum has all expected values."""
    assert HealthTrend.IMPROVING == "improving"
    assert HealthTrend.STABLE == "stable"
    assert HealthTrend.DECLINING == "declining"


@pytest.mark.unit
def test_health_trend_enum_count():
    """Test that HealthTrend has exactly 3 trend directions."""
    assert len(list(HealthTrend)) == 3


# ============================================================================
# AccountStatus Enum Tests
# ============================================================================

@pytest.mark.unit
def test_account_status_enum_values():
    """Test that AccountStatus enum has all expected values."""
    assert AccountStatus.ACTIVE == "active"
    assert AccountStatus.PAUSED == "paused"
    assert AccountStatus.CHURNED == "churned"
    assert AccountStatus.PENDING == "pending"


@pytest.mark.unit
def test_account_status_enum_count():
    """Test that AccountStatus has exactly 4 statuses."""
    assert len(list(AccountStatus)) == 4


# ============================================================================
# CustomerAccount Model Tests
# ============================================================================

@pytest.mark.unit
def test_customer_account_valid_creation(sample_client_id):
    """Test creating a valid CustomerAccount with all required fields."""
    account = CustomerAccount(
        client_id=sample_client_id,
        client_name="Test Corporation",
        company_name="Test Corp Inc.",
        contract_start_date=date.today(),
        contract_end_date=date.today() + timedelta(days=365)
    )

    assert account.client_id == sample_client_id
    assert account.client_name == "Test Corporation"
    assert account.company_name == "Test Corp Inc."
    assert account.tier == CustomerTier.STANDARD  # Default
    assert account.lifecycle_stage == LifecycleStage.ONBOARDING  # Default
    assert account.health_score == 50  # Default
    assert account.status == AccountStatus.ACTIVE  # Default


@pytest.mark.unit
def test_customer_account_with_all_fields(sample_client_id):
    """Test creating CustomerAccount with all optional fields populated."""
    account = CustomerAccount(
        client_id=sample_client_id,
        client_name="Acme Corp",
        company_name="Acme Corporation Inc.",
        industry="Technology",
        tier=CustomerTier.ENTERPRISE,
        lifecycle_stage=LifecycleStage.ACTIVE,
        contract_value=100000.0,
        contract_start_date=date.today(),
        contract_end_date=date.today() + timedelta(days=365),
        renewal_date=date.today() + timedelta(days=365),
        primary_contact_email="john@acme.com",
        primary_contact_name="John Smith",
        csm_assigned="Sarah Johnson",
        health_score=85,
        health_trend=HealthTrend.IMPROVING,
        last_engagement_date=datetime.now(),
        status=AccountStatus.ACTIVE
    )

    assert account.tier == CustomerTier.ENTERPRISE
    assert account.lifecycle_stage == LifecycleStage.ACTIVE
    assert account.contract_value == 100000.0
    assert account.health_score == 85
    assert account.health_trend == HealthTrend.IMPROVING


@pytest.mark.unit
def test_customer_account_invalid_client_id():
    """Test that invalid client_id format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        CustomerAccount(
            client_id="invalid_id",  # Missing cs_ prefix
            client_name="Test",
            company_name="Test Inc.",
            contract_start_date=date.today()
        )

    assert "client_id" in str(exc_info.value)


@pytest.mark.unit
def test_customer_account_invalid_email():
    """Test that invalid email format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        CustomerAccount(
            client_id="cs_1234_test",
            client_name="Test",
            company_name="Test Inc.",
            contract_start_date=date.today(),
            primary_contact_email="invalid_email"  # Missing @
        )

    assert "primary_contact_email" in str(exc_info.value)


@pytest.mark.unit
def test_customer_account_health_score_min_boundary():
    """Test that health_score accepts minimum value of 0."""
    account = CustomerAccount(
        client_id="cs_1234_test",
        client_name="Test",
        company_name="Test Inc.",
        contract_start_date=date.today(),
        health_score=0
    )
    assert account.health_score == 0


@pytest.mark.unit
def test_customer_account_health_score_max_boundary():
    """Test that health_score accepts maximum value of 100."""
    account = CustomerAccount(
        client_id="cs_1234_test",
        client_name="Test",
        company_name="Test Inc.",
        contract_start_date=date.today(),
        health_score=100
    )
    assert account.health_score == 100


@pytest.mark.unit
def test_customer_account_health_score_below_min():
    """Test that health_score below 0 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        CustomerAccount(
            client_id="cs_1234_test",
            client_name="Test",
            company_name="Test Inc.",
            contract_start_date=date.today(),
            health_score=-1
        )

    assert "health_score" in str(exc_info.value)


@pytest.mark.unit
def test_customer_account_health_score_above_max():
    """Test that health_score above 100 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        CustomerAccount(
            client_id="cs_1234_test",
            client_name="Test",
            company_name="Test Inc.",
            contract_start_date=date.today(),
            health_score=101
        )

    assert "health_score" in str(exc_info.value)


@pytest.mark.unit
def test_customer_account_contract_end_before_start():
    """Test that contract_end_date before start_date raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        CustomerAccount(
            client_id="cs_1234_test",
            client_name="Test",
            company_name="Test Inc.",
            contract_start_date=date.today(),
            contract_end_date=date.today() - timedelta(days=1)
        )

    assert "contract_end_date must be after contract_start_date" in str(exc_info.value)


@pytest.mark.unit
def test_customer_account_contract_value_negative():
    """Test that negative contract_value raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        CustomerAccount(
            client_id="cs_1234_test",
            client_name="Test",
            company_name="Test Inc.",
            contract_start_date=date.today(),
            contract_value=-1000.0
        )

    assert "contract_value" in str(exc_info.value)


@pytest.mark.unit
def test_customer_account_default_timestamps():
    """Test that created_at and updated_at are auto-populated."""
    account = CustomerAccount(
        client_id="cs_1234_test",
        client_name="Test",
        company_name="Test Inc.",
        contract_start_date=date.today()
    )

    assert account.created_at is not None
    assert account.updated_at is not None
    assert isinstance(account.created_at, datetime)
    assert isinstance(account.updated_at, datetime)


@pytest.mark.unit
def test_customer_account_string_length_validation():
    """Test that string fields respect max_length constraints."""
    # Test client_name max_length (200)
    long_name = "A" * 201
    with pytest.raises(ValidationError) as exc_info:
        CustomerAccount(
            client_id="cs_1234_test",
            client_name=long_name,
            company_name="Test Inc.",
            contract_start_date=date.today()
        )

    assert "client_name" in str(exc_info.value)


# ============================================================================
# HealthScoreComponents Model Tests
# ============================================================================

@pytest.mark.unit
def test_health_score_components_valid_creation():
    """Test creating valid HealthScoreComponents with all scores."""
    components = HealthScoreComponents(
        usage_score=85.0,
        engagement_score=78.0,
        support_score=92.0,
        satisfaction_score=88.0,
        payment_score=100.0
    )

    assert components.usage_score == 85.0
    assert components.engagement_score == 78.0
    assert components.support_score == 92.0
    assert components.satisfaction_score == 88.0
    assert components.payment_score == 100.0


@pytest.mark.unit
def test_health_score_components_default_weights():
    """Test that default weights are correctly set."""
    components = HealthScoreComponents(
        usage_score=80.0,
        engagement_score=80.0,
        support_score=80.0,
        satisfaction_score=80.0,
        payment_score=80.0
    )

    assert components.usage_weight == 0.35
    assert components.engagement_weight == 0.25
    assert components.support_weight == 0.15
    assert components.satisfaction_weight == 0.15
    assert components.payment_weight == 0.10


@pytest.mark.unit
def test_health_score_components_custom_weights():
    """Test creating HealthScoreComponents with custom weights."""
    components = HealthScoreComponents(
        usage_score=80.0,
        engagement_score=80.0,
        support_score=80.0,
        satisfaction_score=80.0,
        payment_score=80.0,
        usage_weight=0.4,
        engagement_weight=0.3,
        support_weight=0.1,
        satisfaction_weight=0.1,
        payment_weight=0.1
    )

    assert components.usage_weight == 0.4
    assert components.engagement_weight == 0.3


@pytest.mark.unit
def test_health_score_components_weights_must_sum_to_one():
    """Test that weights must sum to 1.0."""
    with pytest.raises(ValidationError) as exc_info:
        HealthScoreComponents(
            usage_score=80.0,
            engagement_score=80.0,
            support_score=80.0,
            satisfaction_score=80.0,
            payment_score=80.0,
            usage_weight=0.5,
            engagement_weight=0.3,
            support_weight=0.1,
            satisfaction_weight=0.1,
            payment_weight=0.2  # Total = 1.2, should fail
        )

    assert "Weights must sum to 1.0" in str(exc_info.value)


@pytest.mark.unit
def test_health_score_components_score_boundaries():
    """Test that scores respect 0-100 boundaries."""
    # Test minimum
    components = HealthScoreComponents(
        usage_score=0.0,
        engagement_score=0.0,
        support_score=0.0,
        satisfaction_score=0.0,
        payment_score=0.0
    )
    assert components.usage_score == 0.0

    # Test maximum
    components = HealthScoreComponents(
        usage_score=100.0,
        engagement_score=100.0,
        support_score=100.0,
        satisfaction_score=100.0,
        payment_score=100.0
    )
    assert components.usage_score == 100.0


@pytest.mark.unit
def test_health_score_components_score_below_min():
    """Test that score below 0 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        HealthScoreComponents(
            usage_score=-1.0,
            engagement_score=80.0,
            support_score=80.0,
            satisfaction_score=80.0,
            payment_score=80.0
        )

    assert "usage_score" in str(exc_info.value)


@pytest.mark.unit
def test_health_score_components_score_above_max():
    """Test that score above 100 raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        HealthScoreComponents(
            usage_score=101.0,
            engagement_score=80.0,
            support_score=80.0,
            satisfaction_score=80.0,
            payment_score=80.0
        )

    assert "usage_score" in str(exc_info.value)


@pytest.mark.unit
def test_health_score_components_calculate_weighted_score():
    """Test the calculate_weighted_score method."""
    components = HealthScoreComponents(
        usage_score=80.0,
        engagement_score=70.0,
        support_score=90.0,
        satisfaction_score=85.0,
        payment_score=100.0,
        usage_weight=0.35,
        engagement_weight=0.25,
        support_weight=0.15,
        satisfaction_weight=0.15,
        payment_weight=0.10
    )

    weighted_score = components.calculate_weighted_score()

    expected = (80.0 * 0.35 + 70.0 * 0.25 + 90.0 * 0.15 + 85.0 * 0.15 + 100.0 * 0.10)
    assert abs(weighted_score - expected) < 0.01


@pytest.mark.unit
def test_health_score_components_calculate_weighted_score_all_perfect():
    """Test weighted score calculation with all perfect scores."""
    components = HealthScoreComponents(
        usage_score=100.0,
        engagement_score=100.0,
        support_score=100.0,
        satisfaction_score=100.0,
        payment_score=100.0
    )

    weighted_score = components.calculate_weighted_score()
    assert abs(weighted_score - 100.0) < 0.01


# ============================================================================
# CustomerSegment Model Tests
# ============================================================================

@pytest.mark.unit
def test_customer_segment_valid_creation():
    """Test creating a valid CustomerSegment."""
    segment = CustomerSegment(
        segment_id="seg_high_value",
        segment_name="High Value Accounts",
        segment_type="value_based",
        criteria={"min_arr": 50000}
    )

    assert segment.segment_id == "seg_high_value"
    assert segment.segment_name == "High Value Accounts"
    assert segment.segment_type == "value_based"
    assert segment.criteria == {"min_arr": 50000}


@pytest.mark.unit
def test_customer_segment_invalid_id_format():
    """Test that invalid segment_id format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        CustomerSegment(
            segment_id="invalid_id",  # Missing seg_ prefix
            segment_name="Test",
            segment_type="value",
            criteria={}
        )

    assert "segment_id" in str(exc_info.value)


@pytest.mark.unit
def test_customer_segment_with_all_fields():
    """Test CustomerSegment with all optional fields populated."""
    segment = CustomerSegment(
        segment_id="seg_enterprise",
        segment_name="Enterprise Customers",
        segment_type="tier_based",
        criteria={"tier": "enterprise"},
        characteristics={"team_size": "100+"},
        engagement_strategy={"frequency": "weekly"},
        success_metrics={"target_health": 90.0},
        customer_count=25,
        total_arr=5000000.0,
        avg_health_score=87.5
    )

    assert segment.customer_count == 25
    assert segment.total_arr == 5000000.0
    assert segment.avg_health_score == 87.5


@pytest.mark.unit
def test_customer_segment_default_values():
    """Test that CustomerSegment has correct default values."""
    segment = CustomerSegment(
        segment_id="seg_test",
        segment_name="Test",
        segment_type="test",
        criteria={}
    )

    assert segment.characteristics == {}
    assert segment.engagement_strategy == {}
    assert segment.success_metrics == {}
    assert segment.customer_count == 0
    assert segment.total_arr == 0.0
    assert segment.avg_health_score == 50.0


# ============================================================================
# RiskIndicator Model Tests
# ============================================================================

@pytest.mark.unit
def test_risk_indicator_valid_creation():
    """Test creating a valid RiskIndicator."""
    indicator = RiskIndicator(
        indicator_id="risk_001",
        indicator_name="Low Engagement",
        category="engagement",
        severity="high",
        current_value=2.5,
        threshold_value=5.0,
        description="User engagement below threshold"
    )

    assert indicator.indicator_id == "risk_001"
    assert indicator.severity == "high"
    assert indicator.current_value == 2.5
    assert indicator.threshold_value == 5.0


@pytest.mark.unit
def test_risk_indicator_severity_validation():
    """Test that severity must be one of allowed values."""
    # Valid severities
    for severity in ["low", "medium", "high", "critical"]:
        indicator = RiskIndicator(
            indicator_id="risk_001",
            indicator_name="Test",
            category="test",
            severity=severity,
            current_value=1.0,
            threshold_value=2.0,
            description="Test"
        )
        assert indicator.severity == severity

    # Invalid severity
    with pytest.raises(ValidationError) as exc_info:
        RiskIndicator(
            indicator_id="risk_001",
            indicator_name="Test",
            category="test",
            severity="invalid",
            current_value=1.0,
            threshold_value=2.0,
            description="Test"
        )

    assert "severity" in str(exc_info.value)


@pytest.mark.unit
def test_risk_indicator_default_timestamp():
    """Test that detected_at is auto-populated."""
    indicator = RiskIndicator(
        indicator_id="risk_001",
        indicator_name="Test",
        category="test",
        severity="low",
        current_value=1.0,
        threshold_value=2.0,
        description="Test"
    )

    assert indicator.detected_at is not None
    assert isinstance(indicator.detected_at, datetime)


@pytest.mark.unit
def test_risk_indicator_mitigation_actions():
    """Test that mitigation_actions list works correctly."""
    actions = ["Action 1", "Action 2", "Action 3"]
    indicator = RiskIndicator(
        indicator_id="risk_001",
        indicator_name="Test",
        category="test",
        severity="high",
        current_value=1.0,
        threshold_value=2.0,
        description="Test",
        mitigation_actions=actions
    )

    assert len(indicator.mitigation_actions) == 3
    assert indicator.mitigation_actions == actions


# ============================================================================
# ChurnPrediction Model Tests
# ============================================================================

@pytest.mark.unit
def test_churn_prediction_valid_creation(sample_client_id):
    """Test creating a valid ChurnPrediction."""
    prediction = ChurnPrediction(
        client_id=sample_client_id,
        churn_probability=0.35,
        churn_risk_level="medium",
        confidence_score=0.82
    )

    assert prediction.client_id == sample_client_id
    assert prediction.churn_probability == 0.35
    assert prediction.churn_risk_level == "medium"
    assert prediction.confidence_score == 0.82


@pytest.mark.unit
def test_churn_prediction_probability_boundaries():
    """Test that churn_probability respects 0-1 boundaries."""
    # Test minimum
    prediction = ChurnPrediction(
        client_id="cs_1234_test",
        churn_probability=0.0,
        churn_risk_level="low",
        confidence_score=0.9
    )
    assert prediction.churn_probability == 0.0

    # Test maximum
    prediction = ChurnPrediction(
        client_id="cs_1234_test",
        churn_probability=1.0,
        churn_risk_level="critical",
        confidence_score=0.9
    )
    assert prediction.churn_probability == 1.0

    # Test below minimum
    with pytest.raises(ValidationError) as exc_info:
        ChurnPrediction(
            client_id="cs_1234_test",
            churn_probability=-0.1,
            churn_risk_level="low",
            confidence_score=0.9
        )

    assert "churn_probability" in str(exc_info.value)


@pytest.mark.unit
def test_churn_prediction_risk_level_validation():
    """Test that churn_risk_level must be one of allowed values."""
    for risk_level in ["low", "medium", "high", "critical"]:
        prediction = ChurnPrediction(
            client_id="cs_1234_test",
            churn_probability=0.5,
            churn_risk_level=risk_level,
            confidence_score=0.8
        )
        assert prediction.churn_risk_level == risk_level

    # Invalid risk level
    with pytest.raises(ValidationError) as exc_info:
        ChurnPrediction(
            client_id="cs_1234_test",
            churn_probability=0.5,
            churn_risk_level="invalid",
            confidence_score=0.8
        )

    assert "churn_risk_level" in str(exc_info.value)


@pytest.mark.unit
def test_churn_prediction_with_risk_indicators(sample_client_id):
    """Test ChurnPrediction with nested RiskIndicator objects."""
    risk_indicators = [
        RiskIndicator(
            indicator_id="risk_001",
            indicator_name="Low Usage",
            category="usage",
            severity="high",
            current_value=10.0,
            threshold_value=50.0,
            description="Usage below threshold"
        ),
        RiskIndicator(
            indicator_id="risk_002",
            indicator_name="Low Satisfaction",
            category="satisfaction",
            severity="medium",
            current_value=3.0,
            threshold_value=4.5,
            description="CSAT below threshold"
        )
    ]

    prediction = ChurnPrediction(
        client_id=sample_client_id,
        churn_probability=0.65,
        churn_risk_level="high",
        confidence_score=0.85,
        risk_indicators=risk_indicators
    )

    assert len(prediction.risk_indicators) == 2
    assert prediction.risk_indicators[0].indicator_id == "risk_001"
    assert prediction.risk_indicators[1].severity == "medium"


@pytest.mark.unit
def test_churn_prediction_default_values(sample_client_id):
    """Test that ChurnPrediction has correct default values."""
    prediction = ChurnPrediction(
        client_id=sample_client_id,
        churn_probability=0.5,
        churn_risk_level="medium",
        confidence_score=0.8
    )

    assert prediction.contributing_factors == []
    assert prediction.risk_indicators == []
    assert prediction.retention_recommendations == []
    assert prediction.model_version == "v1.0.0"
    assert prediction.prediction_date is not None


@pytest.mark.unit
def test_churn_prediction_contributing_factors(sample_client_id):
    """Test ChurnPrediction with contributing factors."""
    factors = [
        {"factor": "decreased_usage", "weight": 0.4},
        {"factor": "low_engagement", "weight": 0.35},
        {"factor": "support_issues", "weight": 0.25}
    ]

    prediction = ChurnPrediction(
        client_id=sample_client_id,
        churn_probability=0.7,
        churn_risk_level="high",
        confidence_score=0.88,
        contributing_factors=factors
    )

    assert len(prediction.contributing_factors) == 3
    assert prediction.contributing_factors[0]["factor"] == "decreased_usage"
    assert prediction.contributing_factors[0]["weight"] == 0.4
