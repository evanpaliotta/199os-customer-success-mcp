# Performance Monitoring Integration Examples

This document provides examples of how to integrate performance monitoring into Customer Success MCP tools.

## Quick Start

### Import the Decorators

```python
from src.monitoring import (
    monitor_tool_execution,
    monitor_database_query,
    monitor_api_call,
    record_cache_hit,
    record_cache_miss
)
```

## Tool Monitoring Examples

### Example 1: Simple Tool Monitoring

```python
from mcp.server.fastmcp import Context
from src.monitoring import monitor_tool_execution

def register_tools(mcp):
    """Register tools with performance monitoring"""

    @mcp.tool()
    @monitor_tool_execution()
    async def register_client(
        ctx: Context,
        client_name: str,
        industry: str
    ):
        """
        Register a new customer client.
        This tool is automatically monitored for performance.
        """
        # Tool implementation
        client_id = generate_client_id(client_name)

        return {
            'status': 'success',
            'client_id': client_id
        }
```

### Example 2: Tool with Custom Name

```python
@mcp.tool()
@monitor_tool_execution(tool_name="register_customer")
async def register_client(ctx: Context, client_name: str):
    """Custom tool name for metrics"""
    # Implementation
    pass
```

### Example 3: Multiple Decorators

```python
from src.monitoring import monitor_tool_execution, monitor_database_query

@mcp.tool()
@monitor_tool_execution()
async def get_client_overview(ctx: Context, client_id: str):
    """Tool with nested database monitoring"""

    # This DB query is also monitored
    client_data = await fetch_client_from_db(client_id)

    return {
        'status': 'success',
        'client': client_data
    }

@monitor_database_query("select")
async def fetch_client_from_db(client_id: str):
    """Database query with monitoring"""
    # Database implementation
    return client_data
```

## Database Monitoring Examples

### Example 4: SELECT Query

```python
from src.monitoring import monitor_database_query

@monitor_database_query("select")
async def get_customer_by_id(client_id: str):
    """
    Retrieve customer from database.
    Monitors query duration and logs slow queries (>50ms).
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT * FROM customers WHERE client_id = $1",
            client_id
        )
    return result
```

### Example 5: INSERT Query

```python
@monitor_database_query("insert")
async def create_customer(customer_data: dict):
    """
    Insert new customer record.
    Tracks insert performance metrics.
    """
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO customers (client_id, name, tier, created_at)
            VALUES ($1, $2, $3, $4)
            """,
            customer_data['client_id'],
            customer_data['name'],
            customer_data['tier'],
            datetime.now()
        )
    return {'status': 'success'}
```

### Example 6: Complex Query

```python
@monitor_database_query("complex")
async def calculate_health_metrics(client_id: str):
    """
    Complex query with joins and aggregations.
    Important to monitor for performance degradation.
    """
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT
                c.client_id,
                AVG(u.usage_score) as avg_usage,
                AVG(e.engagement_score) as avg_engagement,
                COUNT(DISTINCT t.ticket_id) as ticket_count
            FROM customers c
            LEFT JOIN usage_metrics u ON c.client_id = u.client_id
            LEFT JOIN engagement_metrics e ON c.client_id = e.client_id
            LEFT JOIN tickets t ON c.client_id = t.client_id
            WHERE c.client_id = $1
            GROUP BY c.client_id
            """,
            client_id
        )
    return result
```

## Platform API Monitoring Examples

### Example 7: Zendesk API Call

```python
from src.monitoring import monitor_api_call

class ZendeskClient:
    """Zendesk integration with performance monitoring"""

    @monitor_api_call("zendesk", "create_ticket")
    async def create_ticket(self, data: dict):
        """
        Create ticket in Zendesk.
        Monitors API call duration and errors.
        """
        response = await self.zenpy_client.tickets.create(
            subject=data['subject'],
            description=data['description'],
            priority=data.get('priority', 'normal')
        )
        return response

    @monitor_api_call("zendesk", "get_ticket")
    async def get_ticket(self, ticket_id: str):
        """Get ticket by ID"""
        response = await self.zenpy_client.tickets(id=ticket_id)
        return response
```

### Example 8: Intercom API Call

```python
@monitor_api_call("intercom", "send_message")
async def send_intercom_message(user_id: str, message: str):
    """
    Send message via Intercom.
    Tracks API performance and rate limit errors.
    """
    from intercom.client import Client
    intercom = Client(personal_access_token=INTERCOM_TOKEN)

    result = intercom.messages.create(**{
        "message_type": "inapp",
        "from": {"type": "admin", "id": admin_id},
        "to": {"type": "user", "id": user_id},
        "body": message
    })

    return result
```

### Example 9: SendGrid Email

```python
@monitor_api_call("sendgrid", "send_email")
async def send_email(to_email: str, subject: str, content: str):
    """
    Send email via SendGrid.
    Monitors delivery time and tracks failures.
    """
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    message = Mail(
        from_email='noreply@yourcompany.com',
        to_emails=to_email,
        subject=subject,
        html_content=content
    )

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)

    return {
        'status_code': response.status_code,
        'message_id': response.headers.get('X-Message-Id')
    }
```

## Cache Monitoring Examples

### Example 10: Redis Caching with Monitoring

```python
from src.monitoring import record_cache_hit, record_cache_miss
import redis.asyncio as redis

class CacheManager:
    """Cache manager with performance tracking"""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get_cached_health_score(self, client_id: str):
        """
        Get health score from cache with monitoring.
        Records cache hits and misses for tracking effectiveness.
        """
        cache_key = f"health_score:{client_id}"

        # Try to get from cache
        cached_value = await self.redis.get(cache_key)

        if cached_value:
            record_cache_hit("redis")
            return float(cached_value)
        else:
            record_cache_miss("redis")

            # Calculate health score (expensive operation)
            health_score = await calculate_health_score(client_id)

            # Cache for 1 hour
            await self.redis.setex(cache_key, 3600, health_score)

            return health_score

    async def invalidate_cache(self, client_id: str):
        """Invalidate cache when data changes"""
        cache_key = f"health_score:{client_id}"
        await self.redis.delete(cache_key)
```

### Example 11: Memory Cache with Monitoring

```python
from functools import lru_cache
from src.monitoring import record_cache_hit, record_cache_miss

class MemoryCache:
    """In-memory cache with monitoring"""

    def __init__(self):
        self.cache = {}

    async def get_or_compute(self, key: str, compute_func):
        """
        Get from cache or compute value.
        Tracks hit rate for optimization.
        """
        if key in self.cache:
            record_cache_hit("memory")
            return self.cache[key]

        record_cache_miss("memory")

        # Compute expensive value
        value = await compute_func()

        # Store in cache
        self.cache[key] = value

        return value
```

## Health Score Monitoring Example

### Example 12: Health Score Calculation

```python
from src.monitoring import monitor_health_score_calculation

async def calculate_health_score(
    client_id: str,
    usage_score: float,
    engagement_score: float,
    support_score: float,
    satisfaction_score: float,
    payment_score: float
):
    """
    Calculate customer health score.
    Target: <100ms (per development plan)
    """
    with monitor_health_score_calculation():
        # Weight configuration
        weights = {
            'usage': 0.25,
            'engagement': 0.20,
            'support': 0.20,
            'satisfaction': 0.20,
            'payment': 0.15
        }

        # Calculate weighted score
        health_score = (
            usage_score * weights['usage'] +
            engagement_score * weights['engagement'] +
            support_score * weights['support'] +
            satisfaction_score * weights['satisfaction'] +
            payment_score * weights['payment']
        )

        return round(health_score, 2)
```

## Complete Integration Example

### Example 13: Full Tool with All Monitoring

```python
from mcp.server.fastmcp import Context
from src.monitoring import (
    monitor_tool_execution,
    monitor_database_query,
    monitor_api_call,
    record_cache_hit,
    record_cache_miss
)

def register_tools(mcp):
    """Register fully monitored tools"""

    @mcp.tool()
    @monitor_tool_execution()
    async def create_support_ticket(
        ctx: Context,
        client_id: str,
        subject: str,
        description: str,
        priority: str = "normal"
    ):
        """
        Create support ticket with full monitoring.

        Monitors:
        - Overall tool execution time
        - Database insert performance
        - Zendesk API call performance
        - Cache operations
        """
        await ctx.info(f"Creating support ticket for {client_id}")

        # 1. Check cache for client info
        client_info = await get_cached_client(client_id)

        # 2. Create ticket in database
        ticket_id = await store_ticket_in_db({
            'client_id': client_id,
            'subject': subject,
            'description': description,
            'priority': priority,
            'status': 'open',
            'created_at': datetime.now()
        })

        # 3. Create ticket in Zendesk
        zendesk_ticket = await create_zendesk_ticket({
            'subject': subject,
            'description': description,
            'priority': priority,
            'requester': client_info['primary_contact_email']
        })

        # 4. Link Zendesk ticket ID
        await link_zendesk_ticket(ticket_id, zendesk_ticket['id'])

        return {
            'status': 'success',
            'ticket_id': ticket_id,
            'zendesk_ticket_id': zendesk_ticket['id']
        }

# Helper functions with monitoring

@monitor_database_query("insert")
async def store_ticket_in_db(ticket_data: dict):
    """Store ticket in database"""
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            INSERT INTO tickets (client_id, subject, description, priority, status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING ticket_id
            """,
            ticket_data['client_id'],
            ticket_data['subject'],
            ticket_data['description'],
            ticket_data['priority'],
            ticket_data['status'],
            ticket_data['created_at']
        )
        return result['ticket_id']

@monitor_api_call("zendesk", "create_ticket")
async def create_zendesk_ticket(ticket_data: dict):
    """Create ticket in Zendesk"""
    from zenpy import Zenpy
    from zenpy.lib.api_objects import Ticket

    zenpy_client = Zenpy(
        subdomain=ZENDESK_SUBDOMAIN,
        email=ZENDESK_EMAIL,
        token=ZENDESK_TOKEN
    )

    ticket = Ticket(
        subject=ticket_data['subject'],
        description=ticket_data['description'],
        priority=ticket_data['priority']
    )

    created_ticket = zenpy_client.tickets.create(ticket)

    return {
        'id': created_ticket.id,
        'url': created_ticket.url
    }

async def get_cached_client(client_id: str):
    """Get client info from cache"""
    cache_key = f"client:{client_id}"
    cached = await redis.get(cache_key)

    if cached:
        record_cache_hit("redis")
        return json.loads(cached)

    record_cache_miss("redis")

    # Fetch from database
    client = await fetch_client_from_db(client_id)

    # Cache for 5 minutes
    await redis.setex(cache_key, 300, json.dumps(client))

    return client
```

## Error Handling with Monitoring

### Example 14: Proper Error Handling

```python
from src.monitoring import monitor_tool_execution

@mcp.tool()
@monitor_tool_execution()
async def risky_operation(ctx: Context, data: dict):
    """
    Tool with proper error handling.
    Errors are automatically tracked in metrics.
    """
    try:
        # Validate input
        if not data.get('client_id'):
            raise ValueError("client_id is required")

        # Perform operation
        result = await perform_operation(data)

        return {
            'status': 'success',
            'result': result
        }

    except ValueError as e:
        # Validation errors are tracked
        logger.error("Validation error", error=str(e))
        return {
            'status': 'failed',
            'error': f"Validation error: {str(e)}"
        }

    except Exception as e:
        # All exceptions are tracked in error_counter metric
        logger.error("Unexpected error", error=str(e))
        return {
            'status': 'failed',
            'error': f"Internal error: {str(e)}"
        }
```

## Best Practices

### 1. Always Monitor Tools
```python
# GOOD - Tool is monitored
@mcp.tool()
@monitor_tool_execution()
async def my_tool(ctx: Context):
    pass

# BAD - Tool is not monitored
@mcp.tool()
async def my_tool(ctx: Context):
    pass
```

### 2. Use Appropriate Query Types
```python
# GOOD - Specific query type
@monitor_database_query("select")
async def get_data(): pass

@monitor_database_query("insert")
async def create_data(): pass

@monitor_database_query("update")
async def modify_data(): pass

# BAD - Generic query type
@monitor_database_query("query")
async def get_data(): pass
```

### 3. Always Record Cache Operations
```python
# GOOD - Records cache hit/miss
value = await cache.get(key)
if value:
    record_cache_hit("redis")
else:
    record_cache_miss("redis")

# BAD - Doesn't record metrics
value = await cache.get(key)
if value:
    return value
```

### 4. Use Descriptive Integration Names
```python
# GOOD - Clear integration and endpoint
@monitor_api_call("zendesk", "create_ticket")
@monitor_api_call("intercom", "send_message")
@monitor_api_call("sendgrid", "send_email")

# BAD - Generic names
@monitor_api_call("api", "call")
@monitor_api_call("external", "request")
```

## Testing Monitored Tools

### Example 15: Test with Monitoring

```python
import pytest
from src.monitoring import PROMETHEUS_AVAILABLE

@pytest.mark.asyncio
async def test_monitored_tool():
    """Test that monitoring doesn't break functionality"""

    # Tool should work even if Prometheus is not installed
    result = await register_client(
        ctx=None,
        client_name="Test Client",
        industry="Technology"
    )

    assert result['status'] == 'success'
    assert 'client_id' in result

@pytest.mark.skipif(not PROMETHEUS_AVAILABLE, reason="Prometheus not installed")
def test_metrics_recorded():
    """Test that metrics are actually recorded"""
    from src.monitoring.performance_monitor import tool_execution_counter

    # Execute tool
    result = await register_client(ctx=None, client_name="Test")

    # Verify metric was incremented
    # (This requires accessing internal Prometheus state)
    assert result['status'] == 'success'
```

## Deployment Checklist

When deploying tools with monitoring:

- [ ] All tools decorated with `@monitor_tool_execution()`
- [ ] All database queries decorated with `@monitor_database_query()`
- [ ] All API calls decorated with `@monitor_api_call()`
- [ ] Cache operations call `record_cache_hit()` and `record_cache_miss()`
- [ ] prometheus-client installed in requirements.txt
- [ ] Metrics server started in initialization
- [ ] Grafana dashboard imported
- [ ] Prometheus configured to scrape metrics
- [ ] Alerts configured for slow operations
- [ ] Performance baselines established

## Next Steps

1. Review the complete monitoring setup: [MONITORING_SETUP.md](./MONITORING_SETUP.md)
2. Import Grafana dashboard: [GRAFANA_DASHBOARD.json](./GRAFANA_DASHBOARD.json)
3. Run performance tests: `pytest tests/test_performance.py -v`
4. Establish baselines: `pytest tests/test_performance.py::TestPerformanceBaselines::test_establish_baselines`
