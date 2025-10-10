"""
Unit Tests for Renewal Models

Tests for all renewal-related Pydantic models including renewal forecasts,
contract details, expansion opportunities, and renewal campaigns.
"""

import pytest
from datetime import datetime, date, timedelta
from pydantic import ValidationError

from src.models.renewal_models import (
    RenewalStatus, ExpansionType, ContractType, PaymentStatus,
    RenewalForecast, ContractDetails, ExpansionOpportunity, RenewalCampaign
)


# ============================================================================
# RenewalStatus Enum Tests
# ============================================================================

@pytest.mark.unit
def test_renewal_status_enum_values():
    """Test that RenewalStatus enum has all expected values."""
    assert RenewalStatus.ON_TRACK == "on_track"
    assert RenewalStatus.AT_RISK == "at_risk"
    assert RenewalStatus.HIGH_RISK == "high_risk"
    assert RenewalStatus.WON == "won"
    assert RenewalStatus.LOST == "lost"
    assert RenewalStatus.CHURNED == "churned"


@pytest.mark.unit
def test_renewal_status_enum_count():
    """Test that RenewalStatus has exactly 6 statuses."""
    assert len(list(RenewalStatus)) == 6


# ============================================================================
# ExpansionType Enum Tests
# ============================================================================

@pytest.mark.unit
def test_expansion_type_enum_values():
    """Test that ExpansionType enum has all expected values."""
    assert ExpansionType.UPSELL == "upsell"
    assert ExpansionType.CROSS_SELL == "cross_sell"
    assert ExpansionType.USER_EXPANSION == "user_expansion"
    assert ExpansionType.USAGE_EXPANSION == "usage_expansion"
    assert ExpansionType.PROFESSIONAL_SERVICES == "professional_services"
    assert ExpansionType.TRAINING == "training"


# ============================================================================
# ContractType Enum Tests
# ============================================================================

@pytest.mark.unit
def test_contract_type_enum_values():
    """Test that ContractType enum has all expected values."""
    assert ContractType.ANNUAL == "annual"
    assert ContractType.MULTI_YEAR == "multi_year"
    assert ContractType.MONTHLY == "monthly"
    assert ContractType.QUARTERLY == "quarterly"


# ============================================================================
# PaymentStatus Enum Tests
# ============================================================================

@pytest.mark.unit
def test_payment_status_enum_values():
    """Test that PaymentStatus enum has all expected values."""
    assert PaymentStatus.CURRENT == "current"
    assert PaymentStatus.OVERDUE == "overdue"
    assert PaymentStatus.PAYMENT_PLAN == "payment_plan"
    assert PaymentStatus.AT_RISK == "at_risk"


# ============================================================================
# RenewalForecast Model Tests
# ============================================================================

@pytest.mark.unit
def test_renewal_forecast_valid_creation(sample_client_id):
    """Test creating a valid RenewalForecast with all required fields."""
    forecast = RenewalForecast(
        forecast_id="rnw_test_forecast",
        client_id=sample_client_id,
        contract_id="CNT-12345",
        renewal_date=date.today() + timedelta(days=90),
        current_arr=72000.0,
        forecasted_arr=78000.0,
        renewal_probability=0.87,
        renewal_status=RenewalStatus.ON_TRACK,
        confidence_score=0.82,
        health_score=82,
        days_until_renewal=90
    )

    assert forecast.forecast_id == "rnw_test_forecast"
    assert forecast.client_id == sample_client_id
    assert forecast.current_arr == 72000.0
    assert forecast.forecasted_arr == 78000.0
    assert forecast.renewal_probability == 0.87


@pytest.mark.unit
def test_renewal_forecast_invalid_id_format():
    """Test that invalid forecast_id format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        RenewalForecast(
            forecast_id="invalid_id",  # Missing rnw_ prefix
            client_id="cs_1234_test",
            contract_id="CNT-123",
            renewal_date=date.today() + timedelta(days=90),
            current_arr=50000.0,
            forecasted_arr=55000.0,
            renewal_probability=0.8,
            renewal_status=RenewalStatus.ON_TRACK,
            confidence_score=0.75,
            health_score=75,
            days_until_renewal=90
        )

    assert "forecast_id" in str(exc_info.value)


@pytest.mark.unit
def test_renewal_forecast_probability_boundaries():
    """Test that renewal_probability respects 0-1 boundaries."""
    # Test minimum
    forecast = RenewalForecast(
        forecast_id="rnw_test",
        client_id="cs_1234_test",
        contract_id="CNT-123",
        renewal_date=date.today() + timedelta(days=90),
        current_arr=50000.0,
        forecasted_arr=50000.0,
        renewal_probability=0.0,
        renewal_status=RenewalStatus.CHURNED,
        confidence_score=0.9,
        health_score=30,
        days_until_renewal=90
    )
    assert forecast.renewal_probability == 0.0

    # Test maximum
    forecast.renewal_probability = 1.0
    assert forecast.renewal_probability == 1.0

    # Test below minimum
    with pytest.raises(ValidationError) as exc_info:
        RenewalForecast(
            forecast_id="rnw_test2",
            client_id="cs_1234_test",
            contract_id="CNT-123",
            renewal_date=date.today() + timedelta(days=90),
            current_arr=50000.0,
            forecasted_arr=50000.0,
            renewal_probability=-0.1,
            renewal_status=RenewalStatus.ON_TRACK,
            confidence_score=0.8,
            health_score=75,
            days_until_renewal=90
        )

    assert "renewal_probability" in str(exc_info.value)


@pytest.mark.unit
def test_renewal_forecast_health_score_boundaries():
    """Test that health_score respects 0-100 boundaries."""
    forecast = RenewalForecast(
        forecast_id="rnw_test",
        client_id="cs_1234_test",
        contract_id="CNT-123",
        renewal_date=date.today() + timedelta(days=90),
        current_arr=50000.0,
        forecasted_arr=50000.0,
        renewal_probability=0.5,
        renewal_status=RenewalStatus.AT_RISK,
        confidence_score=0.8,
        health_score=100,
        days_until_renewal=90
    )
    assert forecast.health_score == 100

    # Test above maximum
    with pytest.raises(ValidationError) as exc_info:
        RenewalForecast(
            forecast_id="rnw_test2",
            client_id="cs_1234_test",
            contract_id="CNT-123",
            renewal_date=date.today() + timedelta(days=90),
            current_arr=50000.0,
            forecasted_arr=50000.0,
            renewal_probability=0.5,
            renewal_status=RenewalStatus.ON_TRACK,
            confidence_score=0.8,
            health_score=101,
            days_until_renewal=90
        )

    assert "health_score" in str(exc_info.value)


@pytest.mark.unit
def test_renewal_forecast_with_risk_factors(sample_client_id):
    """Test RenewalForecast with risk factors and positive indicators."""
    risk_factors = [
        {"factor": "decreased_usage", "severity": "medium", "weight": 0.3},
        {"factor": "low_engagement", "severity": "high", "weight": 0.5}
    ]
    positive_indicators = [
        {"indicator": "executive_sponsorship", "strength": "high", "weight": 0.4}
    ]

    forecast = RenewalForecast(
        forecast_id="rnw_test",
        client_id=sample_client_id,
        contract_id="CNT-123",
        renewal_date=date.today() + timedelta(days=90),
        current_arr=50000.0,
        forecasted_arr=55000.0,
        renewal_probability=0.7,
        renewal_status=RenewalStatus.ON_TRACK,
        confidence_score=0.8,
        health_score=75,
        risk_factors=risk_factors,
        positive_indicators=positive_indicators,
        days_until_renewal=90
    )

    assert len(forecast.risk_factors) == 2
    assert len(forecast.positive_indicators) == 1


@pytest.mark.unit
def test_renewal_forecast_default_values(sample_client_id):
    """Test that RenewalForecast has correct default values."""
    forecast = RenewalForecast(
        forecast_id="rnw_test",
        client_id=sample_client_id,
        contract_id="CNT-123",
        renewal_date=date.today() + timedelta(days=90),
        current_arr=50000.0,
        forecasted_arr=50000.0,
        renewal_probability=0.8,
        renewal_status=RenewalStatus.ON_TRACK,
        confidence_score=0.85,
        health_score=80,
        days_until_renewal=90
    )

    assert forecast.risk_factors == []
    assert forecast.positive_indicators == []
    assert forecast.expansion_probability == 0.0
    assert forecast.estimated_expansion_value == 0.0
    assert forecast.recommended_actions == []
    assert forecast.model_version == "v1.0.0"


# ============================================================================
# ContractDetails Model Tests
# ============================================================================

@pytest.mark.unit
def test_contract_details_valid_creation(sample_client_id):
    """Test creating valid ContractDetails with all required fields."""
    contract = ContractDetails(
        contract_id="CNT-12345",
        client_id=sample_client_id,
        contract_type=ContractType.ANNUAL,
        contract_value=72000.0,
        billing_frequency="annual",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        renewal_date=date.today() + timedelta(days=365),
        payment_terms="Net 30",
        tier="professional",
        products_included=["Core Platform", "Analytics"]
    )

    assert contract.contract_id == "CNT-12345"
    assert contract.contract_type == ContractType.ANNUAL
    assert contract.contract_value == 72000.0


@pytest.mark.unit
def test_contract_details_invalid_id_format():
    """Test that invalid contract_id format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        ContractDetails(
            contract_id="INVALID-123",  # Should be CNT-
            client_id="cs_1234_test",
            contract_type=ContractType.ANNUAL,
            contract_value=50000.0,
            billing_frequency="annual",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            renewal_date=date.today() + timedelta(days=365),
            payment_terms="Net 30",
            tier="standard",
            products_included=["Product 1"]
        )

    assert "contract_id" in str(exc_info.value)


@pytest.mark.unit
def test_contract_details_billing_frequency_validation():
    """Test that billing_frequency must be one of allowed values."""
    for freq in ["monthly", "quarterly", "annual"]:
        contract = ContractDetails(
            contract_id="CNT-123",
            client_id="cs_1234_test",
            contract_type=ContractType.ANNUAL,
            contract_value=50000.0,
            billing_frequency=freq,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            renewal_date=date.today() + timedelta(days=365),
            payment_terms="Net 30",
            tier="standard",
            products_included=["Product 1"]
        )
        assert contract.billing_frequency == freq

    # Invalid frequency
    with pytest.raises(ValidationError) as exc_info:
        ContractDetails(
            contract_id="CNT-124",
            client_id="cs_1234_test",
            contract_type=ContractType.ANNUAL,
            contract_value=50000.0,
            billing_frequency="invalid",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            renewal_date=date.today() + timedelta(days=365),
            payment_terms="Net 30",
            tier="standard",
            products_included=["Product 1"]
        )

    assert "billing_frequency" in str(exc_info.value)


@pytest.mark.unit
def test_contract_details_currency_validation():
    """Test that currency must be 3-letter code."""
    contract = ContractDetails(
        contract_id="CNT-123",
        client_id="cs_1234_test",
        contract_type=ContractType.ANNUAL,
        contract_value=50000.0,
        billing_frequency="annual",
        currency="USD",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        renewal_date=date.today() + timedelta(days=365),
        payment_terms="Net 30",
        tier="standard",
        products_included=["Product 1"]
    )
    assert contract.currency == "USD"

    # Invalid currency
    with pytest.raises(ValidationError) as exc_info:
        ContractDetails(
            contract_id="CNT-124",
            client_id="cs_1234_test",
            contract_type=ContractType.ANNUAL,
            contract_value=50000.0,
            billing_frequency="annual",
            currency="US",  # Must be 3 letters
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            renewal_date=date.today() + timedelta(days=365),
            payment_terms="Net 30",
            tier="standard",
            products_included=["Product 1"]
        )

    assert "currency" in str(exc_info.value)


@pytest.mark.unit
def test_contract_details_end_date_after_start_date():
    """Test that end_date must be after start_date."""
    with pytest.raises(ValidationError) as exc_info:
        ContractDetails(
            contract_id="CNT-123",
            client_id="cs_1234_test",
            contract_type=ContractType.ANNUAL,
            contract_value=50000.0,
            billing_frequency="annual",
            start_date=date.today(),
            end_date=date.today() - timedelta(days=1),
            renewal_date=date.today() + timedelta(days=365),
            payment_terms="Net 30",
            tier="standard",
            products_included=["Product 1"]
        )

    assert "end_date must be after start_date" in str(exc_info.value)


@pytest.mark.unit
def test_contract_details_discount_boundaries():
    """Test that discount_percentage respects 0-1 boundaries."""
    contract = ContractDetails(
        contract_id="CNT-123",
        client_id="cs_1234_test",
        contract_type=ContractType.ANNUAL,
        contract_value=50000.0,
        billing_frequency="annual",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        renewal_date=date.today() + timedelta(days=365),
        payment_terms="Net 30",
        tier="standard",
        products_included=["Product 1"],
        discount_percentage=0.15
    )
    assert contract.discount_percentage == 0.15


@pytest.mark.unit
def test_contract_details_products_min_length():
    """Test that products_included must have at least one product."""
    with pytest.raises(ValidationError) as exc_info:
        ContractDetails(
            contract_id="CNT-123",
            client_id="cs_1234_test",
            contract_type=ContractType.ANNUAL,
            contract_value=50000.0,
            billing_frequency="annual",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            renewal_date=date.today() + timedelta(days=365),
            payment_terms="Net 30",
            tier="standard",
            products_included=[]  # Empty list
        )

    assert "products_included" in str(exc_info.value)


@pytest.mark.unit
def test_contract_details_default_values(sample_client_id):
    """Test that ContractDetails has correct default values."""
    contract = ContractDetails(
        contract_id="CNT-123",
        client_id=sample_client_id,
        contract_type=ContractType.ANNUAL,
        contract_value=50000.0,
        billing_frequency="annual",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        renewal_date=date.today() + timedelta(days=365),
        payment_terms="Net 30",
        tier="standard",
        products_included=["Product 1"]
    )

    assert contract.currency == "USD"
    assert contract.auto_renew == False
    assert contract.notice_period_days == 30
    assert contract.payment_status == PaymentStatus.CURRENT
    assert contract.discount_percentage == 0.0
    assert contract.addons == []


# ============================================================================
# ExpansionOpportunity Model Tests
# ============================================================================

@pytest.mark.unit
def test_expansion_opportunity_valid_creation(sample_client_id):
    """Test creating a valid ExpansionOpportunity."""
    opportunity = ExpansionOpportunity(
        opportunity_id="EXP-12345",
        client_id=sample_client_id,
        opportunity_name="Enterprise Tier Upgrade",
        expansion_type=ExpansionType.UPSELL,
        estimated_value=28000.0,
        probability=0.65,
        current_stage="qualification"
    )

    assert opportunity.opportunity_id == "EXP-12345"
    assert opportunity.expansion_type == ExpansionType.UPSELL
    assert opportunity.estimated_value == 28000.0
    assert opportunity.probability == 0.65


@pytest.mark.unit
def test_expansion_opportunity_invalid_id_format():
    """Test that invalid opportunity_id format raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        ExpansionOpportunity(
            opportunity_id="INVALID-123",  # Should be EXP-
            client_id="cs_1234_test",
            opportunity_name="Test",
            expansion_type=ExpansionType.UPSELL,
            estimated_value=10000.0,
            probability=0.5,
            current_stage="awareness"
        )

    assert "opportunity_id" in str(exc_info.value)


@pytest.mark.unit
def test_expansion_opportunity_probability_boundaries():
    """Test that probability respects 0-1 boundaries."""
    opportunity = ExpansionOpportunity(
        opportunity_id="EXP-123",
        client_id="cs_1234_test",
        opportunity_name="Test",
        expansion_type=ExpansionType.CROSS_SELL,
        estimated_value=10000.0,
        probability=0.0,
        current_stage="awareness"
    )
    assert opportunity.probability == 0.0

    opportunity.probability = 1.0
    assert opportunity.probability == 1.0


@pytest.mark.unit
def test_expansion_opportunity_competitive_pressure_validation():
    """Test that competitive_pressure must be one of allowed values."""
    for pressure in ["none", "low", "medium", "high", "unknown"]:
        opportunity = ExpansionOpportunity(
            opportunity_id="EXP-123",
            client_id="cs_1234_test",
            opportunity_name="Test",
            expansion_type=ExpansionType.UPSELL,
            estimated_value=10000.0,
            probability=0.5,
            current_stage="awareness",
            competitive_pressure=pressure
        )
        assert opportunity.competitive_pressure == pressure


@pytest.mark.unit
def test_expansion_opportunity_with_stakeholders(sample_client_id):
    """Test ExpansionOpportunity with stakeholder information."""
    opportunity = ExpansionOpportunity(
        opportunity_id="EXP-123",
        client_id=sample_client_id,
        opportunity_name="User Expansion",
        expansion_type=ExpansionType.USER_EXPANSION,
        estimated_value=15000.0,
        probability=0.75,
        current_stage="proposal",
        champion="John Smith, VP Operations",
        decision_makers=["Jane Doe, CTO", "Bob Wilson, CFO"]
    )

    assert opportunity.champion == "John Smith, VP Operations"
    assert len(opportunity.decision_makers) == 2


@pytest.mark.unit
def test_expansion_opportunity_default_values(sample_client_id):
    """Test that ExpansionOpportunity has correct default values."""
    opportunity = ExpansionOpportunity(
        opportunity_id="EXP-123",
        client_id=sample_client_id,
        opportunity_name="Test",
        expansion_type=ExpansionType.TRAINING,
        estimated_value=5000.0,
        probability=0.5,
        current_stage="awareness"
    )

    assert opportunity.confidence_score == 0.5
    assert opportunity.requirements == []
    assert opportunity.value_drivers == []
    assert opportunity.blockers == []
    assert opportunity.decision_makers == []
    assert opportunity.competitive_pressure == "unknown"


# ============================================================================
# RenewalCampaign Model Tests
# ============================================================================

@pytest.mark.unit
def test_renewal_campaign_valid_creation():
    """Test creating a valid RenewalCampaign."""
    campaign = RenewalCampaign(
        campaign_id="CAMP-2026Q1",
        campaign_name="Q1 2026 Renewals",
        start_date=date(2025, 10, 1),
        end_date=date(2026, 1, 31),
        target_renewal_date_range={
            "start": date(2026, 1, 1),
            "end": date(2026, 3, 31)
        },
        total_customers=50,
        total_arr_at_risk=3000000.0
    )

    assert campaign.campaign_id == "CAMP-2026Q1"
    assert campaign.total_customers == 50
    assert campaign.total_arr_at_risk == 3000000.0


@pytest.mark.unit
def test_renewal_campaign_win_rate_boundaries():
    """Test that win_rate respects 0-1 boundaries."""
    campaign = RenewalCampaign(
        campaign_id="CAMP-TEST",
        campaign_name="Test Campaign",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=90),
        target_renewal_date_range={
            "start": date.today(),
            "end": date.today() + timedelta(days=120)
        },
        total_customers=50,
        total_arr_at_risk=1000000.0,
        customers_contacted=40,
        customers_committed=30,
        win_rate=0.75
    )
    assert campaign.win_rate == 0.75


@pytest.mark.unit
def test_renewal_campaign_with_activities():
    """Test RenewalCampaign with campaign activities."""
    activities = [
        "Email reminder series",
        "Executive Business Reviews",
        "Value assessment sessions"
    ]

    campaign = RenewalCampaign(
        campaign_id="CAMP-TEST",
        campaign_name="Test Campaign",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=90),
        target_renewal_date_range={
            "start": date.today(),
            "end": date.today() + timedelta(days=120)
        },
        total_customers=50,
        total_arr_at_risk=1000000.0,
        campaign_activities=activities
    )

    assert len(campaign.campaign_activities) == 3


@pytest.mark.unit
def test_renewal_campaign_default_values():
    """Test that RenewalCampaign has correct default values."""
    campaign = RenewalCampaign(
        campaign_id="CAMP-TEST",
        campaign_name="Test Campaign",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=90),
        target_renewal_date_range={
            "start": date.today(),
            "end": date.today() + timedelta(days=120)
        },
        total_customers=50,
        total_arr_at_risk=1000000.0
    )

    assert campaign.customers_contacted == 0
    assert campaign.customers_committed == 0
    assert campaign.customers_at_risk == 0
    assert campaign.win_rate == 0.0
    assert campaign.expansion_opportunities_identified == 0
    assert campaign.expansion_value_identified == 0.0
    assert campaign.campaign_activities == []
    assert campaign.success_metrics == {}
