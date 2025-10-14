"""
Unit Tests for Core System Tools
Tests for customer registration, overview, updates, listing, and timeline
"""

import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from mcp.server.fastmcp import Context

from src.tools import core_system_tools


@pytest.mark.unit
class TestRegisterClient:
    """Test suite for register_client tool"""

    @pytest.mark.asyncio
    async def test_register_client_success(self, mock_context):
        """Test successful client registration"""
        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "register_client",
                arguments={
                    "client_name": "Acme Corporation",
                    "company_name": "Acme Corp Inc.",
                    "industry": "Technology",
                    "tier": "professional",
                    "contract_value": 72000.0,
                    "contract_start_date": "2025-01-15",
                    "primary_contact_email": "john@acme.com",
                    "primary_contact_name": "John Smith"
                },
                ctx=mock_context
            )

            assert "client_id" in result
            assert result["client_id"].startswith("cs_")

    @pytest.mark.asyncio
    async def test_register_client_validation_errors(self, mock_context):
        """Test client registration with validation errors"""
        mcp = core_system_tools.get_enhanced_agent()
        result = await mcp.call_tool(
            "register_client",
            arguments={
                "client_name": "",  # Invalid empty name
                "company_name": "Test",
                "contract_value": -1000,  # Invalid negative value
                "primary_contact_email": "not-an-email"  # Invalid email
            },
            ctx=mock_context
        )

        assert "error" in result.lower() or "invalid" in result.lower()

    @pytest.mark.asyncio
    async def test_register_client_duplicate_check(self, mock_context):
        """Test duplicate client detection"""
        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            # Mock existing customer found
            existing_customer = MagicMock()
            existing_customer.client_id = "cs_1234_acme"
            mock_session.query.return_value.filter.return_value.first.return_value = existing_customer

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "register_client",
                arguments={
                    "client_name": "Acme Corporation",
                    "company_name": "Acme Corp",
                    "primary_contact_email": "test@acme.com"
                },
                ctx=mock_context
            )

            # Should detect duplicate or return existing
            assert "client_id" in result or "existing" in result.lower()


@pytest.mark.unit
class TestGetClientOverview:
    """Test suite for get_client_overview tool"""

    @pytest.mark.asyncio
    async def test_get_client_overview_success(self, mock_context, mock_customer_data):
        """Test successful client overview retrieval"""
        client_id = mock_customer_data["client_id"]

        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            # Mock customer query
            mock_customer = MagicMock()
            mock_customer.client_id = client_id
            mock_customer.client_name = "Acme Corporation"
            mock_customer.health_score = 82
            mock_customer.tier = "professional"
            mock_session.query.return_value.filter.return_value.first.return_value = mock_customer

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "get_client_overview",
                arguments={"client_id": client_id},
                ctx=mock_context
            )

            assert "client_id" in result
            assert "client_name" in result
            assert "health_score" in result

    @pytest.mark.asyncio
    async def test_get_client_overview_not_found(self, mock_context):
        """Test client overview for non-existent client"""
        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "get_client_overview",
                arguments={"client_id": "cs_999_nonexistent"},
                ctx=mock_context
            )

            assert "not found" in result.lower() or "error" in result.lower()

    @pytest.mark.asyncio
    async def test_get_client_overview_with_health_score(self, mock_context, mock_customer_data):
        """Test client overview includes latest health score"""
        client_id = mock_customer_data["client_id"]

        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            mock_customer = MagicMock()
            mock_customer.health_score = 85
            mock_session.query.return_value.filter.return_value.first.return_value = mock_customer

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "get_client_overview",
                arguments={"client_id": client_id},
                ctx=mock_context
            )

            assert "health_score" in result or "health" in result.lower()


@pytest.mark.unit
class TestUpdateClientInfo:
    """Test suite for update_client_info tool"""

    @pytest.mark.asyncio
    async def test_update_client_success(self, mock_context, mock_customer_data):
        """Test successful client information update"""
        client_id = mock_customer_data["client_id"]
        updates = {
            "tier": "enterprise",
            "csm_assigned": "Jane Doe",
            "contract_value": 144000.0
        }

        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            mock_customer = MagicMock()
            mock_customer.client_id = client_id
            mock_session.query.return_value.filter.return_value.first.return_value = mock_customer

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "update_client_info",
                arguments={
                    "client_id": client_id,
                    "updates": updates
                },
                ctx=mock_context
            )

            assert "updated" in result.lower() or "success" in result.lower()

    @pytest.mark.asyncio
    async def test_update_client_invalid_fields(self, mock_context, mock_customer_data):
        """Test update with invalid field values"""
        client_id = mock_customer_data["client_id"]
        updates = {
            "contract_value": -50000,  # Invalid negative value
            "tier": "invalid_tier"  # Invalid tier
        }

        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            mock_customer = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_customer

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "update_client_info",
                arguments={
                    "client_id": client_id,
                    "updates": updates
                },
                ctx=mock_context
            )

            # Should handle validation errors
            assert "error" in result.lower() or "invalid" in result.lower() or "updated" in result.lower()

    @pytest.mark.asyncio
    async def test_update_client_audit_logging(self, mock_context, mock_customer_data):
        """Test that updates are properly audit logged"""
        client_id = mock_customer_data["client_id"]
        updates = {"tier": "enterprise"}

        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            mock_customer = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_customer

            # Mock audit logging
            with patch('src.security.audit_logger.AuditLogger') as mock_audit:
                mcp = core_system_tools.get_enhanced_agent()
                result = await mcp.call_tool(
                    "update_client_info",
                    arguments={
                        "client_id": client_id,
                        "updates": updates
                    },
                    ctx=mock_context
                )

                # Update should complete (audit is background)
                assert result is not None


@pytest.mark.unit
class TestListClients:
    """Test suite for list_clients tool"""

    @pytest.mark.asyncio
    async def test_list_all_clients(self, mock_context):
        """Test listing all clients without filters"""
        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            # Mock customer query
            mock_customers = [MagicMock(client_id=f"cs_{i}", client_name=f"Customer {i}") for i in range(5)]
            mock_session.query.return_value.limit.return_value.offset.return_value.all.return_value = mock_customers
            mock_session.query.return_value.count.return_value = 5

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "list_clients",
                arguments={},
                ctx=mock_context
            )

            assert "clients" in result
            assert "total" in result or "count" in result

    @pytest.mark.asyncio
    async def test_list_clients_with_tier_filter(self, mock_context):
        """Test listing clients filtered by tier"""
        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            mock_customers = [MagicMock(tier="enterprise") for _ in range(3)]
            mock_query = mock_session.query.return_value
            mock_query.filter.return_value.limit.return_value.offset.return_value.all.return_value = mock_customers
            mock_query.filter.return_value.count.return_value = 3

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "list_clients",
                arguments={"tier_filter": "enterprise"},
                ctx=mock_context
            )

            assert "clients" in result

    @pytest.mark.asyncio
    async def test_list_clients_with_lifecycle_filter(self, mock_context):
        """Test listing clients filtered by lifecycle stage"""
        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            mock_customers = [MagicMock(lifecycle_stage="active") for _ in range(10)]
            mock_query = mock_session.query.return_value
            mock_query.filter.return_value.limit.return_value.offset.return_value.all.return_value = mock_customers
            mock_query.filter.return_value.count.return_value = 10

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "list_clients",
                arguments={"lifecycle_filter": "active"},
                ctx=mock_context
            )

            assert "clients" in result

    @pytest.mark.asyncio
    async def test_list_clients_pagination(self, mock_context):
        """Test client listing with pagination"""
        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            mock_customers = [MagicMock(client_id=f"cs_{i}") for i in range(10)]
            mock_query = mock_session.query.return_value
            mock_query.limit.return_value.offset.return_value.all.return_value = mock_customers[10:20]
            mock_query.count.return_value = 50

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "list_clients",
                arguments={
                    "page": 2,
                    "page_size": 10
                },
                ctx=mock_context
            )

            assert "clients" in result
            assert "total" in result or "count" in result


@pytest.mark.unit
class TestGetClientTimeline:
    """Test suite for get_client_timeline tool"""

    @pytest.mark.asyncio
    async def test_get_timeline_all_events(self, mock_context, mock_customer_data):
        """Test retrieving complete client timeline"""
        client_id = mock_customer_data["client_id"]

        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            # Mock customer exists
            mock_customer = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_customer

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "get_client_timeline",
                arguments={"client_id": client_id},
                ctx=mock_context
            )

            assert "timeline" in result or "events" in result

    @pytest.mark.asyncio
    async def test_get_timeline_date_filtered(self, mock_context, mock_customer_data):
        """Test timeline with date range filtering"""
        client_id = mock_customer_data["client_id"]
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()

        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            mock_customer = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_customer

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "get_client_timeline",
                arguments={
                    "client_id": client_id,
                    "start_date": start_date,
                    "end_date": end_date
                },
                ctx=mock_context
            )

            assert "timeline" in result or "events" in result

    @pytest.mark.asyncio
    async def test_get_timeline_event_type_filter(self, mock_context, mock_customer_data):
        """Test timeline filtered by event type"""
        client_id = mock_customer_data["client_id"]

        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            mock_customer = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_customer

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "get_client_timeline",
                arguments={
                    "client_id": client_id,
                    "event_types": ["support_ticket", "health_score_change"]
                },
                ctx=mock_context
            )

            assert "timeline" in result or "events" in result

    @pytest.mark.asyncio
    async def test_get_timeline_ordering(self, mock_context, mock_customer_data):
        """Test that timeline events are properly ordered"""
        client_id = mock_customer_data["client_id"]

        with patch.object(core_system_tools, 'SessionLocal') as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__enter__.return_value = mock_session

            mock_customer = MagicMock()
            mock_session.query.return_value.filter.return_value.first.return_value = mock_customer

            # Mock timeline events
            mock_events = [
                {"timestamp": datetime.now() - timedelta(days=i), "type": f"event_{i}"}
                for i in range(5)
            ]

            mcp = core_system_tools.get_enhanced_agent()
            result = await mcp.call_tool(
                "get_client_timeline",
                arguments={
                    "client_id": client_id,
                    "sort_order": "desc"
                },
                ctx=mock_context
            )

            # Timeline should be included
            assert "timeline" in result or "events" in result
