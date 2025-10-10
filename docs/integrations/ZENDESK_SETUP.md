# Zendesk Integration Setup Guide

Complete guide to integrating Customer Success MCP with Zendesk for support ticket management.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Creating API Credentials](#creating-api-credentials)
4. [Configuration](#configuration)
5. [Testing the Integration](#testing-the-integration)
6. [Available Features](#available-features)
7. [Common Errors](#common-errors)
8. [Best Practices](#best-practices)
9. [Advanced Configuration](#advanced-configuration)
10. [Troubleshooting](#troubleshooting)

## Overview

The Zendesk integration enables Customer Success MCP to:

- Create support tickets automatically
- Update ticket status and priority
- Add comments to existing tickets
- Search and retrieve ticket information
- Track SLA compliance
- Monitor support metrics
- Route tickets based on customer health
- Escalate at-risk customer issues

### Integration Architecture

```
Customer Success MCP
        ↓
   Zendesk Client (zenpy)
        ↓
   Zendesk API (REST)
        ↓
   Your Zendesk Instance
```

## Prerequisites

Before setting up the Zendesk integration:

- **Zendesk Account**: Professional plan or higher (API access required)
- **Admin Access**: Ability to create API tokens
- **Subdomain**: Your Zendesk subdomain (e.g., `yourcompany.zendesk.com`)
- **Email Address**: Email for API authentication

### Required Zendesk Permissions

The API user needs these permissions:
- Create and modify tickets
- Add comments to tickets
- View and search tickets
- Access ticket fields and custom fields
- View users and organizations

## Creating API Credentials

### Step 1: Access Admin Settings

1. Log into your Zendesk account
2. Click the **Admin** icon (gear icon) in the sidebar
3. Navigate to **Channels** → **API**

### Step 2: Enable Token Access

1. In the API settings page, locate **Token Access**
2. Toggle **Enabled** to turn on token access
3. Click **Save**

### Step 3: Generate API Token

1. Click the **Add API Token** button
2. Enter a description: `Customer Success MCP Integration`
3. Click **Create**
4. **IMPORTANT**: Copy the API token immediately
   - Token is shown only once
   - Store securely (password manager recommended)
   - Cannot be retrieved later

Example token format:
```
1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0
```

### Step 4: Find Your Subdomain

Your subdomain is the first part of your Zendesk URL:

```
https://yourcompany.zendesk.com
         ^^^^^^^^^^
         This is your subdomain
```

### Step 5: Identify API Email

Use the email address of the admin user who created the token, or create a dedicated service account:

**Recommended**: Create service account
```
Email: cs-mcp@yourcompany.com
Role: Agent
Name: Customer Success MCP
```

## Configuration

### Add to Environment Variables

Edit your `.env` file and add:

```bash
# Zendesk Configuration
ZENDESK_SUBDOMAIN=yourcompany
ZENDESK_EMAIL=cs-mcp@yourcompany.com
ZENDESK_API_TOKEN=1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0
```

**Do not include** `.zendesk.com` in the subdomain value.

### Verify Configuration

Check that variables are set:

```bash
# If using Docker
docker-compose exec cs-mcp env | grep ZENDESK

# If running locally
env | grep ZENDESK
```

### Restart Services

```bash
# Docker deployment
docker-compose restart cs-mcp

# Local development
# Stop and restart the MCP server
```

## Testing the Integration

### Test 1: Connection Test

```bash
curl -X POST http://localhost:8080/tools/test_zendesk_connection \
  -H "Content-Type: application/json"
```

**Expected Response**:
```json
{
  "status": "success",
  "message": "Zendesk connection successful",
  "subdomain": "yourcompany",
  "api_version": "v2",
  "rate_limit_remaining": 700
}
```

### Test 2: Create Test Ticket

```bash
curl -X POST http://localhost:8080/tools/handle_support_ticket \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test-client",
    "subject": "Test Ticket from CS MCP",
    "description": "This is a test ticket to verify integration",
    "priority": "normal",
    "ticket_type": "question"
  }'
```

**Expected Response**:
```json
{
  "ticket_id": "12345",
  "status": "created",
  "url": "https://yourcompany.zendesk.com/agent/tickets/12345",
  "created_at": "2025-10-10T10:30:00Z"
}
```

### Test 3: Search Tickets

```bash
curl -X POST http://localhost:8080/tools/search_support_tickets \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test-client",
    "status": "open"
  }'
```

### Test 4: Update Ticket

```bash
curl -X POST http://localhost:8080/tools/update_support_ticket \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "12345",
    "status": "solved",
    "comment": "Issue resolved via CS MCP test"
  }'
```

## Available Features

### Feature Matrix

| Feature | MCP Tool | Zendesk API Endpoint |
|---------|----------|---------------------|
| Create Ticket | `handle_support_ticket` | POST /api/v2/tickets |
| Update Ticket | `update_support_ticket` | PUT /api/v2/tickets/{id} |
| Add Comment | `add_ticket_comment` | PUT /api/v2/tickets/{id} |
| Get Ticket | `get_support_ticket` | GET /api/v2/tickets/{id} |
| Search Tickets | `search_support_tickets` | GET /api/v2/search |
| Track SLA | `check_ticket_sla` | GET /api/v2/tickets/{id}/metrics |

### Ticket Creation Options

```json
{
  "client_id": "acme-corp",
  "subject": "Customer needs onboarding help",
  "description": "Detailed description...",
  "priority": "high",           // low, normal, high, urgent
  "ticket_type": "incident",    // question, incident, problem, task
  "tags": ["onboarding", "at-risk"],
  "assignee_email": "cs-manager@company.com",
  "custom_fields": {
    "health_score": 45,
    "account_tier": "enterprise"
  }
}
```

### SLA Monitoring

Track SLA compliance automatically:

```bash
curl -X POST http://localhost:8080/tools/monitor_sla_compliance \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "acme-corp",
    "time_period_days": 30
  }'
```

Response includes:
- Tickets meeting SLA
- Tickets breaching SLA
- Average response time
- Average resolution time

## Common Errors

### Error 1: Authentication Failed

**Error Message**:
```
401 Unauthorized: Couldn't authenticate you
```

**Causes**:
- Invalid API token
- Incorrect email address
- Token disabled in Zendesk

**Solution**:
```bash
# Verify credentials
curl -u "{email}/token:{api_token}" \
  https://{subdomain}.zendesk.com/api/v2/tickets.json

# Regenerate token if needed
# 1. Go to Zendesk Admin → API
# 2. Deactivate old token
# 3. Create new token
# 4. Update .env file
```

### Error 2: Rate Limit Exceeded

**Error Message**:
```
429 Too Many Requests: Rate limit exceeded
```

**Causes**:
- Too many API calls in short time
- Zendesk rate limits: 400 requests/minute

**Solution**:
The integration includes automatic retry with exponential backoff. If you see this error frequently:

```bash
# Check rate limit status
curl -X GET http://localhost:8080/tools/get_zendesk_rate_limit

# Adjust retry settings in .env
ZENDESK_MAX_RETRIES=5
ZENDESK_RETRY_DELAY=2
```

### Error 3: Invalid Subdomain

**Error Message**:
```
Connection error: Could not resolve host
```

**Causes**:
- Typo in subdomain
- Including `.zendesk.com` in subdomain value

**Solution**:
```bash
# WRONG
ZENDESK_SUBDOMAIN=yourcompany.zendesk.com

# CORRECT
ZENDESK_SUBDOMAIN=yourcompany
```

### Error 4: Missing Required Field

**Error Message**:
```
422 Unprocessable Entity: Subject: cannot be blank
```

**Causes**:
- Missing required ticket fields
- Invalid field values

**Solution**:
```bash
# Ensure all required fields are provided
{
  "client_id": "required",
  "subject": "required",
  "description": "required",
  "priority": "optional but recommended"
}
```

### Error 5: User Not Found

**Error Message**:
```
404 Not Found: Couldn't find User
```

**Causes**:
- Client email not in Zendesk
- Auto-create user disabled

**Solution**:
Enable auto-create in configuration or pre-create users:

```bash
# Option 1: Enable auto-create
ZENDESK_AUTO_CREATE_USER=true

# Option 2: Pre-create user
curl -X POST http://localhost:8080/tools/create_zendesk_user \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "acme-corp",
    "name": "Jane Smith",
    "email": "jane@acmecorp.com"
  }'
```

## Best Practices

### 1. Use Tags for Organization

Tag tickets with relevant metadata:

```json
{
  "tags": [
    "cs-mcp",               // Identify CS MCP tickets
    "client:acme-corp",     // Client identifier
    "health:at-risk",       // Health status
    "tier:enterprise",      // Account tier
    "automated"             // Automated creation
  ]
}
```

### 2. Set Priority Based on Health Score

```python
# Automatic priority assignment
if health_score < 50:
    priority = "urgent"
elif health_score < 70:
    priority = "high"
else:
    priority = "normal"
```

### 3. Include Context in Description

Provide rich context in ticket descriptions:

```markdown
**Customer**: Acme Corp (acme-corp)
**Health Score**: 45/100 (At Risk)
**Churn Probability**: 68% (High Risk)
**MRR**: $15,000
**Contract End**: 2026-03-15 (156 days)

**Issue Description**:
Customer reported login issues affecting 5 users...

**Recent Activity**:
- Login failures increased 300% in last 7 days
- No product usage in last 48 hours
- Previous ticket #11234 resolved 3 days ago

**Suggested Actions**:
1. Investigate login issues immediately
2. Schedule call with customer success manager
3. Consider retention campaign if not resolved
```

### 4. Monitor SLA Compliance

Set up automated monitoring:

```bash
# Run daily SLA check
curl -X POST http://localhost:8080/tools/monitor_daily_sla \
  -H "Content-Type: application/json"
```

### 5. Escalate At-Risk Customers

Automatically escalate tickets for at-risk customers:

```json
{
  "escalation_rules": {
    "health_score_below": 50,
    "priority": "urgent",
    "assign_to": "cs-director@company.com",
    "notify": ["cs-team@company.com"]
  }
}
```

## Advanced Configuration

### Custom Fields

Map custom Zendesk fields:

```bash
# In .env
ZENDESK_CUSTOM_FIELD_HEALTH_SCORE=360001234567
ZENDESK_CUSTOM_FIELD_ACCOUNT_TIER=360001234568
ZENDESK_CUSTOM_FIELD_MRR=360001234569
```

Use in ticket creation:

```json
{
  "custom_fields": {
    "360001234567": 45,           // Health score
    "360001234568": "enterprise", // Account tier
    "360001234569": 15000         // MRR
  }
}
```

### Webhook Integration (Optional)

Receive real-time updates from Zendesk:

1. **Create Webhook in Zendesk**:
   - Admin → Extensions → Webhooks
   - Endpoint: `https://your-server.com/webhooks/zendesk`
   - Triggers: Ticket Created, Ticket Updated, Ticket Solved

2. **Configure Webhook Secret**:
   ```bash
   ZENDESK_WEBHOOK_SECRET=your-webhook-secret
   ```

3. **Handle Webhook Events**:
   ```bash
   # Webhook endpoint automatically processes:
   # - Ticket status changes
   # - Customer responses
   # - SLA breaches
   ```

### Ticket Views and Filters

Create saved searches for common queries:

```bash
# At-risk customers
search_query = "type:ticket tags:at-risk status:open"

# SLA breaches
search_query = "type:ticket sla:breach status:open"

# High-value accounts
search_query = "type:ticket tags:enterprise priority:urgent"
```

### Auto-Assignment Rules

Configure automatic ticket assignment:

```bash
# In .env
ZENDESK_AUTO_ASSIGN_ENTERPRISE=cs-enterprise-team@company.com
ZENDESK_AUTO_ASSIGN_PROFESSIONAL=cs-team@company.com
ZENDESK_AUTO_ASSIGN_STARTER=support@company.com
```

## Troubleshooting

### Enable Debug Logging

```bash
# In .env
LOG_LEVEL=DEBUG
ZENDESK_DEBUG=true
```

View detailed logs:
```bash
docker-compose logs -f cs-mcp | grep zendesk
```

### Test API Directly

Bypass MCP to test Zendesk API:

```bash
# Test authentication
curl -u "{email}/token:{token}" \
  https://{subdomain}.zendesk.com/api/v2/users/me.json

# Create test ticket
curl -u "{email}/token:{token}" \
  https://{subdomain}.zendesk.com/api/v2/tickets.json \
  -H "Content-Type: application/json" \
  -d '{"ticket":{"subject":"Test","comment":{"body":"Test"}}}'
```

### Check Integration Status

```bash
curl -X GET http://localhost:8080/health
```

Look for:
```json
{
  "integrations": {
    "zendesk": {
      "status": "connected",
      "last_check": "2025-10-10T10:30:00Z",
      "rate_limit_remaining": 650
    }
  }
}
```

### Common Connection Issues

**Issue**: Timeout errors
```bash
# Check firewall rules
# Whitelist Zendesk IPs if needed
# Test connectivity
curl -I https://yourcompany.zendesk.com
```

**Issue**: SSL certificate errors
```bash
# Update CA certificates
# For Ubuntu/Debian:
sudo apt-get update
sudo apt-get install ca-certificates

# For Docker:
docker-compose pull
docker-compose build --no-cache
```

## Performance Optimization

### Caching

Ticket data is cached to reduce API calls:

```bash
# Cache configuration in .env
ZENDESK_CACHE_TTL=300          # 5 minutes
ZENDESK_CACHE_USER_TTL=3600    # 1 hour
```

### Batch Operations

For bulk operations, use batch endpoints:

```bash
# Batch update tickets
curl -X POST http://localhost:8080/tools/batch_update_tickets \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_ids": [12345, 12346, 12347],
    "status": "solved"
  }'
```

### Rate Limit Management

Monitor and manage rate limits:

```bash
# Check current rate limit
curl -X GET http://localhost:8080/tools/zendesk_rate_limit_status

# Response:
{
  "limit": 700,
  "remaining": 543,
  "reset_at": "2025-10-10T11:00:00Z"
}
```

## Security Considerations

### Token Rotation

Rotate API tokens regularly:

```bash
# Recommended: Every 90 days
# 1. Generate new token in Zendesk
# 2. Update .env file
# 3. Test connection
# 4. Deactivate old token
```

### Least Privilege

Create dedicated API user with minimal permissions:

```
Permissions:
- Read/Write tickets
- Read users
- Read organizations
NO admin access
NO account settings
```

### Audit Logging

All Zendesk operations are logged:

```bash
# View audit logs
tail -f config/audit_logs/zendesk_operations.log
```

## Support Resources

### Documentation

- [Zendesk API Documentation](https://developer.zendesk.com/api-reference/)
- [Zenpy Library](https://github.com/facetoe/zenpy)
- [CS MCP Tool Reference](../api/TOOL_REFERENCE.md)

### Getting Help

- **Integration Issues**: Check [Troubleshooting Guide](../operations/TROUBLESHOOTING.md)
- **API Questions**: Zendesk Developer Forum
- **MCP Questions**: GitHub Issues

---

**Last Updated**: October 2025
**Version**: 1.0.0