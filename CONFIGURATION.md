# Customer Success MCP - Configuration Reference

Complete reference for all configuration options and environment variables.

## Table of Contents

1. [Overview](#overview)
2. [Server Configuration](#server-configuration)
3. [Database Configuration](#database-configuration)
4. [Security Configuration](#security-configuration)
5. [Platform Integrations](#platform-integrations)
6. [Health Score Configuration](#health-score-configuration)
7. [Onboarding Configuration](#onboarding-configuration)
8. [Retention Configuration](#retention-configuration)
9. [Expansion Configuration](#expansion-configuration)
10. [Support Configuration](#support-configuration)
11. [Monitoring Configuration](#monitoring-configuration)
12. [Feature Flags](#feature-flags)
13. [Learning System Configuration](#learning-system-configuration)
14. [Advanced Configuration](#advanced-configuration)

## Overview

The Customer Success MCP is configured entirely through environment variables defined in the `.env` file. This approach provides:

- **Environment Isolation**: Different configurations for development, staging, and production
- **Security**: Sensitive credentials stored separately from code
- **Flexibility**: Easy customization without code changes
- **Docker Compatibility**: Seamless integration with containerized deployments

### Configuration File Locations

| File | Purpose | Required |
|------|---------|----------|
| `.env` | Main environment variables | Yes |
| `.env.example` | Template with all options | No (reference only) |
| `config/health_weights.json` | Health score component weights | No (optional override) |
| `config/sla_targets.json` | Custom SLA targets | No (optional override) |
| `config/retention_triggers.json` | Retention campaign rules | No (optional override) |
| `config/mcp_servers.json` | MCP server integrations | No (auto-generated) |

### Getting Started

```bash
# Copy the example configuration
cp .env.example .env

# Edit with your settings
nano .env  # or vim, code, etc.

# Validate configuration
python -m src.utils.validate_config

# Restart server to apply changes
docker-compose restart cs-mcp
```

## Server Configuration

Basic server settings and runtime behavior.

### SERVER_NAME

**Description**: Display name for the MCP server
**Type**: String
**Default**: `199OS-CustomerSuccess`
**Required**: No

```bash
SERVER_NAME=199OS-CustomerSuccess
```

### SERVER_PORT

**Description**: Port the MCP server listens on
**Type**: Integer (1-65535)
**Default**: `8080`
**Required**: No

```bash
SERVER_PORT=8080
```

**Note**: In Docker deployments, this is the internal port. External port mapping is configured in `docker-compose.yml`.

### LOG_LEVEL

**Description**: Logging verbosity level
**Type**: Enum
**Values**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
**Default**: `INFO`
**Required**: No

```bash
LOG_LEVEL=INFO
```

**Recommendations**:
- **Development**: `DEBUG` - See all operations
- **Staging**: `INFO` - Normal operational info
- **Production**: `WARNING` - Only warnings and errors

### LOG_FORMAT

**Description**: Log output format
**Type**: Enum
**Values**: `json`, `text`
**Default**: `json`
**Required**: No

```bash
LOG_FORMAT=json
```

**Note**: Use `json` for production (easier to parse), `text` for local development (easier to read).

## Database Configuration

PostgreSQL database and connection pooling settings.

### DATABASE_URL

**Description**: PostgreSQL connection string
**Type**: String (PostgreSQL DSN format)
**Required**: Yes

```bash
DATABASE_URL=postgresql://username:password@host:port/database
```

**Examples**:
```bash
# Local development
DATABASE_URL=postgresql://csuser:cspassword@localhost:5432/customerdb

# Docker Compose
DATABASE_URL=postgresql://csuser:cspassword@postgres:5432/customerdb

# AWS RDS
DATABASE_URL=postgresql://admin:SecurePassword123@cs-mcp.abc123.us-east-1.rds.amazonaws.com:5432/customerdb

# With SSL required
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

### DB_POOL_SIZE

**Description**: Number of database connections to maintain in pool
**Type**: Integer
**Default**: `20`
**Required**: No

```bash
DB_POOL_SIZE=20
```

**Sizing Guidelines**:
- Small deployments (<100 users): `10-20`
- Medium deployments (100-1000 users): `20-50`
- Large deployments (>1000 users): `50-100`

### DB_MAX_OVERFLOW

**Description**: Maximum additional connections beyond pool size
**Type**: Integer
**Default**: `10`
**Required**: No

```bash
DB_MAX_OVERFLOW=10
```

### DB_POOL_TIMEOUT

**Description**: Seconds to wait for available connection before timeout
**Type**: Integer (seconds)
**Default**: `30`
**Required**: No

```bash
DB_POOL_TIMEOUT=30
```

### DB_SSL_MODE

**Description**: SSL/TLS mode for database connections
**Type**: Enum
**Values**: `disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full`
**Default**: `require`
**Required**: No

```bash
DB_SSL_MODE=require
```

**Recommendations**:
- **Production**: `require` or `verify-full`
- **Development**: `prefer` or `disable`

## Redis Configuration

Redis cache and session management settings.

### REDIS_URL

**Description**: Redis connection string
**Type**: String (Redis URL format)
**Required**: Yes

```bash
REDIS_URL=redis://host:port/db
```

**Examples**:
```bash
# Local without password
REDIS_URL=redis://localhost:6379/0

# Docker Compose
REDIS_URL=redis://redis:6379/0

# With password
REDIS_URL=redis://:password@localhost:6379/0

# AWS ElastiCache
REDIS_URL=redis://cs-mcp-cache.abc123.use1.cache.amazonaws.com:6379/0

# Redis Cluster
REDIS_URL=redis://node1:6379,node2:6379,node3:6379/0
```

### REDIS_PASSWORD

**Description**: Password for Redis authentication
**Type**: String
**Default**: None
**Required**: No (but recommended for production)

```bash
REDIS_PASSWORD=your-secure-redis-password
```

### REDIS_MAX_CONNECTIONS

**Description**: Maximum number of Redis connections in pool
**Type**: Integer
**Default**: `50`
**Required**: No

```bash
REDIS_MAX_CONNECTIONS=50
```

### CACHE_DEFAULT_TTL

**Description**: Default cache time-to-live in seconds
**Type**: Integer (seconds)
**Default**: `3600` (1 hour)
**Required**: No

```bash
CACHE_DEFAULT_TTL=3600
```

**Used For**:
- Health scores
- Customer overviews
- API responses

### CACHE_LONG_TTL

**Description**: Long-term cache TTL for infrequently changing data
**Type**: Integer (seconds)
**Default**: `86400` (24 hours)
**Required**: No

```bash
CACHE_LONG_TTL=86400
```

**Used For**:
- Segment definitions
- Knowledge base articles
- Configuration data

### Rate Limiting

Control request rates to prevent abuse and ensure system stability.

#### MAX_REQUESTS_PER_MINUTE

**Description**: Global rate limit per minute (all clients)
**Type**: Integer
**Default**: `1000`
**Required**: No

```bash
MAX_REQUESTS_PER_MINUTE=1000
```

#### MAX_REQUESTS_PER_HOUR

**Description**: Global rate limit per hour (all clients)
**Type**: Integer
**Default**: `10000`
**Required**: No

```bash
MAX_REQUESTS_PER_HOUR=10000
```

#### RATE_LIMIT_PER_CLIENT_PER_MINUTE

**Description**: Per-client rate limit per minute
**Type**: Integer
**Default**: `100`
**Required**: No

```bash
RATE_LIMIT_PER_CLIENT_PER_MINUTE=100
```

## Security Configuration

Critical security settings for credential management and encryption.

### MASTER_PASSWORD

**Description**: Master password for encrypting stored credentials
**Type**: String (32+ characters recommended)
**Required**: Yes

```bash
MASTER_PASSWORD=your-strong-master-password-here
```

**Generate Securely**:
```bash
openssl rand -base64 32
```

**Warning**: Changing this password will invalidate all stored credentials.

### ENCRYPTION_KEY

**Description**: Key for encrypting sensitive data at rest
**Type**: String (32+ bytes hex-encoded)
**Required**: Yes

```bash
ENCRYPTION_KEY=your-encryption-key-here
```

**Generate Securely**:
```bash
openssl rand -hex 32
```

### JWT_SECRET

**Description**: Secret for signing JWT tokens
**Type**: String (64+ characters recommended)
**Required**: Yes

```bash
JWT_SECRET=your-jwt-secret-here
```

**Generate Securely**:
```bash
openssl rand -base64 64
```

### MCP_API_KEY

**Description**: API key for authenticating MCP server requests
**Type**: String
**Default**: None (optional)
**Required**: No

```bash
MCP_API_KEY=your-mcp-api-key-here
```

### WEBHOOK_SECRET

**Description**: Secret for verifying incoming webhook signatures
**Type**: String
**Default**: None
**Required**: No (required if using webhooks)

```bash
WEBHOOK_SECRET=your-webhook-secret
```

## Platform Integrations

Configure third-party platform integrations for Customer Success workflows.

### Zendesk (Support Platform)

**Purpose**: Create and manage support tickets, track SLA compliance.

#### ZENDESK_SUBDOMAIN

**Description**: Your Zendesk subdomain
**Type**: String
**Required**: Only if using Zendesk integration

```bash
ZENDESK_SUBDOMAIN=yourcompany
```

**Example**: For `yourcompany.zendesk.com`, use `yourcompany`

#### ZENDESK_EMAIL

**Description**: Email address for Zendesk API authentication
**Type**: String (email)
**Required**: Only if using Zendesk integration

```bash
ZENDESK_EMAIL=support@yourcompany.com
```

#### ZENDESK_API_TOKEN

**Description**: Zendesk API token for authentication
**Type**: String
**Required**: Only if using Zendesk integration

```bash
ZENDESK_API_TOKEN=your-zendesk-api-token
```

**How to Obtain**: See [Zendesk Setup Guide](docs/integrations/ZENDESK_SETUP.md)

### Intercom (Customer Messaging)

**Purpose**: Send messages, track events, manage customer profiles.

#### INTERCOM_ACCESS_TOKEN

**Description**: Intercom API access token
**Type**: String
**Required**: Only if using Intercom integration

```bash
INTERCOM_ACCESS_TOKEN=your-intercom-access-token
```

#### INTERCOM_APP_ID

**Description**: Intercom application ID
**Type**: String
**Required**: Only if using Intercom integration

```bash
INTERCOM_APP_ID=your-intercom-app-id
```

**How to Obtain**: See [Intercom Setup Guide](docs/integrations/INTERCOM_SETUP.md)

### Mixpanel (Product Analytics)

**Purpose**: Track events, analyze usage, query analytics data.

#### MIXPANEL_PROJECT_TOKEN

**Description**: Mixpanel project token for event tracking
**Type**: String
**Required**: Only if using Mixpanel integration

```bash
MIXPANEL_PROJECT_TOKEN=your-mixpanel-project-token
```

#### MIXPANEL_API_SECRET

**Description**: Mixpanel API secret for querying data
**Type**: String
**Required**: Only if using Mixpanel integration

```bash
MIXPANEL_API_SECRET=your-mixpanel-api-secret
```

**How to Obtain**: See [Mixpanel Setup Guide](docs/integrations/MIXPANEL_SETUP.md)

### SendGrid (Email Delivery)

**Purpose**: Send transactional and marketing emails.

#### SENDGRID_API_KEY

**Description**: SendGrid API key
**Type**: String
**Required**: Only if using SendGrid integration

```bash
SENDGRID_API_KEY=your-sendgrid-api-key
```

#### SENDGRID_FROM_EMAIL

**Description**: Default sender email address
**Type**: String (email)
**Required**: Only if using SendGrid integration

```bash
SENDGRID_FROM_EMAIL=noreply@yourcompany.com
```

**Note**: Email must be verified in SendGrid

#### SENDGRID_FROM_NAME

**Description**: Default sender name
**Type**: String
**Default**: `Your Company`
**Required**: No

```bash
SENDGRID_FROM_NAME=Your Company
```

#### SENDGRID_MAX_RETRIES

**Description**: Number of retries for failed email sends
**Type**: Integer
**Default**: `3`
**Required**: No

```bash
SENDGRID_MAX_RETRIES=3
```

#### SENDGRID_RETRY_DELAY

**Description**: Delay between retries in seconds
**Type**: Integer
**Default**: `1`
**Required**: No

```bash
SENDGRID_RETRY_DELAY=1
```

#### SENDGRID_BATCH_SIZE

**Description**: Maximum emails per batch send
**Type**: Integer
**Default**: `1000`
**Required**: No

```bash
SENDGRID_BATCH_SIZE=1000
```

**How to Obtain**: See [SendGrid Setup Guide](docs/integrations/SENDGRID_SETUP.md)

### Additional Integrations

#### Salesforce CRM

```bash
SALESFORCE_USERNAME=your-salesforce-username
SALESFORCE_PASSWORD=your-salesforce-password
SALESFORCE_SECURITY_TOKEN=your-security-token
```

#### HubSpot CRM

```bash
HUBSPOT_ACCESS_TOKEN=your-hubspot-access-token
```

#### Slack

```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
```

## Health Score Configuration

Configure customer health score calculation methodology.

### Weight Distribution

Health score weights must sum to `1.0` (100%).

#### HEALTH_SCORE_WEIGHT_USAGE

**Description**: Weight for product usage metrics
**Type**: Float (0.0-1.0)
**Default**: `0.35` (35%)
**Required**: No

```bash
HEALTH_SCORE_WEIGHT_USAGE=0.35
```

**Includes**:
- Login frequency
- Session duration
- Daily/weekly active usage
- Feature adoption rate

#### HEALTH_SCORE_WEIGHT_ENGAGEMENT

**Description**: Weight for customer engagement metrics
**Type**: Float (0.0-1.0)
**Default**: `0.25` (25%)
**Required**: No

```bash
HEALTH_SCORE_WEIGHT_ENGAGEMENT=0.25
```

**Includes**:
- Email open rates
- Response rates
- Community participation
- Event attendance

#### HEALTH_SCORE_WEIGHT_SUPPORT

**Description**: Weight for support interaction metrics
**Type**: Float (0.0-1.0)
**Default**: `0.15` (15%)
**Required**: No

```bash
HEALTH_SCORE_WEIGHT_SUPPORT=0.15
```

**Includes**:
- Ticket volume (inverse)
- Ticket severity (inverse)
- Resolution time
- Customer satisfaction (CSAT)

#### HEALTH_SCORE_WEIGHT_SATISFACTION

**Description**: Weight for customer satisfaction metrics
**Type**: Float (0.0-1.0)
**Default**: `0.15` (15%)
**Required**: No

```bash
HEALTH_SCORE_WEIGHT_SATISFACTION=0.15
```

**Includes**:
- NPS score
- CSAT ratings
- Survey responses
- Sentiment analysis

#### HEALTH_SCORE_WEIGHT_PAYMENT

**Description**: Weight for payment and billing metrics
**Type**: Float (0.0-1.0)
**Default**: `0.10` (10%)
**Required**: No

```bash
HEALTH_SCORE_WEIGHT_PAYMENT=0.10
```

**Includes**:
- Payment timeliness
- Billing disputes (inverse)
- Plan utilization
- Contract term remaining

### Health Score Thresholds

Define score ranges for customer health categorization.

#### HEALTH_SCORE_AT_RISK_THRESHOLD

**Description**: Maximum score for "At Risk" status
**Type**: Integer (0-100)
**Default**: `50`
**Required**: No

```bash
HEALTH_SCORE_AT_RISK_THRESHOLD=50
```

**Status Mapping**:
- `0-50`: At Risk (red)
- `51-74`: Needs Attention (yellow)
- `75-89`: Healthy (green)
- `90-100`: Champion (blue)

#### HEALTH_SCORE_HEALTHY_THRESHOLD

**Description**: Minimum score for "Healthy" status
**Type**: Integer (0-100)
**Default**: `75`
**Required**: No

```bash
HEALTH_SCORE_HEALTHY_THRESHOLD=75
```

#### HEALTH_SCORE_CHAMPION_THRESHOLD

**Description**: Minimum score for "Champion" status
**Type**: Integer (0-100)
**Default**: `90`
**Required**: No

```bash
HEALTH_SCORE_CHAMPION_THRESHOLD=90
```

### Churn Prediction

#### CHURN_PROBABILITY_HIGH_RISK

**Description**: Minimum probability for "High Risk" classification
**Type**: Float (0.0-1.0)
**Default**: `0.70` (70%)
**Required**: No

```bash
CHURN_PROBABILITY_HIGH_RISK=0.70
```

#### CHURN_PROBABILITY_MEDIUM_RISK

**Description**: Minimum probability for "Medium Risk" classification
**Type**: Float (0.0-1.0)
**Default**: `0.40` (40%)
**Required**: No

```bash
CHURN_PROBABILITY_MEDIUM_RISK=0.40
```

#### CHURN_PROBABILITY_LOW_RISK

**Description**: Minimum probability for "Low Risk" classification
**Type**: Float (0.0-1.0)
**Default**: `0.15` (15%)
**Required**: No

```bash
CHURN_PROBABILITY_LOW_RISK=0.15
```

## Onboarding Configuration

Configure customer onboarding timelines and milestones.

### TIME_TO_VALUE_TARGET

**Description**: Target days to deliver value to new customers
**Type**: Integer (days)
**Default**: `30`
**Required**: No

```bash
TIME_TO_VALUE_TARGET=30
```

### TIME_TO_FIRST_VALUE

**Description**: Target days to first "aha moment"
**Type**: Integer (days)
**Default**: `7`
**Required**: No

```bash
TIME_TO_FIRST_VALUE=7
```

### TIME_TO_ACTIVATION

**Description**: Target days to product activation
**Type**: Integer (days)
**Default**: `14`
**Required**: No

```bash
TIME_TO_ACTIVATION=14
```

### ONBOARDING_COMPLETION_THRESHOLD

**Description**: Minimum completion percentage for successful onboarding
**Type**: Float (0.0-1.0)
**Default**: `0.80` (80%)
**Required**: No

```bash
ONBOARDING_COMPLETION_THRESHOLD=0.80
```

### TRAINING_COMPLETION_THRESHOLD

**Description**: Minimum training completion percentage
**Type**: Float (0.0-1.0)
**Default**: `0.75` (75%)
**Required**: No

```bash
TRAINING_COMPLETION_THRESHOLD=0.75
```

## Retention Configuration

Configure retention campaign triggers and renewal workflows.

### RETENTION_CAMPAIGN_TRIGGER_SCORE

**Description**: Health score threshold to trigger retention campaign
**Type**: Integer (0-100)
**Default**: `60`
**Required**: No

```bash
RETENTION_CAMPAIGN_TRIGGER_SCORE=60
```

### RETENTION_CAMPAIGN_FREQUENCY_DAYS

**Description**: Minimum days between retention campaigns
**Type**: Integer (days)
**Default**: `7`
**Required**: No

```bash
RETENTION_CAMPAIGN_FREQUENCY_DAYS=7
```

### RETENTION_ESCALATION_SCORE

**Description**: Health score threshold for executive escalation
**Type**: Integer (0-100)
**Default**: `40`
**Required**: No

```bash
RETENTION_ESCALATION_SCORE=40
```

### RENEWAL_REMINDER_DAYS_BEFORE

**Description**: Days before renewal to send reminders (comma-separated)
**Type**: String (comma-separated integers)
**Default**: `90,60,30,14,7`
**Required**: No

```bash
RENEWAL_REMINDER_DAYS_BEFORE=90,60,30,14,7
```

### RENEWAL_FORECAST_WINDOW_DAYS

**Description**: Days ahead to forecast renewals
**Type**: Integer (days)
**Default**: `90`
**Required**: No

```bash
RENEWAL_FORECAST_WINDOW_DAYS=90
```

## Expansion Configuration

Configure upsell and cross-sell opportunity identification.

### EXPANSION_MIN_HEALTH_SCORE

**Description**: Minimum health score for expansion consideration
**Type**: Integer (0-100)
**Default**: `75`
**Required**: No

```bash
EXPANSION_MIN_HEALTH_SCORE=75
```

### EXPANSION_MIN_USAGE_THRESHOLD

**Description**: Minimum usage rate for expansion eligibility
**Type**: Float (0.0-1.0)
**Default**: `0.70` (70%)
**Required**: No

```bash
EXPANSION_MIN_USAGE_THRESHOLD=0.70
```

### EXPANSION_MIN_TENURE_DAYS

**Description**: Minimum customer tenure for expansion offers
**Type**: Integer (days)
**Default**: `60`
**Required**: No

```bash
EXPANSION_MIN_TENURE_DAYS=60
```

### UPSELL_OPPORTUNITY_THRESHOLD

**Description**: Score threshold for upsell recommendation
**Type**: Float (0.0-1.0)
**Default**: `0.65` (65%)
**Required**: No

```bash
UPSELL_OPPORTUNITY_THRESHOLD=0.65
```

### CROSS_SELL_OPPORTUNITY_THRESHOLD

**Description**: Score threshold for cross-sell recommendation
**Type**: Float (0.0-1.0)
**Default**: `0.60` (60%)
**Required**: No

```bash
CROSS_SELL_OPPORTUNITY_THRESHOLD=0.60
```

## Support Configuration

Configure SLA targets and escalation rules.

### SLA Targets (in minutes)

#### SUPPORT_FIRST_RESPONSE_SLA

**Description**: Target minutes for first response to new tickets
**Type**: Integer (minutes)
**Default**: `15`
**Required**: No

```bash
SUPPORT_FIRST_RESPONSE_SLA=15
```

#### SUPPORT_RESOLUTION_SLA_P1

**Description**: Resolution SLA for P1 (Critical) tickets
**Type**: Integer (minutes)
**Default**: `240` (4 hours)
**Required**: No

```bash
SUPPORT_RESOLUTION_SLA_P1=240
```

#### SUPPORT_RESOLUTION_SLA_P2

**Description**: Resolution SLA for P2 (High) tickets
**Type**: Integer (minutes)
**Default**: `480` (8 hours)
**Required**: No

```bash
SUPPORT_RESOLUTION_SLA_P2=480
```

#### SUPPORT_RESOLUTION_SLA_P3

**Description**: Resolution SLA for P3 (Normal) tickets
**Type**: Integer (minutes)
**Default**: `1440` (24 hours)
**Required**: No

```bash
SUPPORT_RESOLUTION_SLA_P3=1440
```

### Escalation Rules

#### SUPPORT_ESCALATION_NO_RESPONSE_HOURS

**Description**: Hours without response before escalation
**Type**: Integer (hours)
**Default**: `2`
**Required**: No

```bash
SUPPORT_ESCALATION_NO_RESPONSE_HOURS=2
```

#### SUPPORT_ESCALATION_NO_RESOLUTION_DAYS

**Description**: Days without resolution before escalation
**Type**: Integer (days)
**Default**: `3`
**Required**: No

```bash
SUPPORT_ESCALATION_NO_RESOLUTION_DAYS=3
```

## Monitoring Configuration

Configure observability and audit logging.

### ENABLE_MONITORING

**Description**: Enable Prometheus metrics endpoint
**Type**: Boolean
**Default**: `true`
**Required**: No

```bash
ENABLE_MONITORING=true
```

### ENABLE_AUDIT_LOGGING

**Description**: Enable comprehensive audit logging
**Type**: Boolean
**Default**: `true`
**Required**: No

```bash
ENABLE_AUDIT_LOGGING=true
```

### ENABLE_TRACING

**Description**: Enable distributed tracing
**Type**: Boolean
**Default**: `true`
**Required**: No

```bash
ENABLE_TRACING=true
```

### AUDIT_LOG_RETENTION_DAYS

**Description**: Days to retain audit logs
**Type**: Integer (days)
**Default**: `90`
**Required**: No

```bash
AUDIT_LOG_RETENTION_DAYS=90
```

### AUDIT_LOG_DIR

**Description**: Directory for audit log files
**Type**: String (path)
**Default**: `./config/audit_logs`
**Required**: No

```bash
AUDIT_LOG_DIR=./config/audit_logs
```

## Feature Flags

Enable or disable specific features.

### FEATURE_CHURN_PREDICTION

**Description**: Enable churn prediction algorithms
**Type**: Boolean
**Default**: `true`
**Required**: No

```bash
FEATURE_CHURN_PREDICTION=true
```

### FEATURE_HEALTH_SCORING

**Description**: Enable health score calculation
**Type**: Boolean
**Default**: `true`
**Required**: No

```bash
FEATURE_HEALTH_SCORING=true
```

### FEATURE_AUTOMATED_RETENTION

**Description**: Enable automated retention campaigns
**Type**: Boolean
**Default**: `true`
**Required**: No

```bash
FEATURE_AUTOMATED_RETENTION=true
```

### FEATURE_EXPANSION_SCORING

**Description**: Enable expansion opportunity scoring
**Type**: Boolean
**Default**: `true`
**Required**: No

```bash
FEATURE_EXPANSION_SCORING=true
```

### FEATURE_SENTIMENT_ANALYSIS

**Description**: Enable sentiment analysis on feedback
**Type**: Boolean
**Default**: `true`
**Required**: No

```bash
FEATURE_SENTIMENT_ANALYSIS=true
```

## Learning System Configuration

Configure the adaptive learning system.

### LEARNING_COMPLETION_THRESHOLD

**Description**: Confidence threshold for learning questions
**Type**: Float (0.0-1.0)
**Default**: `0.70` (70%)
**Required**: No

```bash
LEARNING_COMPLETION_THRESHOLD=0.70
```

### LEARNING_FREQUENCY

**Description**: How often to ask learning questions
**Type**: Enum
**Values**: `always`, `often`, `occasionally`, `rarely`
**Default**: `often`
**Required**: No

```bash
LEARNING_FREQUENCY=often
```

### PREFERENCES_DIR

**Description**: Directory for storing learned preferences
**Type**: String (path)
**Default**: `./config/preferences`
**Required**: No

```bash
PREFERENCES_DIR=./config/preferences
```

## Advanced Configuration

### MCP Integration Control

```bash
# Enable/disable specific MCP servers
MCP_ENABLE_ZENDESK=true
MCP_ENABLE_INTERCOM=true
MCP_ENABLE_MIXPANEL=true
MCP_ENABLE_SENDGRID=true
MCP_ENABLE_SALESFORCE=false
MCP_ENABLE_HUBSPOT=false
```

### MCP Configuration Path

```bash
MCP_CONFIG_PATH=./config/mcp_servers.json
```

## Configuration Validation

Validate your configuration before starting:

```bash
# Validate all settings
python -m src.utils.validate_config

# Check specific sections
python -m src.utils.validate_config --section database
python -m src.utils.validate_config --section security
python -m src.utils.validate_config --section integrations
```

## Configuration Best Practices

### Development Environment

```bash
# .env.dev
LOG_LEVEL=DEBUG
LOG_FORMAT=text
DB_SSL_MODE=disable
ENABLE_MONITORING=false
FEATURE_CHURN_PREDICTION=false  # Speed up testing
```

### Staging Environment

```bash
# .env.staging
LOG_LEVEL=INFO
LOG_FORMAT=json
DB_SSL_MODE=require
ENABLE_MONITORING=true
ENABLE_AUDIT_LOGGING=true
```

### Production Environment

```bash
# .env.prod
LOG_LEVEL=WARNING
LOG_FORMAT=json
DB_SSL_MODE=verify-full
ENABLE_MONITORING=true
ENABLE_AUDIT_LOGGING=true
ENABLE_TRACING=true
AUDIT_LOG_RETENTION_DAYS=365
```

## Troubleshooting Configuration

### Common Issues

**Issue**: Configuration validation fails
```bash
# Check syntax errors
python -m src.utils.validate_config --verbose

# Verify environment variables are set
env | grep DATABASE_URL
env | grep REDIS_URL
```

**Issue**: Health score weights don't sum to 1.0
```bash
# Check current weights
python -c "from src.config import config; print(config.get_health_weights())"

# Recalculate proportionally
python -m src.utils.normalize_health_weights
```

**Issue**: Platform integration not working
```bash
# Test connection
curl -X POST http://localhost:8080/tools/test_zendesk_connection
curl -X POST http://localhost:8080/tools/test_intercom_connection

# Verify credentials
docker-compose exec cs-mcp env | grep ZENDESK
```

## See Also

- [Installation Guide](INSTALLATION.md)
- [Quick Start](QUICK_START.md)
- [Platform Integration Guides](docs/integrations/)
- [Security Best Practices](docs/operations/SECURITY.md)
- [Troubleshooting](docs/operations/TROUBLESHOOTING.md)

---

**Last Updated**: October 2025
**Version**: 1.0.0