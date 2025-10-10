# Intercom Integration Setup Guide

Complete guide to integrating Customer Success MCP with Intercom for customer messaging and engagement.

## Overview

The Intercom integration enables:
- Send targeted messages to customers
- Track customer events and behavior
- Manage user profiles and segments
- Automate onboarding communications
- Collect in-app feedback
- Monitor customer engagement

## Prerequisites

- Intercom account (Starter plan or higher)
- Admin access to create app and tokens
- Your Intercom App ID
- Workspace access

## Creating API Credentials

### Step 1: Create Developer App

1. Log into Intercom
2. Go to **Settings** → **Developers** → **Developer Hub**
3. Click **New app**
4. Enter app details:
   - **Name**: Customer Success MCP
   - **Description**: Integration for automated customer success
5. Click **Create app**

### Step 2: Generate Access Token

1. In your app settings, go to **Authentication**
2. Click **Generate access token**
3. Copy the token immediately (shown only once)
4. Store securely

Token format:
```
dG9rOjE6YWNjX2FiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6MTIzNDU=
```

### Step 3: Find App ID

1. In app settings, locate **App ID**
2. Format: `abc123de`
3. Copy for configuration

## Configuration

Add to `.env`:

```bash
# Intercom Configuration
INTERCOM_ACCESS_TOKEN=dG9rOjE6YWNjX2FiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6MTIzNDU=
INTERCOM_APP_ID=abc123de
```

Restart services:
```bash
docker-compose restart cs-mcp
```

## Testing the Integration

### Test Connection

```bash
curl -X POST http://localhost:8080/tools/test_intercom_connection
```

Expected response:
```json
{
  "status": "success",
  "app_id": "abc123de",
  "app_name": "Customer Success MCP"
}
```

### Send Test Message

```bash
curl -X POST http://localhost:8080/tools/send_intercom_message \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test-client",
    "message": "Welcome to our platform!",
    "from_admin": "cs-team"
  }'
```

### Create User Profile

```bash
curl -X POST http://localhost:8080/tools/sync_intercom_user \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "acme-corp",
    "email": "jane@acmecorp.com",
    "name": "Jane Smith",
    "custom_attributes": {
      "health_score": 85,
      "plan": "enterprise",
      "mrr": 15000
    }
  }'
```

### Track Event

```bash
curl -X POST http://localhost:8080/tools/track_intercom_event \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "acme-corp",
    "event_name": "onboarding_completed",
    "metadata": {
      "completion_rate": 100,
      "duration_days": 12
    }
  }'
```

## Available Features

### Messaging Features

| Feature | MCP Tool | Description |
|---------|----------|-------------|
| Send Message | `send_intercom_message` | Personal messages to users |
| Send Broadcast | `send_intercom_broadcast` | Messages to segments |
| Automated Series | `create_intercom_series` | Multi-step campaigns |
| In-App Messages | `send_intercom_banner` | Banners and popups |

### User Management

| Feature | MCP Tool | Description |
|---------|----------|-------------|
| Create/Update User | `sync_intercom_user` | Sync user profiles |
| Add Tags | `add_intercom_tags` | Tag for segmentation |
| Update Attributes | `update_intercom_attributes` | Custom fields |
| Delete User | `delete_intercom_user` | GDPR compliance |

### Event Tracking

| Feature | MCP Tool | Description |
|---------|----------|-------------|
| Track Event | `track_intercom_event` | Log user actions |
| Batch Events | `batch_track_intercom_events` | Bulk event logging |
| Event Metadata | Included | Rich event context |

## Message Templates

### Welcome Message

```json
{
  "template_name": "welcome",
  "message": "Hi {{name}}! Welcome to {{company_name}}. We're excited to help you succeed!",
  "merge_fields": {
    "name": "Jane",
    "company_name": "Acme Corp"
  }
}
```

### Onboarding Milestone

```json
{
  "template_name": "milestone_completed",
  "message": "Great job, {{name}}! You've completed {{milestone_name}}. Next up: {{next_step}}",
  "merge_fields": {
    "name": "Jane",
    "milestone_name": "Initial Setup",
    "next_step": "Team Invitation"
  }
}
```

### At-Risk Alert

```json
{
  "template_name": "engagement_check",
  "message": "Hi {{name}}, we noticed you haven't logged in recently. Need any help? Reply to chat anytime!",
  "from_admin": "cs-manager"
}
```

### Feature Announcement

```json
{
  "template_name": "new_feature",
  "message": "New feature alert! {{feature_name}} is now available. Check it out: {{feature_url}}",
  "merge_fields": {
    "feature_name": "Advanced Analytics",
    "feature_url": "https://app.example.com/analytics"
  }
}
```

## Event Naming Conventions

Use consistent event naming:

### Onboarding Events
```
onboarding_started
onboarding_step_completed
onboarding_milestone_reached
onboarding_completed
```

### Engagement Events
```
feature_used
session_started
report_generated
team_member_invited
```

### Support Events
```
ticket_created
ticket_resolved
feedback_submitted
help_article_viewed
```

### Renewal Events
```
renewal_approaching
renewal_completed
subscription_upgraded
subscription_downgraded
```

## Custom Attributes

Define custom user attributes:

```json
{
  "health_score": 85,
  "health_status": "healthy",
  "churn_risk": "low",
  "plan": "enterprise",
  "mrr": 15000,
  "contract_end_date": "2026-03-15",
  "onboarding_status": "completed",
  "lifetime_value": 180000,
  "support_tickets_count": 3,
  "nps_score": 9
}
```

## Segmentation

Create segments based on attributes:

### At-Risk Customers
```
health_score < 60 AND
churn_risk = "high" AND
last_seen_at > 7 days ago
```

### Expansion Opportunities
```
health_score > 80 AND
plan = "professional" AND
feature_adoption > 0.75
```

### Onboarding Active
```
onboarding_status = "in_progress" AND
created_at < 30 days ago
```

## Common Errors

### Error: Unauthorized (401)

**Cause**: Invalid access token

**Solution**:
```bash
# Verify token
curl -X GET https://api.intercom.io/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# Regenerate token if invalid
# 1. Go to Intercom Developer Hub
# 2. Revoke old token
# 3. Generate new token
# 4. Update .env
```

### Error: User Not Found (404)

**Cause**: User doesn't exist in Intercom

**Solution**: Create user before sending message
```bash
# Create user first
curl -X POST http://localhost:8080/tools/sync_intercom_user \
  -d '{"client_id": "acme-corp", "email": "user@acme.com"}'

# Then send message
curl -X POST http://localhost:8080/tools/send_intercom_message \
  -d '{"client_id": "acme-corp", "message": "Hello!"}'
```

### Error: Rate Limit (429)

**Cause**: Too many API requests

**Solution**: Integration has automatic retry. Adjust settings:
```bash
INTERCOM_MAX_RETRIES=5
INTERCOM_RETRY_DELAY=2
```

### Error: Invalid Event Name

**Cause**: Event name contains invalid characters

**Solution**: Use only alphanumeric and underscore:
```bash
# WRONG
event_name="User Logged In!"

# CORRECT
event_name="user_logged_in"
```

## Best Practices

### 1. Sync User Data Regularly

```bash
# Daily sync
curl -X POST http://localhost:8080/tools/sync_all_intercom_users
```

### 2. Use Tags for Organization

```bash
tags = [
  "cs-mcp",
  "tier:enterprise",
  "health:at-risk",
  "automated",
  "cohort:2025-q1"
]
```

### 3. Track Key Events

Focus on events that indicate:
- Product adoption
- Feature usage
- Engagement level
- Churn signals
- Expansion readiness

### 4. Personalize Messages

Always use merge fields:
```json
{
  "message": "Hi {{name}}, your account with {{company_name}} needs attention.",
  "merge_fields": {
    "name": "Jane",
    "company_name": "Acme Corp"
  }
}
```

### 5. Respect Frequency Limits

Don't message too often:
```bash
INTERCOM_MESSAGE_FREQUENCY_DAYS=3  # Min 3 days between messages
INTERCOM_MAX_DAILY_MESSAGES=5      # Max 5 per user per day
```

## Advanced Configuration

### Webhook Setup

Receive real-time events from Intercom:

1. **Create Webhook**:
   - Developer Hub → Webhooks
   - Endpoint: `https://your-server.com/webhooks/intercom`
   - Topics: `user.created`, `conversation.user.replied`

2. **Configure Secret**:
   ```bash
   INTERCOM_WEBHOOK_SECRET=your-webhook-secret
   ```

### Message Templates

Store templates in `config/intercom_templates.json`:

```json
{
  "welcome": {
    "message": "Welcome {{name}}!",
    "from_admin": "cs-team"
  },
  "check_in": {
    "message": "How are things going, {{name}}?",
    "from_admin": "cs-manager"
  }
}
```

### Automated Campaigns

Configure automatic message triggers:

```bash
# In .env
INTERCOM_ENABLE_AUTO_CAMPAIGNS=true
INTERCOM_WELCOME_DELAY_HOURS=1
INTERCOM_FOLLOWUP_DELAY_DAYS=3
```

## Performance Optimization

### Batching

Batch operations for efficiency:

```bash
# Batch event tracking
curl -X POST http://localhost:8080/tools/batch_track_intercom_events \
  -d '{
    "events": [
      {"client_id": "client1", "event": "login"},
      {"client_id": "client2", "event": "feature_used"}
    ]
  }'
```

### Caching

User data is cached:
```bash
INTERCOM_CACHE_TTL=1800  # 30 minutes
```

## Security

### Token Management

- Rotate tokens every 90 days
- Use separate tokens per environment
- Never commit tokens to version control

### Data Privacy

Comply with GDPR:
```bash
# Delete user data
curl -X POST http://localhost:8080/tools/delete_intercom_user \
  -d '{"client_id": "user-to-delete"}'
```

## Support Resources

- [Intercom API Docs](https://developers.intercom.com/docs)
- [Python SDK](https://github.com/intercom/python-intercom)
- [CS MCP Tool Reference](../api/TOOL_REFERENCE.md)

---

**Last Updated**: October 2025