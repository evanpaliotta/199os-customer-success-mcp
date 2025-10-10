# Customer Success MCP - Quick Start Guide

Get up and running with Customer Success MCP in 5 minutes or less.

## Prerequisites

Before you begin, ensure you have:
- Docker and Docker Compose installed
- 4 GB RAM available
- 10 GB disk space

## 5-Minute Quick Start

### Step 1: Clone and Start (2 minutes)

```bash
# Clone the repository
git clone https://github.com/yourusername/199os-customer-success-mcp.git
cd 199os-customer-success-mcp

# Copy environment configuration
cp .env.example .env

# Start all services
docker-compose up -d

# Wait for services to be ready (~30 seconds)
docker-compose logs -f cs-mcp
```

### Step 2: Run Onboarding Wizard (2 minutes)

```bash
# Launch the interactive setup wizard
docker-compose exec cs-mcp python -m src.tools.onboarding_wizard
```

Follow the wizard prompts:

1. **System Check**: Automatically verifies dependencies
2. **Platform Integrations** (Optional): Skip for now or configure:
   - Zendesk (support tickets)
   - Intercom (messaging)
   - Mixpanel (analytics)
   - SendGrid (email)
3. **Health Score Weights**: Use defaults or customize
4. **Database Setup**: Automatically creates tables

### Step 3: Test the System (1 minute)

#### Register Your First Customer

```bash
curl -X POST http://localhost:8080/tools/register_client \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Acme Corp",
    "contact_name": "Jane Smith",
    "contact_email": "jane@acmecorp.com",
    "subscription_tier": "professional",
    "contract_start_date": "2025-01-01",
    "contract_end_date": "2026-01-01",
    "mrr": 5000
  }'
```

#### Calculate Health Score

```bash
curl -X POST http://localhost:8080/tools/calculate_health_score \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "acme-corp"
  }'
```

#### Create Support Ticket (if Zendesk configured)

```bash
curl -X POST http://localhost:8080/tools/handle_support_ticket \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "acme-corp",
    "subject": "Need help with onboarding",
    "description": "Customer needs assistance with initial setup",
    "priority": "high"
  }'
```

#### Send Email (if SendGrid configured)

```bash
curl -X POST http://localhost:8080/tools/send_personalized_email \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "acme-corp",
    "subject": "Welcome to Our Platform!",
    "template_id": "welcome",
    "merge_data": {
      "company_name": "Acme Corp",
      "contact_name": "Jane"
    }
  }'
```

## What You Just Built

You now have a fully functional Customer Success platform with:

- **49 MCP Tools**: All customer success operations at your fingertips
- **Health Scoring**: Automated customer health calculation
- **Support Integration**: Zendesk ticket creation and management
- **Communication**: Intercom messaging and SendGrid email
- **Analytics**: Mixpanel event tracking and insights
- **Churn Prevention**: Risk identification and retention campaigns

## Next Steps

### 1. Connect to Claude Desktop

Add this configuration to your Claude Desktop MCP settings:

```json
{
  "mcpServers": {
    "customer-success": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "cs-mcp",
        "python",
        "-m",
        "src.server"
      ]
    }
  }
}
```

### 2. Explore Core Workflows

#### Complete Customer Lifecycle

```bash
# 1. Register customer
curl -X POST http://localhost:8080/tools/register_client -H "Content-Type: application/json" -d '{"company_name": "TechStart Inc", "contact_email": "ceo@techstart.io", "subscription_tier": "enterprise", "mrr": 15000}'

# 2. Create onboarding plan
curl -X POST http://localhost:8080/tools/create_onboarding_plan -H "Content-Type: application/json" -d '{"client_id": "techstart-inc", "duration_days": 90}'

# 3. Track usage
curl -X POST http://localhost:8080/tools/track_usage_engagement -H "Content-Type: application/json" -d '{"client_id": "techstart-inc", "logins": 25, "feature_adoption": 0.75}'

# 4. Calculate health score
curl -X POST http://localhost:8080/tools/calculate_health_score -H "Content-Type: application/json" -d '{"client_id": "techstart-inc"}'

# 5. Check for churn risk
curl -X POST http://localhost:8080/tools/identify_churn_risk -H "Content-Type: application/json" -d '{"client_id": "techstart-inc"}'

# 6. Execute retention campaign (if at risk)
curl -X POST http://localhost:8080/tools/execute_retention_campaign -H "Content-Type: application/json" -d '{"client_id": "techstart-inc", "campaign_type": "engagement"}'
```

#### Get Customer Overview

```bash
curl -X POST http://localhost:8080/tools/get_client_overview \
  -H "Content-Type: application/json" \
  -d '{"client_id": "techstart-inc"}'
```

Response:
```json
{
  "client_id": "techstart-inc",
  "company_name": "TechStart Inc",
  "health_score": 85.5,
  "health_status": "good",
  "churn_risk": "low",
  "onboarding_status": "in_progress",
  "onboarding_completion": 45.0,
  "mrr": 15000,
  "subscription_tier": "enterprise",
  "days_to_renewal": 345,
  "open_tickets": 2,
  "recent_activity": [
    {"date": "2025-10-10", "event": "Feature adoption increased to 75%"},
    {"date": "2025-10-09", "event": "Support ticket created: Setup assistance"},
    {"date": "2025-10-08", "event": "Onboarding milestone completed: Initial training"}
  ]
}
```

### 3. Configure Platform Integrations

See detailed setup guides:

- [Zendesk Setup](docs/integrations/ZENDESK_SETUP.md) - Support ticket management
- [Intercom Setup](docs/integrations/INTERCOM_SETUP.md) - Customer messaging
- [Mixpanel Setup](docs/integrations/MIXPANEL_SETUP.md) - Analytics tracking
- [SendGrid Setup](docs/integrations/SENDGRID_SETUP.md) - Email delivery

### 4. Customize Health Scoring

Edit `config/health_weights.json`:

```json
{
  "usage_score_weight": 0.25,
  "engagement_score_weight": 0.20,
  "support_score_weight": 0.15,
  "feedback_score_weight": 0.10,
  "adoption_score_weight": 0.20,
  "renewal_likelihood_weight": 0.10
}
```

Then reload configuration:
```bash
docker-compose restart cs-mcp
```

### 5. Set Up Monitoring

Access Prometheus metrics:
```bash
curl http://localhost:8080/metrics
```

Import Grafana dashboard:
```bash
# Dashboard available at: docs/operations/GRAFANA_DASHBOARD.json
```

## Common Use Cases

### Use Case 1: Automated Customer Health Monitoring

Set up automated health score calculation for all customers:

```python
# Using MCP client (Claude Desktop)
# Ask Claude: "Calculate health scores for all active customers"

# Claude will automatically:
# 1. List all active customers
# 2. Calculate health score for each
# 3. Identify at-risk customers
# 4. Suggest retention campaigns
```

### Use Case 2: Proactive Support

Monitor support tickets and escalate high-priority issues:

```python
# Ask Claude: "Show me all critical support tickets that are past SLA"

# Claude will:
# 1. Query Zendesk for critical tickets
# 2. Check SLA status
# 3. Escalate overdue tickets
# 4. Notify customer success managers
```

### Use Case 3: Expansion Opportunity Identification

Identify customers ready for upsells:

```python
# Ask Claude: "Find customers with high health scores and low feature adoption"

# Claude will:
# 1. Filter customers by health score > 80
# 2. Check feature adoption < 60%
# 3. Identify expansion opportunities
# 4. Generate personalized outreach emails
```

### Use Case 4: NPS Survey Management

Collect and analyze customer feedback:

```python
# Ask Claude: "Send NPS surveys to all enterprise customers"

# Claude will:
# 1. Filter enterprise tier customers
# 2. Send personalized NPS surveys via email
# 3. Track response rates
# 4. Analyze sentiment and generate insights
```

## Environment Variables Quick Reference

Essential variables in `.env`:

```bash
# Database (required)
DATABASE_URL=postgresql://csuser:cspassword@postgres:5432/customerdb
REDIS_URL=redis://redis:6379/0

# Security (required)
ENCRYPTION_KEY=your-32-byte-base64-encoded-key
JWT_SECRET=your-secret-key

# Server Configuration
MCP_PORT=8080
LOG_LEVEL=INFO

# Zendesk (optional)
ZENDESK_SUBDOMAIN=yourcompany
ZENDESK_EMAIL=support@yourcompany.com
ZENDESK_API_TOKEN=your-token

# Intercom (optional)
INTERCOM_ACCESS_TOKEN=your-token

# Mixpanel (optional)
MIXPANEL_PROJECT_TOKEN=your-token
MIXPANEL_API_SECRET=your-secret

# SendGrid (optional)
SENDGRID_API_KEY=your-key
SENDGRID_FROM_EMAIL=noreply@yourcompany.com
```

See [CONFIGURATION.md](CONFIGURATION.md) for complete reference.

## Troubleshooting Quick Fixes

### Server Won't Start

```bash
# Check service logs
docker-compose logs cs-mcp

# Restart services
docker-compose restart

# Rebuild if needed
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Database Connection Error

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Verify connection
docker-compose exec postgres psql -U csuser -d customerdb -c "SELECT 1;"

# Reset database (CAUTION: deletes data)
docker-compose down -v
docker-compose up -d
```

### Port Already in Use

```bash
# Change port in .env
echo "MCP_PORT=8081" >> .env

# Restart with new port
docker-compose down
docker-compose up -d
```

### Integration Not Working

```bash
# Test Zendesk connection
curl -X POST http://localhost:8080/tools/test_zendesk_connection

# Test Intercom connection
curl -X POST http://localhost:8080/tools/test_intercom_connection

# Check environment variables
docker-compose exec cs-mcp env | grep ZENDESK
docker-compose exec cs-mcp env | grep INTERCOM
```

## Learn More

### Documentation

- [Installation Guide](INSTALLATION.md) - Detailed installation instructions
- [Configuration Reference](CONFIGURATION.md) - All environment variables
- [Core Tools Guide](docs/tools/CORE_TOOLS.md) - 5 essential tools
- [API Reference](docs/api/TOOL_REFERENCE.md) - All 49 tools documented
- [Deployment Guide](docs/operations/DEPLOYMENT.md) - Production deployment

### Example Workflows

See example workflows in `examples/`:
- `examples/customer_onboarding.json` - Complete onboarding workflow
- `examples/churn_prevention.json` - Churn risk mitigation
- `examples/expansion_playbook.json` - Upsell and cross-sell
- `examples/support_automation.json` - Support ticket routing

### Video Tutorials

- [5-Minute Setup](https://youtu.be/example) - Getting started
- [Health Scoring Deep Dive](https://youtu.be/example) - Understanding health metrics
- [Integration Setup](https://youtu.be/example) - Configuring platforms

## Support

Need help? We're here for you:

- **Documentation**: Full documentation at [docs/](docs/)
- **GitHub Issues**: https://github.com/yourusername/199os-customer-success-mcp/issues
- **Community Discord**: https://discord.gg/cs-mcp
- **Email**: support@customer-success-mcp.com

## What's Next?

Now that you have Customer Success MCP running:

1. Import your customer data
2. Configure platform integrations
3. Customize health score weights
4. Set up retention campaigns
5. Connect to Claude Desktop
6. Automate your customer success workflows

Welcome to automated, AI-powered customer success!

---

**Congratulations!** You've successfully set up Customer Success MCP. Start building amazing customer experiences today.