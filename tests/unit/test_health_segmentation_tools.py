"""
Unit Tests for Health & Segmentation Tools
Critical tests for health score calculation, customer segmentation, and lifecycle management
"""

import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from mcp.server.fastmcp import Context

# Import tools to test
from src.tools import health_segmentation_tools


@pytest.mark.unit
@pytest.mark.critical
class TestCalculateHealthScore:
    """Test suite for calculate_health_score tool"""

    @pytest.mark.asyncio
    async def test_calculate_health_score_success(self, mock_context, mock_customer_data):
        """Test successful health score calculation with default weights"""
        client_id = mock_customer_data["client_id"]

        # Mock database session
        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            # Mock customer lookup
            with patch.object(health_segmentation_tools, '_get_customer_from_db') as mock_get_customer:
                mock_customer = MagicMock()
                mock_customer.client_id = client_id
                mock_customer.client_name = "Test Customer"
                mock_get_customer.return_value = mock_customer

                # Mock component score calculations
                with patch.object(health_segmentation_tools, '_calculate_usage_score_from_db', return_value=85.0), \
                     patch.object(health_segmentation_tools, '_calculate_engagement_score_from_db', return_value=78.0), \
                     patch.object(health_segmentation_tools, '_calculate_support_score_from_db', return_value=92.0), \
                     patch.object(health_segmentation_tools, '_calculate_satisfaction_score_from_db', return_value=88.0), \
                     patch.object(health_segmentation_tools, '_calculate_payment_score_from_db', return_value=100.0), \
                     patch.object(health_segmentation_tools, '_get_previous_health_score', return_value=80.0), \
                     patch.object(health_segmentation_tools, '_save_health_score_to_db'):

                    # Call the tool - need to access from mcp instance
                    mcp = health_segmentation_tools.get_enhanced_agent()
                    result = await mcp.call_tool(
                        "calculate_health_score",
                        arguments={
                            "client_id": client_id,
                            "scoring_model": "weighted_composite"
                        },
                        ctx=mock_context
                    )

                    # Assertions
                    assert "health_score" in result
                    assert 0 <= result["health_score"] <= 100
                    assert "components" in result
                    assert len(result["components"]) == 5
                    assert "trend" in result
                    assert "calculated_at" in result

    @pytest.mark.asyncio
    async def test_calculate_health_score_custom_weights(self, mock_context, mock_customer_data):
        """Test health score calculation with custom component weights"""
        client_id = mock_customer_data["client_id"]
        custom_weights = {
            "usage_weight": 0.40,
            "engagement_weight": 0.30,
            "support_weight": 0.10,
            "satisfaction_weight": 0.10,
            "payment_weight": 0.10
        }

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_customer_from_db') as mock_get_customer:
                mock_customer = MagicMock()
                mock_customer.client_id = client_id
                mock_get_customer.return_value = mock_customer

                with patch.object(health_segmentation_tools, '_calculate_usage_score_from_db', return_value=90.0), \
                     patch.object(health_segmentation_tools, '_calculate_engagement_score_from_db', return_value=85.0), \
                     patch.object(health_segmentation_tools, '_calculate_support_score_from_db', return_value=95.0), \
                     patch.object(health_segmentation_tools, '_calculate_satisfaction_score_from_db', return_value=80.0), \
                     patch.object(health_segmentation_tools, '_calculate_payment_score_from_db', return_value=100.0), \
                     patch.object(health_segmentation_tools, '_save_health_score_to_db'):

                    mcp = health_segmentation_tools.get_enhanced_agent()
                    result = await mcp.call_tool(
                        "calculate_health_score",
                        arguments={
                            "client_id": client_id,
                            "component_weights": custom_weights
                        },
                        ctx=mock_context
                    )

                    assert "health_score" in result
                    # Verify custom weights were used in calculation
                    expected_score = (90.0 * 0.40 + 85.0 * 0.30 + 95.0 * 0.10 + 80.0 * 0.10 + 100.0 * 0.10)
                    assert abs(result["health_score"] - expected_score) < 1.0

    @pytest.mark.asyncio
    async def test_calculate_health_score_invalid_client(self, mock_context):
        """Test health score calculation with invalid client ID"""
        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_customer_from_db', return_value=None):
                mcp = health_segmentation_tools.get_enhanced_agent()
                result = await mcp.call_tool(
                    "calculate_health_score",
                    arguments={"client_id": "invalid_client_id"},
                    ctx=mock_context
                )

                assert "error" in result.lower() or "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_calculate_health_score_database_error(self, mock_context, mock_customer_data):
        """Test health score calculation when database fails"""
        client_id = mock_customer_data["client_id"]

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")

            mcp = health_segmentation_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "calculate_health_score",
                arguments={"client_id": client_id},
                ctx=mock_context
            )

            assert "error" in result.lower() or "failed" in result.lower()

    @pytest.mark.asyncio
    async def test_calculate_health_score_caching(self, mock_context, mock_customer_data):
        """Test that health scores are properly cached"""
        client_id = mock_customer_data["client_id"]

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_customer_from_db') as mock_get_customer:
                mock_customer = MagicMock()
                mock_customer.client_id = client_id
                mock_get_customer.return_value = mock_customer

                with patch.object(health_segmentation_tools, '_calculate_usage_score_from_db', return_value=85.0), \
                     patch.object(health_segmentation_tools, '_calculate_engagement_score_from_db', return_value=78.0), \
                     patch.object(health_segmentation_tools, '_calculate_support_score_from_db', return_value=92.0), \
                     patch.object(health_segmentation_tools, '_calculate_satisfaction_score_from_db', return_value=88.0), \
                     patch.object(health_segmentation_tools, '_calculate_payment_score_from_db', return_value=100.0), \
                     patch.object(health_segmentation_tools, '_save_health_score_to_db') as mock_save:

                    mcp = health_segmentation_tools.get_enhanced_agent()
                    await mcp.call_tool(
                        "calculate_health_score",
                        arguments={"client_id": client_id},
                        ctx=mock_context
                    )

                    # Verify save was called to persist to database
                    assert mock_save.called


@pytest.mark.unit
@pytest.mark.critical
class TestSegmentCustomers:
    """Test suite for segment_customers tool"""

    @pytest.mark.asyncio
    async def test_segment_by_value_tier_success(self, mock_context):
        """Test successful customer segmentation by value tier"""
        criteria = {
            "min_arr": 50000,
            "tier_breakdown": True
        }

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_generate_value_segments') as mock_gen:
                mock_gen.return_value = [
                    MagicMock(segment_id="seg_high_value", customer_count=25, total_arr=5000000.0),
                    MagicMock(segment_id="seg_mid_value", customer_count=50, total_arr=3000000.0)
                ]

                mcp = health_segmentation_tools.get_enhanced_agent()
                result = await mcp.call_tool(
                    "segment_customers",
                    arguments={
                        "segmentation_type": "value_based",
                        "criteria": criteria,
                        "min_segment_size": 5
                    },
                    ctx=mock_context
                )

                assert "segments" in result
                assert len(result["segments"]) >= 1
                assert "total_segments" in result

    @pytest.mark.asyncio
    async def test_segment_by_lifecycle_stage(self, mock_context):
        """Test customer segmentation by lifecycle stage"""
        criteria = {"include_all_stages": True}

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_generate_lifecycle_segments') as mock_gen:
                mock_gen.return_value = [
                    MagicMock(segment_id="seg_onboarding", customer_count=15),
                    MagicMock(segment_id="seg_active", customer_count=80),
                    MagicMock(segment_id="seg_at_risk", customer_count=10)
                ]

                mcp = health_segmentation_tools.get_enhanced_agent()
                result = await mcp.call_tool(
                    "segment_customers",
                    arguments={
                        "segmentation_type": "lifecycle",
                        "criteria": criteria
                    },
                    ctx=mock_context
                )

                assert "segments" in result
                assert len(result["segments"]) >= 3

    @pytest.mark.asyncio
    async def test_segment_by_health_score(self, mock_context):
        """Test customer segmentation by health score ranges"""
        criteria = {
            "health_ranges": {
                "high": {"min": 80, "max": 100},
                "medium": {"min": 60, "max": 79},
                "low": {"min": 0, "max": 59}
            }
        }

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_generate_health_segments') as mock_gen:
                mock_gen.return_value = [
                    MagicMock(segment_id="seg_healthy", customer_count=60, avg_health_score=85.5),
                    MagicMock(segment_id="seg_at_risk", customer_count=25, avg_health_score=45.2)
                ]

                mcp = health_segmentation_tools.get_enhanced_agent()
                result = await mcp.call_tool(
                    "segment_customers",
                    arguments={
                        "segmentation_type": "health_based",
                        "criteria": criteria
                    },
                    ctx=mock_context
                )

                assert "segments" in result


@pytest.mark.unit
@pytest.mark.critical
class TestManageLifecycleStages:
    """Test suite for manage_lifecycle_stages tool"""

    @pytest.mark.asyncio
    async def test_get_lifecycle_distribution(self, mock_context):
        """Test retrieving lifecycle stage distribution"""
        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_lifecycle_stage_distribution') as mock_dist:
                mock_dist.return_value = {
                    "onboarding": 15,
                    "active": 80,
                    "at_risk": 10,
                    "expansion": 20,
                    "renewal": 25
                }

                mcp = health_segmentation_tools.get_enhanced_agent()
                result = await mcp.call_tool(
                    "manage_lifecycle_stages",
                    arguments={"include_transitions": False},
                    ctx=mock_context
                )

                assert "distribution" in result
                assert "onboarding" in result["distribution"]
                assert "active" in result["distribution"]
                assert "at_risk" in result["distribution"]

    @pytest.mark.asyncio
    async def test_update_customer_lifecycle_stage(self, mock_context, mock_customer_data):
        """Test updating a customer's lifecycle stage"""
        client_id = mock_customer_data["client_id"]

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_customer_from_db') as mock_get:
                mock_customer = MagicMock()
                mock_customer.client_id = client_id
                mock_customer.lifecycle_stage = "active"
                mock_get.return_value = mock_customer

                mcp = health_segmentation_tools.get_enhanced_agent()
                result = await mcp.call_tool(
                    "manage_lifecycle_stages",
                    arguments={
                        "client_id": client_id,
                        "current_stage": "expansion"
                    },
                    ctx=mock_context
                )

                # Should show stage change
                assert "stage" in result or "lifecycle" in result


@pytest.mark.unit
@pytest.mark.critical
class TestTrackUsageEngagement:
    """Test suite for track_usage_engagement tool"""

    @pytest.mark.asyncio
    async def test_track_usage_engagement_success(self, mock_context, mock_customer_data):
        """Test successful usage and engagement tracking"""
        client_id = mock_customer_data["client_id"]
        period_start = (datetime.now() - timedelta(days=30)).isoformat()
        period_end = datetime.now().isoformat()

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_customer_from_db') as mock_get:
                mock_customer = MagicMock()
                mock_customer.client_id = client_id
                mock_get.return_value = mock_customer

                # Mock Mixpanel client
                with patch('src.integrations.mixpanel_client.MixpanelClient') as mock_mixpanel:
                    mock_mp_instance = MagicMock()
                    mock_mixpanel.return_value = mock_mp_instance
                    mock_mp_instance.get_user_engagement.return_value = {
                        "daily_active_users": 45,
                        "weekly_active_users": 78,
                        "total_events": 1250
                    }

                    mcp = health_segmentation_tools.get_enhanced_agent()
                    result = await mcp.call_tool(
                        "track_usage_engagement",
                        arguments={
                            "client_id": client_id,
                            "period_start": period_start,
                            "period_end": period_end
                        },
                        ctx=mock_context
                    )

                    assert "engagement_metrics" in result or "usage" in result

    @pytest.mark.asyncio
    async def test_track_usage_with_feature_breakdown(self, mock_context, mock_customer_data):
        """Test usage tracking with feature-level breakdown"""
        client_id = mock_customer_data["client_id"]
        period_start = (datetime.now() - timedelta(days=7)).isoformat()
        period_end = datetime.now().isoformat()

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_customer_from_db') as mock_get:
                mock_customer = MagicMock()
                mock_get.return_value = mock_customer

                mcp = health_segmentation_tools.get_enhanced_agent()
                result = await mcp.call_tool(
                    "track_usage_engagement",
                    arguments={
                        "client_id": client_id,
                        "period_start": period_start,
                        "period_end": period_end,
                        "granularity": "daily",
                        "include_feature_breakdown": True
                    },
                    ctx=mock_context
                )

                # Should include feature breakdown
                assert "feature" in result.lower() or "breakdown" in result.lower()


@pytest.mark.unit
@pytest.mark.critical
class TestTrackFeatureAdoption:
    """Test suite for track_feature_adoption tool"""

    @pytest.mark.asyncio
    async def test_track_feature_adoption_all_customers(self, mock_context):
        """Test tracking feature adoption across all customers"""
        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            mcp = health_segmentation_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "track_feature_adoption",
                arguments={"time_period_days": 90},
                ctx=mock_context
            )

            assert "adoption" in result.lower() or "features" in result.lower()

    @pytest.mark.asyncio
    async def test_track_specific_feature_adoption(self, mock_context, mock_customer_data):
        """Test tracking adoption of a specific feature"""
        client_id = mock_customer_data["client_id"]

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_customer_from_db') as mock_get:
                mock_customer = MagicMock()
                mock_get.return_value = mock_customer

                mcp = health_segmentation_tools.get_enhanced_agent()
                result = await mcp.call_tool(
                    "track_feature_adoption",
                    arguments={
                        "client_id": client_id,
                        "feature_id": "advanced_analytics",
                        "time_period_days": 30
                    },
                    ctx=mock_context
                )

                assert "adoption" in result.lower() or "feature" in result.lower()


@pytest.mark.unit
@pytest.mark.critical
class TestSegmentByValueTier:
    """Test suite for segment_by_value_tier tool"""

    @pytest.mark.asyncio
    async def test_segment_by_arr_ranges(self, mock_context):
        """Test segmentation by ARR value ranges"""
        criteria = {
            "arr_ranges": {
                "enterprise": {"min": 100000},
                "mid_market": {"min": 25000, "max": 99999},
                "smb": {"max": 24999}
            }
        }

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_value_tier_distribution') as mock_dist:
                mock_dist.return_value = {
                    "tiers": {
                        "enterprise": {"count": 15, "total_arr": 3500000},
                        "mid_market": {"count": 45, "total_arr": 2250000},
                        "smb": {"count": 120, "total_arr": 1200000}
                    }
                }

                mcp = health_segmentation_tools.get_enhanced_agent()
                result = await mcp.call_tool(
                    "segment_by_value_tier",
                    arguments={
                        "segmentation_criteria": criteria,
                        "service_level_mapping": True
                    },
                    ctx=mock_context
                )

                assert "segments" in result or "tiers" in result

    @pytest.mark.asyncio
    async def test_segment_with_service_mapping(self, mock_context):
        """Test value tier segmentation with service level mapping"""
        criteria = {"include_ltv": True}

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            mcp = health_segmentation_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "segment_by_value_tier",
                arguments={
                    "segmentation_criteria": criteria,
                    "service_level_mapping": True
                },
                ctx=mock_context
            )

            # Should include service level recommendations
            assert "service" in result.lower() or "tier" in result.lower()


@pytest.mark.unit
@pytest.mark.critical
class TestAnalyzeEngagementPatterns:
    """Test suite for analyze_engagement_patterns tool"""

    @pytest.mark.asyncio
    async def test_analyze_all_customer_patterns(self, mock_context):
        """Test engagement pattern analysis for all customers"""
        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            mcp = health_segmentation_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "analyze_engagement_patterns",
                arguments={
                    "analysis_scope": "all_customers",
                    "pattern_types": ["login_frequency", "feature_usage", "support_interaction"]
                },
                ctx=mock_context
            )

            assert "patterns" in result.lower() or "engagement" in result.lower()

    @pytest.mark.asyncio
    async def test_analyze_segment_patterns(self, mock_context):
        """Test engagement pattern analysis for specific segment"""
        scope_filter = {
            "tier": "enterprise",
            "lifecycle_stage": "active"
        }

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            mcp = health_segmentation_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "analyze_engagement_patterns",
                arguments={
                    "analysis_scope": "segment",
                    "scope_filter": scope_filter
                },
                ctx=mock_context
            )

            assert "patterns" in result.lower() or "segment" in result.lower()


@pytest.mark.unit
@pytest.mark.critical
class TestTrackAdoptionMilestones:
    """Test suite for track_adoption_milestones tool"""

    @pytest.mark.asyncio
    async def test_track_standard_milestones(self, mock_context, mock_customer_data):
        """Test tracking standard adoption milestones"""
        client_id = mock_customer_data["client_id"]

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_customer_from_db') as mock_get:
                mock_customer = MagicMock()
                mock_get.return_value = mock_customer

                mcp = health_segmentation_tools.get_enhanced_agent()
                result = await mcp.call_tool(
                    "track_adoption_milestones",
                    arguments={
                        "client_id": client_id,
                        "milestone_framework": "standard"
                    },
                    ctx=mock_context
                )

                assert "milestone" in result.lower() or "adoption" in result.lower()

    @pytest.mark.asyncio
    async def test_track_custom_milestones(self, mock_context, mock_customer_data):
        """Test tracking custom adoption milestones"""
        client_id = mock_customer_data["client_id"]
        custom_milestones = [
            {"id": "m1", "name": "First API Call", "threshold": 1},
            {"id": "m2", "name": "10 Active Users", "threshold": 10},
            {"id": "m3", "name": "Feature Complete", "threshold": 100}
        ]

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            with patch.object(health_segmentation_tools, '_get_customer_from_db') as mock_get:
                mock_customer = MagicMock()
                mock_get.return_value = mock_customer

                mcp = health_segmentation_tools.get_enhanced_agent()
                result = await mcp.call_tool(
                    "track_adoption_milestones",
                    arguments={
                        "client_id": client_id,
                        "milestone_framework": "custom",
                        "custom_milestones": custom_milestones
                    },
                    ctx=mock_context
                )

                assert "milestone" in result.lower()


@pytest.mark.unit
class TestHealthScoreComponents:
    """Test suite for health score component calculations"""

    def test_usage_score_calculation(self, mock_customer_data):
        """Test usage score calculation logic"""
        client_id = mock_customer_data["client_id"]

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            score = health_segmentation_tools._calculate_usage_score_from_db(mock_session, client_id, days=30)

            assert 0 <= score <= 100

    def test_engagement_score_calculation(self, mock_customer_data):
        """Test engagement score calculation logic"""
        client_id = mock_customer_data["client_id"]

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            score = health_segmentation_tools._calculate_engagement_score_from_db(mock_session, client_id, days=30)

            assert 0 <= score <= 100

    def test_support_score_calculation(self, mock_customer_data):
        """Test support score calculation logic"""
        client_id = mock_customer_data["client_id"]

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            score = health_segmentation_tools._calculate_support_score_from_db(mock_session, client_id, days=30)

            assert 0 <= score <= 100

    def test_satisfaction_score_calculation(self, mock_customer_data):
        """Test satisfaction score calculation logic"""
        client_id = mock_customer_data["client_id"]

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            score = health_segmentation_tools._calculate_satisfaction_score_from_db(mock_session, client_id, days=90)

            assert 0 <= score <= 100

    def test_payment_score_calculation(self, mock_customer_data):
        """Test payment score calculation logic"""
        client_id = mock_customer_data["client_id"]

        with patch.object(health_segmentation_tools, '_get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session

            score = health_segmentation_tools._calculate_payment_score_from_db(mock_session, client_id)

            assert 0 <= score <= 100


@pytest.mark.unit
class TestSegmentationHelpers:
    """Test suite for segmentation helper functions"""

    def test_pareto_calculation(self):
        """Test Pareto 80/20 calculation for segments"""
        from src.models.customer_models import CustomerSegment

        segments = [
            CustomerSegment(
                segment_id=f"seg_{i}",
                segment_name=f"Segment {i}",
                segment_type="test",
                criteria={},
                total_arr=100000 * (10 - i),
                customer_count=10
            )
            for i in range(5)
        ]

        pareto = health_segmentation_tools._calculate_pareto(segments)

        assert "top_20_percent" in pareto
        assert "revenue_concentration" in pareto

    def test_channel_recommendations(self):
        """Test communication channel recommendations"""
        from src.models.customer_models import CustomerSegment

        segment = CustomerSegment(
            segment_id="seg_enterprise",
            segment_name="Enterprise Customers",
            segment_type="value_based",
            criteria={"min_arr": 100000},
            total_arr=5000000,
            customer_count=25
        )

        channels = health_segmentation_tools._recommend_channels(segment)

        assert isinstance(channels, list)
        assert len(channels) > 0

    def test_content_recommendations(self):
        """Test content recommendations for segments"""
        from src.models.customer_models import CustomerSegment

        segment = CustomerSegment(
            segment_id="seg_high_value",
            segment_name="High Value SaaS",
            segment_type="value_based",
            criteria={},
            total_arr=3000000,
            customer_count=30
        )

        content = health_segmentation_tools._recommend_content(segment, "value_based")

        assert isinstance(content, dict)
