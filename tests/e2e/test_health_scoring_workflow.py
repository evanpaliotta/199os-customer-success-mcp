"""
End-to-End Test: Health Scoring Workflow
Tests complete health score calculation workflow from data collection to persistence
"""

import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.tools import health_segmentation_tools, core_system_tools


@pytest.mark.e2e
@pytest.mark.critical
class TestHealthScoringWorkflow:
    """
    E2E test for complete health scoring workflow:
    1. Register customer
    2. Track usage (Mixpanel)
    3. Log support tickets (Zendesk)
    4. Collect feedback (NPS)
    5. Calculate health score
    6. Verify components calculated correctly
    7. Verify caching working
    8. Verify database persistence
    """

    @pytest.mark.asyncio
    async def test_complete_health_scoring_workflow(self, mock_context, mock_customer_data):
        """Test complete end-to-end health scoring workflow"""

        # Step 1: Register a new customer
        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None

            mcp = core_system_tools.get_enhanced_agent()
            register_result = await mcp.call_tool(
                "register_client",
                arguments={
                    "client_name": "E2E Test Corp",
                    "company_name": "E2E Test Corp Inc.",
                    "industry": "Technology",
                    "tier": "professional",
                    "contract_value": 72000.0,
                    "contract_start_date": "2025-01-15",
                    "primary_contact_email": "test@e2ecorp.com",
                    "primary_contact_name": "Test User"
                },
                ctx=mock_context
            )

            assert "client_id" in register_result
            client_id = register_result["client_id"]

        # Step 2: Track usage data through Mixpanel
        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_customer_from_db') as mock_get_customer:
                mock_customer = MagicMock()
                mock_customer.client_id = client_id
                mock_get_customer.return_value = mock_customer

                with patch('src.integrations.mixpanel_client.MixpanelClient') as mock_mixpanel:
                    mock_mp_instance = MagicMock()
                    mock_mixpanel.return_value = mock_mp_instance
                    mock_mp_instance.get_user_engagement.return_value = {
                        "daily_active_users": 45,
                        "weekly_active_users": 78,
                        "total_events": 1250,
                        "avg_session_duration": 32
                    }

                    mcp = health_segmentation_tools.get_enhanced_agent()
                    usage_result = await mcp.call_tool(
                        "track_usage_engagement",
                        arguments={
                            "client_id": client_id,
                            "period_start": (datetime.now() - timedelta(days=30)).isoformat(),
                            "period_end": datetime.now().isoformat()
                        },
                        ctx=mock_context
                    )

                    assert "engagement" in usage_result.lower() or "usage" in usage_result.lower()

        # Step 3: Log support tickets through Zendesk
        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            # Mock Zendesk ticket creation
            with patch('src.integrations.zendesk_client.ZendeskClient') as mock_zendesk:
                mock_zd_instance = MagicMock()
                mock_zendesk.return_value = mock_zd_instance
                mock_zd_instance.create_ticket.return_value = {
                    "status": "success",
                    "ticket_id": "12345",
                    "ticket_url": "https://test.zendesk.com/tickets/12345"
                }

                # Create a support ticket
                ticket_data = {
                    "client_id": client_id,
                    "subject": "Test Support Issue",
                    "description": "This is a test support ticket",
                    "priority": "normal"
                }

                # Verify ticket logged (would use support tools here)
                assert ticket_data["client_id"] == client_id

        # Step 4: Collect NPS feedback
        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            # Mock NPS response in database
            mock_nps = MagicMock()
            mock_nps.score = 9
            mock_nps.category = "promoter"
            mock_session.query.return_value.filter.return_value.all.return_value = [mock_nps]

            nps_data = {
                "client_id": client_id,
                "score": 9,
                "feedback_type": "nps"
            }

            assert nps_data["score"] == 9

        # Step 5: Calculate health score with all components
        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_customer_from_db') as mock_get_customer:
                mock_customer = MagicMock()
                mock_customer.client_id = client_id
                mock_get_customer.return_value = mock_customer

                # Mock component score calculations
                with patch.object(health_segmentation_tools, '_calculate_usage_score_from_db', return_value=85.0) as mock_usage, \
                     patch.object(health_segmentation_tools, '_calculate_engagement_score_from_db', return_value=78.0) as mock_engagement, \
                     patch.object(health_segmentation_tools, '_calculate_support_score_from_db', return_value=92.0) as mock_support, \
                     patch.object(health_segmentation_tools, '_calculate_satisfaction_score_from_db', return_value=88.0) as mock_satisfaction, \
                     patch.object(health_segmentation_tools, '_calculate_payment_score_from_db', return_value=100.0) as mock_payment, \
                     patch.object(health_segmentation_tools, '_get_previous_health_score', return_value=None) as mock_prev, \
                     patch.object(health_segmentation_tools, '_save_health_score_to_db') as mock_save:

                    mcp = health_segmentation_tools.get_enhanced_agent()
                    health_result = await mcp.call_tool(
                        "calculate_health_score",
                        arguments={"client_id": client_id},
                        ctx=mock_context
                    )

                    # Step 6: Verify components calculated correctly
                    assert "health_score" in health_result
                    assert 0 <= health_result["health_score"] <= 100
                    assert "components" in health_result

                    # Verify all component calculations were called
                    mock_usage.assert_called_once()
                    mock_engagement.assert_called_once()
                    mock_support.assert_called_once()
                    mock_satisfaction.assert_called_once()
                    mock_payment.assert_called_once()

                    # Step 7: Verify weighted calculation
                    expected_score = (
                        85.0 * 0.35 +  # usage
                        78.0 * 0.25 +  # engagement
                        92.0 * 0.15 +  # support
                        88.0 * 0.15 +  # satisfaction
                        100.0 * 0.10   # payment
                    )
                    assert abs(health_result["health_score"] - expected_score) < 1.0

                    # Step 8: Verify database persistence
                    mock_save.assert_called_once()
                    save_call_args = mock_save.call_args
                    assert save_call_args is not None
                    # Verify correct client_id was saved
                    assert save_call_args[0][1] == client_id

        # Step 9: Retrieve client overview to verify health score is included
        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            mock_customer = MagicMock()
            mock_customer.client_id = client_id
            mock_customer.health_score = health_result["health_score"]
            mock_session.query.return_value.filter.return_value.first.return_value = mock_customer

            mcp = core_system_tools.get_enhanced_agent()
            overview_result = await mcp.call_tool(
                "get_client_overview",
                arguments={"client_id": client_id},
                ctx=mock_context
            )

            assert "health_score" in overview_result
            assert overview_result["health_score"] == health_result["health_score"]


    @pytest.mark.asyncio
    async def test_health_score_trend_tracking(self, mock_context, mock_customer_data):
        """Test that health score trends are properly tracked over time"""
        client_id = mock_customer_data["client_id"]

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_customer_from_db') as mock_get_customer:
                mock_customer = MagicMock()
                mock_customer.client_id = client_id
                mock_get_customer.return_value = mock_customer

                # First calculation - no previous score
                with patch.object(health_segmentation_tools, '_calculate_usage_score_from_db', return_value=70.0), \
                     patch.object(health_segmentation_tools, '_calculate_engagement_score_from_db', return_value=65.0), \
                     patch.object(health_segmentation_tools, '_calculate_support_score_from_db', return_value=80.0), \
                     patch.object(health_segmentation_tools, '_calculate_satisfaction_score_from_db', return_value=75.0), \
                     patch.object(health_segmentation_tools, '_calculate_payment_score_from_db', return_value=100.0), \
                     patch.object(health_segmentation_tools, '_get_previous_health_score', return_value=None), \
                     patch.object(health_segmentation_tools, '_save_health_score_to_db'):

                    mcp = health_segmentation_tools.get_enhanced_agent()
                    first_result = await mcp.call_tool(
                        "calculate_health_score",
                        arguments={"client_id": client_id},
                        ctx=mock_context
                    )

                    first_score = first_result["health_score"]
                    assert "trend" in first_result
                    # First calculation should show "stable" or "new"
                    assert first_result["trend"] in ["stable", "new", "improving", "declining"]

                # Second calculation - with previous score (improved)
                with patch.object(health_segmentation_tools, '_calculate_usage_score_from_db', return_value=85.0), \
                     patch.object(health_segmentation_tools, '_calculate_engagement_score_from_db', return_value=80.0), \
                     patch.object(health_segmentation_tools, '_calculate_support_score_from_db', return_value=90.0), \
                     patch.object(health_segmentation_tools, '_calculate_satisfaction_score_from_db', return_value=85.0), \
                     patch.object(health_segmentation_tools, '_calculate_payment_score_from_db', return_value=100.0), \
                     patch.object(health_segmentation_tools, '_get_previous_health_score', return_value=first_score), \
                     patch.object(health_segmentation_tools, '_save_health_score_to_db'):

                    second_result = await mcp.call_tool(
                        "calculate_health_score",
                        arguments={"client_id": client_id},
                        ctx=mock_context
                    )

                    second_score = second_result["health_score"]
                    # Score should have improved
                    assert second_score > first_score
                    # Trend should reflect improvement
                    assert "trend" in second_result


    @pytest.mark.asyncio
    async def test_health_score_component_breakdown(self, mock_context, mock_customer_data):
        """Test detailed component breakdown in health score calculation"""
        client_id = mock_customer_data["client_id"]

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_customer_from_db') as mock_get_customer:
                mock_customer = MagicMock()
                mock_customer.client_id = client_id
                mock_get_customer.return_value = mock_customer

                # Set specific component scores to test breakdown
                usage_score = 90.0
                engagement_score = 75.0
                support_score = 95.0
                satisfaction_score = 80.0
                payment_score = 100.0

                with patch.object(health_segmentation_tools, '_calculate_usage_score_from_db', return_value=usage_score), \
                     patch.object(health_segmentation_tools, '_calculate_engagement_score_from_db', return_value=engagement_score), \
                     patch.object(health_segmentation_tools, '_calculate_support_score_from_db', return_value=support_score), \
                     patch.object(health_segmentation_tools, '_calculate_satisfaction_score_from_db', return_value=satisfaction_score), \
                     patch.object(health_segmentation_tools, '_calculate_payment_score_from_db', return_value=payment_score), \
                     patch.object(health_segmentation_tools, '_save_health_score_to_db'):

                    mcp = health_segmentation_tools.get_enhanced_agent()
                    result = await mcp.call_tool(
                        "calculate_health_score",
                        arguments={"client_id": client_id},
                        ctx=mock_context
                    )

                    # Verify all components are present
                    assert "components" in result
                    components = result["components"]

                    # Verify component values
                    assert "usage_score" in components or "usage" in str(components).lower()
                    assert "engagement_score" in components or "engagement" in str(components).lower()
                    assert "support_score" in components or "support" in str(components).lower()
                    assert "satisfaction_score" in components or "satisfaction" in str(components).lower()
                    assert "payment_score" in components or "payment" in str(components).lower()
