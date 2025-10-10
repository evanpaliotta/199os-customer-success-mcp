# Core Tools Reference

Complete reference for the 5 core system tools that form the foundation of Customer Success MCP.

## Table of Contents

1. [Overview](#overview)
2. [register_client](#register_client)
3. [get_client_overview](#get_client_overview)
4. [update_client_info](#update_client_info)
5. [list_clients](#list_clients)
6. [get_client_timeline](#get_client_timeline)
7. [Usage Examples](#usage-examples)
8. [Error Codes](#error-codes)
9. [Best Practices](#best-practices)

## Overview

The core tools provide essential customer lifecycle management capabilities:

- **Customer Registration**: Onboard new customers into the system
- **Customer Overview**: 360-degree view of customer health and status
- **Customer Updates**: Modify customer information and metadata
- **Customer Listing**: Query and filter customer base
- **Customer Timeline**: Historical activity and event tracking

### Common Parameters

| Parameter | Type | Description | Required |
|-----------|------|-------------|----------|
| `client_id` | string | Unique customer identifier | Yes (except register) |
| `ctx` | Context | MCP context object | Yes (auto-provided) |

### Common Response Format

All tools return a standardized response:

```json
{
  "status": "success|failed",
  "message": "Human-readable message",
  "data": {...},
  "error": "Error message if failed"
}
```

## register_client

Register a new customer in the Customer Success system.

### Purpose

Creates a complete customer record with:
- Basic company information
- Contract details
- Initial health score (50/100)
- Lifecycle stage (onboarding)
- Placeholder for metrics

### Signature

```python
async def register_client(
    ctx: Context,
    client_name: str,
    company_name: str,
    industry: str = "Technology",
    contract_value: float = 0.0,
    contract_start_date: Optional[str] = None,
    contract_end_date: Optional[str] = None,
    primary_contact_email: Optional[str] = None,
    primary_contact_name: Optional[str] = None,
    tier: str = "standard"
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `client_name` | string | Yes | - | Display name for the client |
| `company_name` | string | Yes | - | Legal company name |
| `industry` | string | No | "Technology" | Industry vertical |
| `contract_value` | float | No | 0.0 | Annual contract value (ARR) |
| `contract_start_date` | string | No | Today | Contract start (YYYY-MM-DD) |
| `contract_end_date` | string | No | +365 days | Contract end (YYYY-MM-DD) |
| `primary_contact_email` | string | No | None | Primary contact email |
| `primary_contact_name` | string | No | None | Primary contact name |
| `tier` | string | No | "standard" | Customer tier |

### Valid Tier Values

- `starter` - Entry-level customers
- `standard` - Standard plan customers
- `professional` - Professional plan customers
- `enterprise` - Enterprise customers

### Response Schema

```json
{
  "status": "success",
  "message": "Client 'Acme Corp' registered successfully",
  "client_id": "cs_1696800000_acme_corp",
  "client_record": {
    "client_id": "cs_1696800000_acme_corp",
    "client_name": "Acme Corp",
    "company_name": "Acme Corporation Inc.",
    "industry": "Technology",
    "tier": "professional",
    "contract_value": 72000,
    "contract_start_date": "2025-01-01",
    "contract_end_date": "2026-01-01",
    "renewal_date": "2026-01-01",
    "primary_contact_email": "john@acme.com",
    "primary_contact_name": "John Smith",
    "csm_assigned": null,
    "health_score": 50,
    "health_trend": "stable",
    "lifecycle_stage": "onboarding",
    "last_engagement_date": null,
    "users_provisioned": 0,
    "active_users": 0,
    "feature_adoption_rate": 0.0,
    "support_tickets_open": 0,
    "satisfaction_score": null,
    "created_at": "2025-10-10T10:30:00",
    "updated_at": "2025-10-10T10:30:00",
    "status": "active"
  },
  "summary": {
    "tier": "professional",
    "contract_value": "$72,000.00",
    "contract_term": "365 days",
    "days_until_renewal": 365,
    "lifecycle_stage": "onboarding"
  },
  "next_steps": [
    "Create onboarding plan (use create_onboarding_plan tool)",
    "Schedule kickoff call (use schedule_kickoff_meeting tool)",
    "Provision user accounts and access",
    "Assign Customer Success Manager (use assign_csm tool)",
    "Set up health score monitoring (automatic)",
    "Configure integration points"
  ]
}
```

### Example Usage

```bash
curl -X POST http://localhost:8080/tools/register_client \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Acme Corp",
    "company_name": "Acme Corporation Inc.",
    "industry": "Technology",
    "contract_value": 72000,
    "contract_start_date": "2025-01-01",
    "contract_end_date": "2026-01-01",
    "primary_contact_email": "john@acme.com",
    "primary_contact_name": "John Smith",
    "tier": "professional"
  }'
```

### Error Responses

| Error | Cause | Solution |
|-------|-------|----------|
| Invalid tier | Tier not in valid list | Use: starter, standard, professional, enterprise |
| Invalid date format | Date not YYYY-MM-DD | Use correct format: 2025-01-01 |
| Missing required field | client_name or company_name missing | Provide both required fields |

## get_client_overview

Retrieve comprehensive 360-degree view of a customer.

### Purpose

Returns complete customer status including:
- Health score and trend
- Onboarding progress
- Engagement metrics
- Support tickets
- Product usage
- Revenue opportunities
- Communication history
- Risks and opportunities

### Signature

```python
async def get_client_overview(
    ctx: Context,
    client_id: str
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Unique client identifier |

### Response Schema

```json
{
  "status": "success",
  "client_overview": {
    "client_id": "acme-corp",
    "client_name": "Acme Corporation",
    "company_name": "Acme Corp Inc.",
    "industry": "SaaS",
    "tier": "professional",
    "health_score": 82,
    "health_trend": "improving",
    "lifecycle_stage": "active",
    "csm_assigned": "Sarah Chen",
    "contract_value": 72000,
    "contract_start_date": "2024-01-15",
    "contract_end_date": "2025-01-15",
    "days_until_renewal": 127,
    "renewal_probability": 0.89,
    "renewal_risk_level": "low",
    "onboarding": {
      "status": "completed",
      "completion_rate": 1.0,
      "completion_date": "2024-02-08",
      "time_to_value_days": 24
    },
    "engagement": {
      "last_login": "2025-10-08",
      "days_since_last_login": 2,
      "weekly_active_users": 45,
      "monthly_active_users": 68,
      "feature_adoption_rate": 0.73
    },
    "support": {
      "open_tickets": 2,
      "tickets_this_month": 8,
      "avg_resolution_time_hours": 4.2,
      "satisfaction_score": 4.6
    },
    "product_usage": {
      "core_features_used": 18,
      "core_features_total": 25,
      "integrations_active": 3
    },
    "revenue": {
      "current_arr": 72000,
      "expansion_opportunities": 3,
      "expansion_potential_arr": 28000
    }
  },
  "health_components": {
    "usage_score": 85,
    "engagement_score": 88,
    "support_score": 82,
    "satisfaction_score": 92,
    "payment_score": 100
  },
  "insights": {
    "overall_status": "healthy",
    "key_strengths": [
      "High engagement and feature adoption",
      "Excellent support satisfaction"
    ],
    "recommended_actions": [
      "Present expansion proposal for additional licenses"
    ]
  }
}
```

### Example Usage

```bash
curl -X POST http://localhost:8080/tools/get_client_overview \
  -H "Content-Type: application/json" \
  -d '{"client_id": "acme-corp"}'
```

## update_client_info

Update customer information and metadata.

### Purpose

Modify any updateable client field including:
- Contact information
- Tier changes
- Contract details
- CSM assignment
- Account status

### Signature

```python
async def update_client_info(
    ctx: Context,
    client_id: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `client_id` | string | Yes | Unique client identifier |
| `updates` | dict | Yes | Fields to update with new values |

### Allowed Update Fields

- `client_name` - Display name
- `company_name` - Legal name
- `industry` - Industry vertical
- `tier` - Customer tier
- `contract_value` - ARR value
- `contract_start_date` - Contract start
- `contract_end_date` - Contract end
- `primary_contact_email` - Contact email
- `primary_contact_name` - Contact name
- `csm_assigned` - CSM name
- `status` - Account status (active, inactive, churned)

### Example Usage

```bash
curl -X POST http://localhost:8080/tools/update_client_info \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "acme-corp",
    "updates": {
      "tier": "enterprise",
      "contract_value": 120000,
      "csm_assigned": "Michael Torres"
    }
  }'
```

### Response

```json
{
  "status": "success",
  "message": "Client information updated successfully",
  "client_id": "acme-corp",
  "updated_fields": ["tier", "contract_value", "csm_assigned"],
  "updated_record": {...},
  "audit": {
    "updated_at": "2025-10-10T14:30:00",
    "fields_changed": 3
  }
}
```

## list_clients

List and filter customers with pagination.

### Purpose

Query customer base with filters:
- Tier-based filtering
- Lifecycle stage filtering
- Health score range
- Pagination support

### Signature

```python
async def list_clients(
    ctx: Context,
    tier_filter: Optional[str] = None,
    lifecycle_stage_filter: Optional[str] = None,
    health_score_min: Optional[int] = None,
    health_score_max: Optional[int] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `tier_filter` | string | No | None | Filter by tier |
| `lifecycle_stage_filter` | string | No | None | Filter by lifecycle stage |
| `health_score_min` | int | No | None | Minimum health score (0-100) |
| `health_score_max` | int | No | None | Maximum health score (0-100) |
| `limit` | int | No | 50 | Results per page (max 1000) |
| `offset` | int | No | 0 | Pagination offset |

### Valid Filter Values

**Tier**: starter, standard, professional, enterprise

**Lifecycle Stage**: onboarding, active, at_risk, churned, expansion

### Example Usage

```bash
# List all enterprise customers
curl -X POST http://localhost:8080/tools/list_clients \
  -H "Content-Type: application/json" \
  -d '{"tier_filter": "enterprise"}'

# List at-risk customers
curl -X POST http://localhost:8080/tools/list_clients \
  -H "Content-Type: application/json" \
  -d '{
    "lifecycle_stage_filter": "at_risk",
    "health_score_max": 60
  }'

# Pagination
curl -X POST http://localhost:8080/tools/list_clients \
  -H "Content-Type: application/json" \
  -d '{"limit": 25, "offset": 50}'
```

### Response

```json
{
  "status": "success",
  "clients": [...],
  "pagination": {
    "total_count": 150,
    "limit": 50,
    "offset": 0,
    "returned_count": 50,
    "has_more": true
  },
  "summary": {
    "total_clients": 150,
    "average_health_score": 76.5,
    "total_arr": 10500000,
    "total_active_users": 3420
  }
}
```

## get_client_timeline

Retrieve chronological timeline of customer events.

### Purpose

Get historical view of:
- Onboarding milestones
- Support tickets
- Health score changes
- Product usage spikes
- Business reviews
- Contract events

### Signature

```python
async def get_client_timeline(
    ctx: Context,
    client_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_types: Optional[List[str]] = None,
    limit: int = 100
) -> Dict[str, Any]
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `client_id` | string | Yes | - | Unique client identifier |
| `start_date` | string | No | -90 days | Timeline start (YYYY-MM-DD) |
| `end_date` | string | No | Today | Timeline end (YYYY-MM-DD) |
| `event_types` | array | No | All | Filter event types |
| `limit` | int | No | 100 | Max events (max 1000) |

### Event Types

- `onboarding` - Onboarding milestones
- `support` - Support tickets
- `usage` - Product usage events
- `health` - Health score changes
- `communication` - CSM touchpoints, EBRs
- `renewal` - Contract events
- `product` - Feature adoption
- `contract` - Contract changes

### Example Usage

```bash
# Get full timeline
curl -X POST http://localhost:8080/tools/get_client_timeline \
  -H "Content-Type: application/json" \
  -d '{"client_id": "acme-corp"}'

# Get only support events
curl -X POST http://localhost:8080/tools/get_client_timeline \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "acme-corp",
    "event_types": ["support"],
    "start_date": "2025-01-01"
  }'
```

### Response

```json
{
  "status": "success",
  "client_id": "acme-corp",
  "timeline": [
    {
      "event_id": "evt_001",
      "timestamp": "2024-01-15T10:00:00Z",
      "event_type": "contract",
      "title": "Contract Signed",
      "description": "Professional tier contract signed - $72,000 ARR",
      "impact": "positive",
      "severity": "high"
    }
  ],
  "summary": {
    "total_events": 12,
    "returned_events": 12,
    "event_type_breakdown": {
      "onboarding": 3,
      "support": 2,
      "communication": 4,
      "health": 1,
      "usage": 2
    }
  }
}
```

## Usage Examples

### Complete Customer Onboarding Workflow

```python
# Step 1: Register customer
response = await register_client(
    client_name="Acme Corp",
    company_name="Acme Corporation Inc.",
    industry="Technology",
    contract_value=72000,
    tier="professional",
    primary_contact_email="john@acme.com",
    primary_contact_name="John Smith"
)
client_id = response['client_id']

# Step 2: Assign CSM
await update_client_info(
    client_id=client_id,
    updates={"csm_assigned": "Sarah Chen"}
)

# Step 3: Check onboarding progress (after some time)
overview = await get_client_overview(client_id=client_id)
print(f"Onboarding: {overview['client_overview']['onboarding']['status']}")

# Step 4: Review timeline
timeline = await get_client_timeline(
    client_id=client_id,
    event_types=["onboarding"]
)
```

### Weekly At-Risk Customer Report

```python
# Get all at-risk customers
at_risk = await list_clients(
    lifecycle_stage_filter="at_risk",
    health_score_max=60
)

for client in at_risk['clients']:
    # Get detailed overview
    overview = await get_client_overview(client_id=client['client_id'])

    # Get recent timeline
    timeline = await get_client_timeline(
        client_id=client['client_id'],
        start_date="2025-10-01",
        limit=10
    )

    print(f"{client['client_name']}: Health={client['health_score']}")
```

## Error Codes

| Code | Error | Description |
|------|-------|-------------|
| `INVALID_CLIENT_ID` | Invalid client_id format | client_id contains invalid characters |
| `CLIENT_NOT_FOUND` | Client does not exist | No client with given ID |
| `INVALID_TIER` | Invalid tier value | Tier not in allowed list |
| `INVALID_DATE` | Invalid date format | Date not YYYY-MM-DD |
| `INVALID_FIELD` | Invalid update field | Field not updateable |
| `INVALID_RANGE` | Invalid range | health_score out of 0-100 |
| `LIMIT_EXCEEDED` | Limit too high | Limit > 1000 |

## Best Practices

### 1. Client ID Naming

Use consistent, lowercase, hyphenated names:
```
✓ acme-corp
✓ techstart-inc
✗ Acme Corp
✗ acme_corp
```

### 2. Always Check Status

```python
response = await register_client(...)
if response['status'] == 'success':
    # Proceed
else:
    # Handle error
    print(response['error'])
```

### 3. Use Pagination

For large customer bases:
```python
offset = 0
limit = 50
while True:
    result = await list_clients(limit=limit, offset=offset)
    if len(result['clients']) == 0:
        break
    # Process batch
    offset += limit
```

### 4. Filter Aggressively

Don't retrieve all data when you need subset:
```python
# Instead of listing all then filtering
all_clients = await list_clients(limit=1000)
enterprise = [c for c in all_clients if c['tier'] == 'enterprise']

# Do this
enterprise = await list_clients(tier_filter="enterprise")
```

### 5. Timeline Date Ranges

Use appropriate date ranges:
```python
# Last 30 days for recent activity
recent = await get_client_timeline(
    client_id=client_id,
    start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
)

# Full history for deep analysis
full = await get_client_timeline(
    client_id=client_id,
    limit=1000
)
```

---

**Last Updated**: October 2025
**Version**: 1.0.0