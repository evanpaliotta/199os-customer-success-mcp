"""
End-to-End Integration Tests

This module contains comprehensive end-to-end tests that validate
the complete customer lifecycle and platform integrations.

Test Coverage:
- Complete customer lifecycle (registration → churn risk → retention)
- Platform integrations (Zendesk, Intercom, Mixpanel, SendGrid)
- Error recovery and resilience
- Cross-component workflows
"""

import pytest
import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, Any
from unittest.mock import patch, Mock, AsyncMock

# Import models
from src.models.customer_models import (
    CustomerAccount, HealthScoreComponents, CustomerTier,
    LifecycleStage, HealthTrend, AccountStatus
)
from src.models.onboarding_models import OnboardingPlan, OnboardingMilestone
from src.models.support_models import SupportTicket, TicketPriority, TicketStatus
from src.models.feedback_models import NPSResponse, CustomerFeedback
from src.models.renewal_models import RenewalForecast, ExpansionOpportunity


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def test_customer_id() -> str:
    """Generate a unique customer ID for E2E tests."""
    timestamp = int(datetime.now().timestamp())
    return f"cs_{timestamp}_e2e_test_company"


@pytest.fixture
def test_customer_data() -> Dict[str, Any]:
    """Generate test customer data for E2E tests."""
    return {
        "client_name": "E2E Test Company",
        "company_name": "E2E Test Company Inc.",
        "industry": "Technology",
        "tier": "professional",
        "contract_value": 72000.0,
        "contract_start_date": date.today(),
        "contract_end_date": date.today() + timedelta(days=365),
        "renewal_date": date.today() + timedelta(days=365),
        "primary_contact_email": "test@e2etest.com",
        "primary_contact_name": "E2E Test User",
        "csm_assigned": "Test CSM"
    }


@pytest.fixture
def mock_integrations():
    """Mock all platform integrations for E2E tests."""
    with patch('src.integrations.zendesk_client.ZendeskClient') as mock_zendesk, \
         patch('src.integrations.intercom_client.IntercomClient') as mock_intercom, \
         patch('src.integrations.mixpanel_client.MixpanelClient') as mock_mixpanel, \
         patch('src.integrations.sendgrid_client.SendGridClient') as mock_sendgrid:

        # Configure Zendesk mock
        mock_zendesk_instance = Mock()
        mock_zendesk_instance.create_ticket = AsyncMock(return_value={
            "ticket_id": "12345",
            "status": "open",
            "url": "https://test.zendesk.com/tickets/12345"
        })
        mock_zendesk_instance.get_ticket = AsyncMock(return_value={
            "ticket_id": "12345",
            "status": "open"
        })
        mock_zendesk.return_value = mock_zendesk_instance

        # Configure Intercom mock
        mock_intercom_instance = Mock()
        mock_intercom_instance.send_message = AsyncMock(return_value={
            "message_id": "msg_123",
            "status": "sent"
        })
        mock_intercom_instance.create_user = AsyncMock(return_value={
            "user_id": "usr_123",
            "email": "test@e2etest.com"
        })
        mock_intercom.return_value = mock_intercom_instance

        # Configure Mixpanel mock
        mock_mixpanel_instance = Mock()
        mock_mixpanel_instance.track_event = AsyncMock(return_value=True)
        mock_mixpanel_instance.set_profile = AsyncMock(return_value=True)
        mock_mixpanel.return_value = mock_mixpanel_instance

        # Configure SendGrid mock
        mock_sendgrid_instance = Mock()
        mock_sendgrid_instance.send_email = AsyncMock(return_value={
            "message_id": "email_123",
            "status": "sent"
        })
        mock_sendgrid.return_value = mock_sendgrid_instance

        yield {
            "zendesk": mock_zendesk_instance,
            "intercom": mock_intercom_instance,
            "mixpanel": mock_mixpanel_instance,
            "sendgrid": mock_sendgrid_instance
        }


# ============================================================================
# Complete Customer Lifecycle Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
class TestCompleteCustomerLifecycle:
    """Test complete customer lifecycle from registration to renewal."""

    async def test_full_customer_journey(
        self,
        test_customer_id: str,
        test_customer_data: Dict[str, Any],
        mock_integrations: Dict[str, Mock]
    ):
        """
        Test complete customer journey:
        1. Register customer
        2. Create onboarding plan
        3. Track usage and engagement
        4. Calculate health score
        5. Identify churn risk
        6. Execute retention campaign
        7. Track renewal
        8. Identify expansion opportunity
        9. Collect feedback
        """

        # Step 1: Register Customer
        print("\n[E2E Test] Step 1: Registering customer...")

        from src.tools.core_system_tools import register_client

        result = await register_client(
            client_id=test_customer_id,
            **test_customer_data
        )

        assert result["success"] is True
        assert result["client_id"] == test_customer_id
        print(f"✓ Customer registered: {test_customer_id}")

        # Step 2: Create Onboarding Plan
        print("\n[E2E Test] Step 2: Creating onboarding plan...")

        from src.tools.onboarding_training_tools import create_onboarding_plan

        onboarding_result = await create_onboarding_plan(
            client_id=test_customer_id,
            plan_name="Enterprise Onboarding",
            duration_days=90,
            milestones=[
                {
                    "milestone_name": "Initial Setup",
                    "target_date": (date.today() + timedelta(days=7)).isoformat(),
                    "completion_criteria": ["API integration", "User training"]
                },
                {
                    "milestone_name": "First Value Delivery",
                    "target_date": (date.today() + timedelta(days=30)).isoformat(),
                    "completion_criteria": ["First health score", "First report"]
                }
            ]
        )

        assert onboarding_result["success"] is True
        assert onboarding_result["plan_id"] is not None
        print(f"✓ Onboarding plan created: {onboarding_result['plan_id']}")

        # Step 3: Track Usage and Engagement
        print("\n[E2E Test] Step 3: Tracking usage and engagement...")

        from src.tools.health_segmentation_tools import track_usage_engagement

        usage_events = [
            {"event_name": "login", "properties": {"source": "web"}},
            {"event_name": "feature_used", "properties": {"feature": "health_score"}},
            {"event_name": "report_generated", "properties": {"report_type": "customer_overview"}}
        ]

        for event in usage_events:
            await track_usage_engagement(
                client_id=test_customer_id,
                **event
            )

        # Verify Mixpanel tracking
        assert mock_integrations["mixpanel"].track_event.call_count >= 3
        print(f"✓ Tracked {len(usage_events)} usage events")

        # Step 4: Calculate Health Score
        print("\n[E2E Test] Step 4: Calculating health score...")

        from src.tools.health_segmentation_tools import calculate_health_score

        health_result = await calculate_health_score(
            client_id=test_customer_id,
            usage_score=85.0,
            engagement_score=78.0,
            support_score=92.0,
            satisfaction_score=88.0,
            payment_score=100.0
        )

        assert health_result["success"] is True
        assert health_result["health_score"] > 0
        assert health_result["health_score"] <= 100
        print(f"✓ Health score calculated: {health_result['health_score']}")

        # Step 5: Identify Churn Risk (simulate declining health)
        print("\n[E2E Test] Step 5: Identifying churn risk...")

        from src.tools.retention_risk_tools import identify_churn_risk

        # Simulate declining health score
        low_health_result = await calculate_health_score(
            client_id=test_customer_id,
            usage_score=35.0,  # Low usage
            engagement_score=40.0,  # Low engagement
            support_score=50.0,
            satisfaction_score=45.0,
            payment_score=70.0
        )

        churn_result = await identify_churn_risk(
            client_id=test_customer_id,
            health_score=low_health_result["health_score"]
        )

        assert churn_result["success"] is True
        assert churn_result["churn_risk_level"] in ["low", "medium", "high", "critical"]
        print(f"✓ Churn risk identified: {churn_result['churn_risk_level']}")

        # Step 6: Execute Retention Campaign
        print("\n[E2E Test] Step 6: Executing retention campaign...")

        from src.tools.retention_risk_tools import execute_retention_campaign

        campaign_result = await execute_retention_campaign(
            client_id=test_customer_id,
            campaign_name="At-Risk Customer Re-Engagement",
            campaign_type="email",
            target_action="increase_engagement"
        )

        assert campaign_result["success"] is True
        assert campaign_result["campaign_id"] is not None

        # Verify email sent via SendGrid
        assert mock_integrations["sendgrid"].send_email.called
        print(f"✓ Retention campaign executed: {campaign_result['campaign_id']}")

        # Step 7: Track Renewal (customer recovers)
        print("\n[E2E Test] Step 7: Tracking renewal...")

        from src.tools.expansion_revenue_tools import track_renewals

        renewal_result = await track_renewals(
            client_id=test_customer_id,
            renewal_date=(date.today() + timedelta(days=90)).isoformat(),
            renewal_amount=78000.0,  # 8% increase
            renewal_status="negotiating"
        )

        assert renewal_result["success"] is True
        assert renewal_result["renewal_id"] is not None
        print(f"✓ Renewal tracked: {renewal_result['renewal_id']}")

        # Step 8: Identify Expansion Opportunity
        print("\n[E2E Test] Step 8: Identifying expansion opportunity...")

        from src.tools.expansion_revenue_tools import identify_upsell_opportunities

        expansion_result = await identify_upsell_opportunities(
            client_id=test_customer_id,
            current_tier="professional",
            usage_patterns={"feature_adoption": 0.85, "team_size_growth": 1.5}
        )

        assert expansion_result["success"] is True
        assert expansion_result["opportunities"] is not None
        print(f"✓ Expansion opportunities identified: {len(expansion_result['opportunities'])}")

        # Step 9: Collect Feedback
        print("\n[E2E Test] Step 9: Collecting feedback...")

        from src.tools.feedback_intelligence_tools import collect_feedback

        feedback_result = await collect_feedback(
            client_id=test_customer_id,
            feedback_type="nps",
            score=9,
            comment="Great product! Would recommend to others."
        )

        assert feedback_result["success"] is True
        assert feedback_result["feedback_id"] is not None
        print(f"✓ Feedback collected: {feedback_result['feedback_id']}")

        print("\n[E2E Test] ✅ Complete customer lifecycle test PASSED")
        print(f"Total steps completed: 9")
        print(f"Customer ID: {test_customer_id}")


# ============================================================================
# Platform Integration Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
class TestPlatformIntegrations:
    """Test all platform integrations in sequence."""

    async def test_all_platform_integrations(
        self,
        test_customer_id: str,
        mock_integrations: Dict[str, Mock]
    ):
        """Test Zendesk, Intercom, Mixpanel, and SendGrid integrations."""

        print("\n[E2E Test] Testing all platform integrations...")

        # Test 1: Zendesk - Create Support Ticket
        print("\n[Integration Test] 1. Zendesk: Creating support ticket...")

        from src.tools.support_selfservice_tools import handle_support_ticket

        ticket_result = await handle_support_ticket(
            client_id=test_customer_id,
            subject="E2E Test Ticket",
            description="This is a test ticket for E2E integration testing",
            priority="medium",
            category="technical"
        )

        assert ticket_result["success"] is True
        assert ticket_result["ticket_id"] is not None
        assert mock_integrations["zendesk"].create_ticket.called
        print(f"✓ Zendesk ticket created: {ticket_result['ticket_id']}")

        # Test 2: Intercom - Send Message
        print("\n[Integration Test] 2. Intercom: Sending message...")

        from src.tools.communication_engagement_tools import send_personalized_email

        message_result = await send_personalized_email(
            client_id=test_customer_id,
            template="welcome",
            recipient_email="test@e2etest.com",
            subject="Welcome to CS MCP",
            variables={"name": "E2E Test User"}
        )

        assert message_result["success"] is True
        assert mock_integrations["intercom"].send_message.called or \
               mock_integrations["sendgrid"].send_email.called
        print(f"✓ Intercom/SendGrid message sent")

        # Test 3: Mixpanel - Track Event
        print("\n[Integration Test] 3. Mixpanel: Tracking event...")

        from src.tools.health_segmentation_tools import track_usage_engagement

        event_result = await track_usage_engagement(
            client_id=test_customer_id,
            event_name="e2e_test_event",
            properties={"test": True, "timestamp": datetime.now().isoformat()}
        )

        assert event_result["success"] is True
        assert mock_integrations["mixpanel"].track_event.called
        print(f"✓ Mixpanel event tracked")

        # Test 4: SendGrid - Send Email
        print("\n[Integration Test] 4. SendGrid: Sending email...")

        email_result = await send_personalized_email(
            client_id=test_customer_id,
            template="monthly_report",
            recipient_email="test@e2etest.com",
            subject="Your Monthly Report",
            variables={"month": "October", "year": "2025"}
        )

        assert email_result["success"] is True
        assert mock_integrations["sendgrid"].send_email.called
        print(f"✓ SendGrid email sent")

        print("\n[E2E Test] ✅ All platform integrations test PASSED")
        print(f"Integrations tested: 4")
        print(f"- Zendesk: ✓")
        print(f"- Intercom: ✓")
        print(f"- Mixpanel: ✓")
        print(f"- SendGrid: ✓")


# ============================================================================
# Error Recovery Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
class TestErrorRecovery:
    """Test error handling and recovery scenarios."""

    async def test_database_failure_recovery(self, test_customer_id: str):
        """Test recovery from database connection failure."""

        print("\n[E2E Test] Testing database failure recovery...")

        from src.tools.core_system_tools import get_client_overview

        # Simulate database failure
        with patch('src.core.database.DatabaseManager.fetch_one', side_effect=Exception("Database connection lost")):
            try:
                result = await get_client_overview(client_id=test_customer_id)
                # Should handle gracefully
                assert result["success"] is False
                assert "error" in result
                print("✓ Database failure handled gracefully")
            except Exception as e:
                pytest.fail(f"Database failure not handled properly: {e}")

    async def test_platform_api_failure_recovery(self, test_customer_id: str):
        """Test recovery from platform API failure."""

        print("\n[E2E Test] Testing platform API failure recovery...")

        from src.tools.support_selfservice_tools import handle_support_ticket

        # Simulate Zendesk API failure
        with patch('src.integrations.zendesk_client.ZendeskClient.create_ticket',
                   side_effect=Exception("API rate limit exceeded")):

            result = await handle_support_ticket(
                client_id=test_customer_id,
                subject="Test Ticket",
                description="Test",
                priority="low",
                category="general"
            )

            # Should degrade gracefully (log ticket locally but fail API call)
            # Depending on implementation, this might succeed (cached) or fail gracefully
            assert "error" in result or result.get("success") is False
            print("✓ API failure handled gracefully (degraded mode)")

    async def test_invalid_input_handling(self):
        """Test handling of invalid inputs."""

        print("\n[E2E Test] Testing invalid input handling...")

        from src.tools.core_system_tools import register_client

        # Test 1: Invalid client_id
        with pytest.raises(ValueError):
            await register_client(
                client_id="invalid_id_with_@_symbols",
                client_name="Test",
                industry="Tech"
            )
        print("✓ Invalid client_id rejected")

        # Test 2: Invalid email
        from src.tools.communication_engagement_tools import send_personalized_email

        result = await send_personalized_email(
            client_id="cs_123_test",
            template="welcome",
            recipient_email="invalid-email",
            subject="Test",
            variables={}
        )

        assert result["success"] is False
        print("✓ Invalid email rejected")

        # Test 3: SQL injection attempt
        with pytest.raises((ValueError, Exception)):
            await register_client(
                client_id="cs_123_test'; DROP TABLE customers;--",
                client_name="Test",
                industry="Tech"
            )
        print("✓ SQL injection attempt blocked")

        print("\n[E2E Test] ✅ Error recovery tests PASSED")


# ============================================================================
# Cross-Component Workflow Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
class TestCrossComponentWorkflows:
    """Test workflows that span multiple components."""

    async def test_health_score_to_retention_workflow(
        self,
        test_customer_id: str,
        mock_integrations: Dict[str, Mock]
    ):
        """Test workflow: Low health score → Churn risk → Retention campaign."""

        print("\n[E2E Test] Testing health score to retention workflow...")

        # Step 1: Calculate low health score
        from src.tools.health_segmentation_tools import calculate_health_score

        health_result = await calculate_health_score(
            client_id=test_customer_id,
            usage_score=30.0,
            engagement_score=35.0,
            support_score=40.0,
            satisfaction_score=42.0,
            payment_score=80.0
        )

        assert health_result["health_score"] < 50
        print(f"✓ Low health score calculated: {health_result['health_score']}")

        # Step 2: Identify churn risk
        from src.tools.retention_risk_tools import identify_churn_risk

        churn_result = await identify_churn_risk(
            client_id=test_customer_id,
            health_score=health_result["health_score"]
        )

        assert churn_result["churn_risk_level"] in ["high", "critical"]
        print(f"✓ High churn risk identified: {churn_result['churn_risk_level']}")

        # Step 3: Trigger retention campaign
        from src.tools.retention_risk_tools import execute_retention_campaign

        campaign_result = await execute_retention_campaign(
            client_id=test_customer_id,
            campaign_name="High-Risk Recovery",
            campaign_type="multi_channel",
            target_action="increase_engagement"
        )

        assert campaign_result["success"] is True
        print(f"✓ Retention campaign triggered: {campaign_result['campaign_id']}")

        # Verify integration calls
        assert mock_integrations["sendgrid"].send_email.called or \
               mock_integrations["intercom"].send_message.called

        print("\n[E2E Test] ✅ Health score to retention workflow PASSED")

    async def test_onboarding_to_health_workflow(
        self,
        test_customer_id: str,
        test_customer_data: Dict[str, Any]
    ):
        """Test workflow: Customer registration → Onboarding → Health score."""

        print("\n[E2E Test] Testing onboarding to health workflow...")

        # Step 1: Register customer
        from src.tools.core_system_tools import register_client

        await register_client(client_id=test_customer_id, **test_customer_data)
        print(f"✓ Customer registered: {test_customer_id}")

        # Step 2: Create onboarding plan
        from src.tools.onboarding_training_tools import create_onboarding_plan

        onboarding_result = await create_onboarding_plan(
            client_id=test_customer_id,
            plan_name="Standard Onboarding",
            duration_days=90,
            milestones=[{"milestone_name": "Setup Complete", "target_date": (date.today() + timedelta(days=7)).isoformat()}]
        )

        assert onboarding_result["success"] is True
        print(f"✓ Onboarding plan created")

        # Step 3: Track onboarding progress
        from src.tools.onboarding_training_tools import track_onboarding_progress

        progress_result = await track_onboarding_progress(
            client_id=test_customer_id,
            milestone_id=onboarding_result.get("milestones", [{}])[0].get("milestone_id", "milestone_1"),
            completion_percentage=50.0
        )

        assert progress_result["success"] is True
        print(f"✓ Onboarding progress tracked: 50%")

        # Step 4: Calculate health score (should reflect onboarding progress)
        from src.tools.health_segmentation_tools import calculate_health_score

        health_result = await calculate_health_score(
            client_id=test_customer_id,
            usage_score=60.0,  # Moderate usage during onboarding
            engagement_score=65.0,
            support_score=85.0,
            satisfaction_score=75.0,
            payment_score=100.0
        )

        assert health_result["health_score"] > 50
        print(f"✓ Health score calculated: {health_result['health_score']}")

        print("\n[E2E Test] ✅ Onboarding to health workflow PASSED")


# ============================================================================
# Performance Test (Simple)
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestPerformance:
    """Simple performance tests (more comprehensive load testing with Locust)."""

    async def test_health_score_calculation_performance(self, test_customer_id: str):
        """Test health score calculation performance (<100ms target)."""

        import time
        from src.tools.health_segmentation_tools import calculate_health_score

        start = time.time()

        result = await calculate_health_score(
            client_id=test_customer_id,
            usage_score=85.0,
            engagement_score=78.0,
            support_score=92.0,
            satisfaction_score=88.0,
            payment_score=100.0
        )

        duration = (time.time() - start) * 1000  # Convert to ms

        assert result["success"] is True
        assert duration < 100, f"Health score calculation took {duration}ms (target: <100ms)"

        print(f"\n[Performance Test] Health score calculation: {duration:.2f}ms ✓")

    async def test_database_query_performance(self, test_customer_id: str, test_customer_data: Dict[str, Any]):
        """Test database query performance (<50ms target for indexed lookups)."""

        import time
        from src.tools.core_system_tools import register_client, get_client_overview

        # Register customer
        await register_client(client_id=test_customer_id, **test_customer_data)

        # Test retrieval performance
        start = time.time()
        result = await get_client_overview(client_id=test_customer_id)
        duration = (time.time() - start) * 1000

        assert result["success"] is True
        assert duration < 50, f"Database query took {duration}ms (target: <50ms)"

        print(f"\n[Performance Test] Database query: {duration:.2f}ms ✓")


# ============================================================================
# Run All E2E Tests
# ============================================================================

if __name__ == "__main__":
    """Run all E2E tests with detailed output."""

    print("=" * 80)
    print("CUSTOMER SUCCESS MCP - END-TO-END INTEGRATION TESTS")
    print("=" * 80)

    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s",  # Show print statements
        "--durations=10",  # Show slowest 10 tests
        "-m", "integration",  # Run only integration tests
    ])
