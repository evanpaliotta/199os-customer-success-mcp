"""
Unit Tests for Core System Tools

Tests for customer registration, overview, updates, listing, and timeline functionality.
"""

import pytest
from datetime import datetime, timedelta, date
from unittest.mock import Mock, AsyncMock, patch
from mcp.server.fastmcp import Context

from src.tools import core_system_tools
from src.security.input_validation import ValidationError


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_context():
    """Create a mock MCP Context for testing."""
    context = AsyncMock(spec=Context)
    context.info = AsyncMock()
    context.warn = AsyncMock()
    context.error = AsyncMock()
    return context


@pytest.fixture
def valid_client_data():
    """Sample valid client registration data."""
    return {
        "client_name": "Test Corporation",
        "company_name": "Test Corp Inc.",
        "industry": "Technology",
        "contract_value": 50000.0,
        "contract_start_date": date.today().strftime("%Y-%m-%d"),
        "contract_end_date": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d"),
        "primary_contact_email": "test@testcorp.com",
        "primary_contact_name": "John Doe",
        "tier": "professional"
    }


@pytest.fixture
def mock_mcp():
    """Create a mock MCP instance with tool registration."""
    mcp = Mock()
    mcp.tool = lambda: lambda func: func  # Simple decorator that returns the function
    return mcp


# ============================================================================
# Tests for register_client
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_client_success(mock_context, valid_client_data):
    """Test successful client registration."""
    # Create a mock MCP and register tools
    mcp = Mock()
    registered_func = None

    def tool_decorator():
        def decorator(func):
            nonlocal registered_func
            registered_func = func
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    # Call the registered function
    result = await registered_func(
        mock_context,
        **valid_client_data
    )

    # Assertions
    assert result['status'] == 'success'
    assert 'client_id' in result
    assert result['client_id'].startswith('cs_')
    assert 'client_record' in result
    assert result['client_record']['client_name'] == valid_client_data['client_name']
    assert result['client_record']['tier'] == valid_client_data['tier'].lower()
    assert result['client_record']['contract_value'] == valid_client_data['contract_value']
    assert 'next_steps' in result
    assert len(result['next_steps']) > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_client_invalid_tier(mock_context):
    """Test client registration with invalid tier."""
    mcp = Mock()
    registered_func = None

    def tool_decorator():
        def decorator(func):
            nonlocal registered_func
            registered_func = func
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    result = await registered_func(
        mock_context,
        client_name="Test Client",
        company_name="Test Company",
        tier="invalid_tier"
    )

    assert result['status'] == 'failed'
    assert 'Invalid tier' in result['error']


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_client_default_contract_dates(mock_context):
    """Test client registration with default contract dates."""
    mcp = Mock()
    registered_func = None

    def tool_decorator():
        def decorator(func):
            nonlocal registered_func
            registered_func = func
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    result = await registered_func(
        mock_context,
        client_name="Test Client",
        company_name="Test Company",
        industry="Technology"
    )

    assert result['status'] == 'success'
    assert 'contract_start_date' in result['client_record']
    assert 'contract_end_date' in result['client_record']

    # Verify default 1-year contract
    start = datetime.strptime(result['client_record']['contract_start_date'], "%Y-%m-%d")
    end = datetime.strptime(result['client_record']['contract_end_date'], "%Y-%m-%d")
    duration_days = (end - start).days
    assert 360 <= duration_days <= 370  # Allow some tolerance


@pytest.mark.unit
@pytest.mark.asyncio
async def test_register_client_generates_unique_id(mock_context):
    """Test that each registration generates a unique client ID."""
    mcp = Mock()
    registered_func = None

    def tool_decorator():
        def decorator(func):
            nonlocal registered_func
            registered_func = func
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    # Register two clients
    result1 = await registered_func(
        mock_context,
        client_name="Client One",
        company_name="Company One"
    )

    result2 = await registered_func(
        mock_context,
        client_name="Client Two",
        company_name="Company Two"
    )

    assert result1['status'] == 'success'
    assert result2['status'] == 'success'
    assert result1['client_id'] != result2['client_id']


# ============================================================================
# Tests for get_client_overview
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_client_overview_success(mock_context):
    """Test successful retrieval of client overview."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    # get_client_overview is the second registered function
    get_overview_func = registered_funcs[1]

    result = await get_overview_func(
        mock_context,
        client_id="cs_1696800000_test"
    )

    assert result['status'] == 'success'
    assert 'client_overview' in result
    assert 'health_components' in result
    assert 'insights' in result
    assert result['client_overview']['client_id'] == "cs_1696800000_test"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_client_overview_invalid_client_id(mock_context):
    """Test client overview with invalid client ID."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    get_overview_func = registered_funcs[1]

    # Test with invalid client ID format
    result = await get_overview_func(
        mock_context,
        client_id="invalid_id"
    )

    assert result['status'] == 'failed'
    assert 'Invalid client_id' in result['error']


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_client_overview_contains_all_sections(mock_context):
    """Test that client overview contains all expected data sections."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    get_overview_func = registered_funcs[1]

    result = await get_overview_func(
        mock_context,
        client_id="cs_1696800000_test"
    )

    assert result['status'] == 'success'
    overview = result['client_overview']

    # Check all major sections exist
    assert 'health_score' in overview
    assert 'lifecycle_stage' in overview
    assert 'onboarding' in overview
    assert 'engagement' in overview
    assert 'support' in overview
    assert 'product_usage' in overview
    assert 'revenue' in overview
    assert 'communication' in overview


# ============================================================================
# Tests for update_client_info
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_client_info_success(mock_context):
    """Test successful client information update."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    update_func = registered_funcs[2]

    updates = {
        "client_name": "Updated Client Name",
        "tier": "enterprise",
        "contract_value": 100000.0
    }

    result = await update_func(
        mock_context,
        client_id="cs_1696800000_test",
        updates=updates
    )

    assert result['status'] == 'success'
    assert 'updated_fields' in result
    assert set(result['updated_fields']) == set(updates.keys())
    assert 'updated_record' in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_client_info_invalid_fields(mock_context):
    """Test update with invalid/disallowed fields."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    update_func = registered_funcs[2]

    updates = {
        "health_score": 100,  # Not allowed to update directly
        "invalid_field": "value"
    }

    result = await update_func(
        mock_context,
        client_id="cs_1696800000_test",
        updates=updates
    )

    assert result['status'] == 'failed'
    assert 'Invalid fields' in result['error']


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_client_info_invalid_tier(mock_context):
    """Test update with invalid tier value."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    update_func = registered_funcs[2]

    updates = {"tier": "invalid_tier"}

    result = await update_func(
        mock_context,
        client_id="cs_1696800000_test",
        updates=updates
    )

    assert result['status'] == 'failed'
    assert 'Invalid tier' in result['error']


@pytest.mark.unit
@pytest.mark.asyncio
async def test_update_client_info_adds_timestamp(mock_context):
    """Test that update adds updated_at timestamp."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    update_func = registered_funcs[2]

    updates = {"client_name": "New Name"}

    result = await update_func(
        mock_context,
        client_id="cs_1696800000_test",
        updates=updates
    )

    assert result['status'] == 'success'
    assert 'updated_at' in result['updated_record']
    assert 'audit' in result
    assert 'updated_at' in result['audit']


# ============================================================================
# Tests for list_clients
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_clients_no_filters(mock_context):
    """Test listing all clients without filters."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    list_func = registered_funcs[3]

    result = await list_func(mock_context)

    assert result['status'] == 'success'
    assert 'clients' in result
    assert 'pagination' in result
    assert 'summary' in result
    assert len(result['clients']) > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_clients_tier_filter(mock_context):
    """Test listing clients with tier filter."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    list_func = registered_funcs[3]

    result = await list_func(
        mock_context,
        tier_filter="professional"
    )

    assert result['status'] == 'success'
    # All returned clients should match the filter
    for client in result['clients']:
        assert client['tier'] == 'professional'


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_clients_health_score_range(mock_context):
    """Test listing clients with health score range filter."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    list_func = registered_funcs[3]

    result = await list_func(
        mock_context,
        health_score_min=80,
        health_score_max=100
    )

    assert result['status'] == 'success'
    for client in result['clients']:
        assert 80 <= client['health_score'] <= 100


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_clients_pagination(mock_context):
    """Test client listing with pagination."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    list_func = registered_funcs[3]

    result = await list_func(
        mock_context,
        limit=2,
        offset=0
    )

    assert result['status'] == 'success'
    assert result['pagination']['limit'] == 2
    assert result['pagination']['offset'] == 0
    assert result['pagination']['returned_count'] <= 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_clients_invalid_limit(mock_context):
    """Test listing with invalid limit parameter."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    list_func = registered_funcs[3]

    # Test limit too high
    result = await list_func(
        mock_context,
        limit=2000
    )

    assert result['status'] == 'failed'
    assert 'limit must be between 1 and 1000' in result['error']


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_clients_summary_statistics(mock_context):
    """Test that list_clients returns accurate summary statistics."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    list_func = registered_funcs[3]

    result = await list_func(mock_context)

    assert result['status'] == 'success'
    summary = result['summary']

    assert 'total_clients' in summary
    assert 'average_health_score' in summary
    assert 'total_arr' in summary
    assert 'lifecycle_breakdown' in summary


# ============================================================================
# Tests for get_client_timeline
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_client_timeline_success(mock_context):
    """Test successful retrieval of client timeline."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    timeline_func = registered_funcs[4]

    result = await timeline_func(
        mock_context,
        client_id="cs_1696800000_test"
    )

    assert result['status'] == 'success'
    assert 'timeline' in result
    assert 'summary' in result
    assert len(result['timeline']) > 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_client_timeline_event_types_filter(mock_context):
    """Test timeline with event type filtering."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    timeline_func = registered_funcs[4]

    result = await timeline_func(
        mock_context,
        client_id="cs_1696800000_test",
        event_types=["onboarding", "support"]
    )

    assert result['status'] == 'success'
    for event in result['timeline']:
        assert event['event_type'] in ["onboarding", "support"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_client_timeline_invalid_event_type(mock_context):
    """Test timeline with invalid event type."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    timeline_func = registered_funcs[4]

    result = await timeline_func(
        mock_context,
        client_id="cs_1696800000_test",
        event_types=["invalid_type"]
    )

    assert result['status'] == 'failed'
    assert 'Invalid event_types' in result['error']


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_client_timeline_date_range(mock_context):
    """Test timeline with date range filtering."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    timeline_func = registered_funcs[4]

    start_date = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    result = await timeline_func(
        mock_context,
        client_id="cs_1696800000_test",
        start_date=start_date,
        end_date=end_date
    )

    assert result['status'] == 'success'
    assert result['summary']['date_range']['start'] == start_date
    assert result['summary']['date_range']['end'] == end_date


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_client_timeline_invalid_date_format(mock_context):
    """Test timeline with invalid date format."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    timeline_func = registered_funcs[4]

    result = await timeline_func(
        mock_context,
        client_id="cs_1696800000_test",
        start_date="invalid-date"
    )

    assert result['status'] == 'failed'
    assert 'YYYY-MM-DD format' in result['error']


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_client_timeline_sentiment_analysis(mock_context):
    """Test that timeline includes sentiment analysis."""
    mcp = Mock()
    registered_funcs = []

    def tool_decorator():
        def decorator(func):
            registered_funcs.append(func)
            return func
        return decorator

    mcp.tool = tool_decorator
    core_system_tools.register_tools(mcp)

    timeline_func = registered_funcs[4]

    result = await timeline_func(
        mock_context,
        client_id="cs_1696800000_test"
    )

    assert result['status'] == 'success'
    assert 'sentiment' in result['summary']
    sentiment = result['summary']['sentiment']

    assert 'positive_events' in sentiment
    assert 'negative_events' in sentiment
    assert 'neutral_events' in sentiment
    assert 'overall_sentiment' in sentiment
