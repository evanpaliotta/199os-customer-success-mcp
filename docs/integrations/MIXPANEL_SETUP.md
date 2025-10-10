# Mixpanel Integration Setup Guide

Complete guide to integrating Customer Success MCP with Mixpanel for product analytics and usage tracking.

## Overview

The Mixpanel integration enables:
- Track user events and product usage
- Analyze feature adoption and engagement
- Create customer cohorts and segments
- Query analytics data programmatically
- Monitor product metrics
- Identify usage trends and patterns

## Prerequisites

- Mixpanel account (Free or paid plan)
- Project created in Mixpanel
- Admin access to generate tokens

## Finding Your Credentials

### Step 1: Locate Project Token

1. Log into Mixpanel
2. Click **Settings** (gear icon)
3. Navigate to **Project** → **Project Settings**
4. Find **Project Token** under Project Information
5. Copy the token

Token format: `abc123def456ghi789jkl012mno345`

### Step 2: Get API Secret

1. In Project Settings, scroll to **Access Keys**
2. Find **API Secret**
3. Click **Show** to reveal
4. Copy the secret

Secret format: `1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p`

### Step 3: Note Project ID

1. In Project Settings, find **Project ID**
2. This is typically a numeric ID
3. Copy for reference (optional)

## Configuration

Add to `.env`:

```bash
# Mixpanel Configuration
MIXPANEL_PROJECT_TOKEN=abc123def456ghi789jkl012mno345
MIXPANEL_API_SECRET=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p
```

Restart services:
```bash
docker-compose restart cs-mcp
```

## Testing the Integration

### Test Connection

```bash
curl -X POST http://localhost:8080/tools/test_mixpanel_connection
```

Expected response:
```json
{
  "status": "success",
  "project_id": "12345",
  "project_name": "Your Project"
}
```

### Track Test Event

```bash
curl -X POST http://localhost:8080/tools/track_mixpanel_event \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test-client",
    "event_name": "Test Event",
    "properties": {
      "source": "cs-mcp",
      "test": true
    }
  }'
```

### Update User Profile

```bash
curl -X POST http://localhost:8080/tools/update_mixpanel_profile \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "acme-corp",
    "properties": {
      "$name": "Acme Corp",
      "$email": "contact@acmecorp.com",
      "health_score": 85,
      "plan": "enterprise"
    }
  }'
```

### Query Events

```bash
curl -X POST http://localhost:8080/tools/query_mixpanel_events \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Login",
    "from_date": "2025-10-01",
    "to_date": "2025-10-10"
  }'
```

## Event Naming Conventions

Use consistent, descriptive event names following these patterns:

### User Actions
```
user_signed_up
user_logged_in
user_logged_out
user_updated_profile
user_changed_password
```

### Feature Usage
```
feature_opened
feature_used
feature_completed
feature_shared
feature_favorited
```

### Onboarding
```
onboarding_started
onboarding_step_1_completed
onboarding_step_2_completed
onboarding_completed
onboarding_skipped
```

### Product Engagement
```
report_generated
dashboard_viewed
export_created
search_performed
filter_applied
```

### Support Events
```
help_article_viewed
support_ticket_created
live_chat_started
feedback_submitted
```

## Event Properties

Include rich context with every event:

### Required Properties
```json
{
  "distinct_id": "client-id",
  "time": 1728561234,
  "$insert_id": "unique-event-id"
}
```

### Recommended Properties
```json
{
  "client_id": "acme-corp",
  "company_name": "Acme Corp",
  "user_email": "jane@acmecorp.com",
  "plan": "enterprise",
  "health_score": 85,
  "source": "cs-mcp",
  "environment": "production"
}
```

### Event-Specific Properties
```json
{
  "event": "feature_used",
  "properties": {
    "feature_name": "Advanced Analytics",
    "duration_seconds": 120,
    "success": true,
    "method": "api"
  }
}
```

## User Profile Properties

### Special Properties (Mixpanel reserved)

Use `$` prefix for Mixpanel special properties:

```json
{
  "$name": "Jane Smith",
  "$email": "jane@acmecorp.com",
  "$phone": "+1-555-123-4567",
  "$created": "2025-01-15T10:30:00Z",
  "$last_seen": "2025-10-10T14:22:00Z"
}
```

### Custom Properties

Add your own properties (no `$` prefix):

```json
{
  "health_score": 85,
  "churn_risk": "low",
  "plan": "enterprise",
  "mrr": 15000,
  "contract_end_date": "2026-03-15",
  "onboarding_status": "completed",
  "lifetime_value": 180000,
  "support_tickets_count": 3,
  "nps_score": 9,
  "feature_adoption_rate": 0.75,
  "team_size": 25,
  "industry": "Technology"
}
```

### Increment Properties

Use increment operations for counters:

```bash
curl -X POST http://localhost:8080/tools/increment_mixpanel_property \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "acme-corp",
    "property": "login_count",
    "value": 1
  }'
```

## Cohort and Segmentation

### Create Cohorts Programmatically

```bash
curl -X POST http://localhost:8080/tools/create_mixpanel_cohort \
  -H "Content-Type: application/json" \
  -d '{
    "name": "At-Risk Customers",
    "filters": {
      "health_score": {"$lt": 60},
      "last_seen": {"$gt": "7 days ago"}
    }
  }'
```

### Common Segment Queries

**High-Value Active Users**:
```json
{
  "plan": "enterprise",
  "health_score": {"$gte": 80},
  "last_seen": {"$lt": "1 day ago"}
}
```

**Onboarding Users**:
```json
{
  "onboarding_status": "in_progress",
  "$created": {"$gte": "30 days ago"}
}
```

**Feature Adopters**:
```json
{
  "feature_adoption_rate": {"$gte": 0.7},
  "plan": {"$in": ["professional", "enterprise"]}
}
```

## Querying Analytics Data

### JQL (Mixpanel Query Language)

Execute advanced queries:

```bash
curl -X POST http://localhost:8080/tools/execute_mixpanel_jql \
  -H "Content-Type: application/json" \
  -d '{
    "script": "function main() { return Events({ from_date: \"2025-10-01\", to_date: \"2025-10-10\", event_selectors: [{event: \"Login\"}] }); }"
  }'
```

### Common Queries

**Daily Active Users**:
```javascript
function main() {
  return Events({
    from_date: '2025-10-01',
    to_date: '2025-10-10',
    event_selectors: [{event: 'Login'}]
  })
  .groupBy(['name'], mixpanel.reducer.count())
  .groupByUser(mixpanel.reducer.count());
}
```

**Feature Adoption Rate**:
```javascript
function main() {
  return People()
    .filter(function(user) {
      return user.properties.feature_adoption_rate >= 0.7;
    })
    .reduce(mixpanel.reducer.count());
}
```

**Churn Risk Analysis**:
```javascript
function main() {
  return People()
    .filter(function(user) {
      return user.properties.churn_risk === 'high';
    })
    .groupBy(['plan'], mixpanel.reducer.count());
}
```

## Batch Event Tracking

For high-volume event tracking, use batching:

```bash
curl -X POST http://localhost:8080/tools/batch_track_mixpanel_events \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "client_id": "client1",
        "event": "page_viewed",
        "properties": {"page": "dashboard"}
      },
      {
        "client_id": "client2",
        "event": "feature_used",
        "properties": {"feature": "analytics"}
      }
    ]
  }'
```

Configuration:
```bash
MIXPANEL_BATCH_SIZE=50          # Events per batch
MIXPANEL_BATCH_FLUSH_INTERVAL=5 # Seconds
```

## Common Errors

### Error: Invalid Token

**Error**: `401 Unauthorized`

**Cause**: Invalid project token

**Solution**:
```bash
# Verify token
curl "https://mixpanel.com/api/2.0/engage?project_id=YOUR_PROJECT_ID" \
  -u "YOUR_API_SECRET:"

# Get new token from Mixpanel settings
```

### Error: Event Not Appearing

**Cause**: Events can take up to 60 seconds to appear

**Solution**:
- Wait 1-2 minutes
- Check event name matches exactly
- Verify distinct_id is set
- Check Mixpanel Live View

### Error: Property Type Mismatch

**Error**: Property value type changed

**Cause**: Sending different data types for same property

**Solution**: Maintain consistent types:
```bash
# WRONG - mixing types
{"age": "25"}  # string
{"age": 25}    # number

# CORRECT - consistent type
{"age": 25}    # always number
```

### Error: Rate Limit Exceeded

**Error**: `429 Too Many Requests`

**Solution**:
```bash
# Enable batching
MIXPANEL_ENABLE_BATCHING=true

# Increase retry delay
MIXPANEL_RETRY_DELAY=2
```

## Best Practices

### 1. Use Consistent Naming

Follow snake_case for event names:
```
✓ user_logged_in
✓ feature_opened
✗ UserLoggedIn
✗ feature-opened
```

### 2. Include Context Properties

Always include:
- `client_id` or `distinct_id`
- `timestamp` (auto-added if omitted)
- `source: "cs-mcp"`
- Plan/tier information
- Health score (if relevant)

### 3. Track Both Actions and Outcomes

```bash
# Action
track("report_generation_started")

# Outcome
track("report_generation_completed", {
  "duration_seconds": 3.2,
  "success": true,
  "row_count": 1500
})
```

### 4. Set Up Funnels

Track multi-step processes:
```bash
1. onboarding_started
2. onboarding_step_1_completed
3. onboarding_step_2_completed
4. onboarding_completed
```

### 5. Monitor Key Metrics

Track metrics that indicate:
- Product adoption
- Feature usage
- Engagement level
- Churn signals
- Expansion opportunities

## Advanced Configuration

### Custom Event Processing

Process events before sending:

```bash
# In .env
MIXPANEL_ENABLE_EVENT_PROCESSING=true
MIXPANEL_ADD_DEFAULT_PROPERTIES=true
```

Default properties added:
```json
{
  "mp_lib": "cs-mcp",
  "mp_lib_version": "1.0.0",
  "$insert_id": "auto-generated-uuid",
  "source": "customer-success-mcp"
}
```

### Data Enrichment

Enrich events with additional context:

```bash
MIXPANEL_ENRICH_WITH_HEALTH_SCORE=true
MIXPANEL_ENRICH_WITH_ACCOUNT_DATA=true
```

### GDPR Compliance

Delete user data:
```bash
curl -X POST http://localhost:8080/tools/delete_mixpanel_user \
  -H "Content-Type: application/json" \
  -d '{"client_id": "user-to-delete"}'
```

Export user data:
```bash
curl -X POST http://localhost:8080/tools/export_mixpanel_user_data \
  -H "Content-Type: application/json" \
  -d '{"client_id": "user-to-export"}'
```

## Performance Optimization

### Event Buffering

Buffer events for batch sending:
```bash
MIXPANEL_BUFFER_SIZE=100
MIXPANEL_BUFFER_TIMEOUT=10
```

### Async Tracking

Events are tracked asynchronously by default:
```bash
MIXPANEL_ASYNC_TRACKING=true
MIXPANEL_ASYNC_WORKERS=4
```

### Caching

Cache query results:
```bash
MIXPANEL_CACHE_QUERY_RESULTS=true
MIXPANEL_QUERY_CACHE_TTL=3600  # 1 hour
```

## Integration with CS Workflows

### Automatic Event Tracking

Events automatically tracked by CS MCP:

```bash
# Customer lifecycle
customer_registered
customer_onboarded
customer_health_calculated
customer_churned

# Engagement
login
feature_used
report_generated
export_created

# Support
ticket_created
ticket_resolved
feedback_submitted

# Renewal
renewal_approaching
renewal_completed
subscription_upgraded
```

### Health Score Sync

Sync health scores to Mixpanel:
```bash
curl -X POST http://localhost:8080/tools/sync_health_scores_to_mixpanel
```

Updates these profile properties:
- `health_score`
- `health_status`
- `churn_risk`
- `last_health_calculation`

## Reporting and Dashboards

### Create Custom Reports

```bash
curl -X POST http://localhost:8080/tools/create_mixpanel_report \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Health Dashboard",
    "charts": [
      {
        "type": "segmentation",
        "event": "health_score_calculated",
        "property": "health_status"
      }
    ]
  }'
```

### Export Data

```bash
curl -X POST http://localhost:8080/tools/export_mixpanel_data \
  -H "Content-Type: application/json" \
  -d '{
    "from_date": "2025-10-01",
    "to_date": "2025-10-10",
    "event": "Login",
    "format": "json"
  }'
```

## Security

### Token Management

- Rotate API secrets every 90 days
- Use separate projects for dev/staging/prod
- Never expose tokens in client-side code

### Data Privacy

- Hash PII before sending
- Use distinct_id instead of email
- Implement data retention policies

```bash
MIXPANEL_HASH_PII=true
MIXPANEL_DATA_RETENTION_DAYS=365
```

## Support Resources

- [Mixpanel API Docs](https://developer.mixpanel.com/docs)
- [JQL Reference](https://developer.mixpanel.com/docs/jql)
- [Python SDK](https://github.com/mixpanel/mixpanel-python)
- [CS MCP Tool Reference](../api/TOOL_REFERENCE.md)

---

**Last Updated**: October 2025