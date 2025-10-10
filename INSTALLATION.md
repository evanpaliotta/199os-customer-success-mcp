# Customer Success MCP - Installation Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Installation Methods](#installation-methods)
   - [Docker Installation (Recommended)](#docker-installation-recommended)
   - [Local Development Installation](#local-development-installation)
   - [Production Installation](#production-installation)
4. [Configuration](#configuration)
5. [Post-Installation Verification](#post-installation-verification)
6. [Troubleshooting](#troubleshooting)
7. [Uninstallation](#uninstallation)
8. [Support](#support)

## Prerequisites

Before installing the Customer Success MCP, ensure you have the following prerequisites installed and configured on your system:

### Required Software

| Software | Minimum Version | Recommended Version | Purpose |
|----------|----------------|-------------------|---------|
| **Python** | 3.10+ | 3.11+ | Core runtime environment |
| **PostgreSQL** | 14+ | 16+ | Primary database for customer data |
| **Redis** | 6.2+ | 7.0+ | Caching and session management |
| **Docker** | 20.10+ | 24.0+ | Container runtime (for Docker installation) |
| **Docker Compose** | 2.0+ | 2.20+ | Multi-container orchestration |
| **Git** | 2.30+ | Latest | Source code management |

### Platform Accounts (Optional)

To fully utilize all features, you'll need API credentials for:

- **Zendesk**: For support ticket management
- **Intercom**: For customer communication
- **Mixpanel**: For analytics and usage tracking
- **SendGrid**: For email delivery

> **Note**: The system can run without these integrations, but functionality will be limited.

### Network Requirements

- **Outbound Internet Access**: Required for platform integrations
- **Port 8080**: Default MCP server port (configurable)
- **Port 5432**: PostgreSQL database (if not using Docker)
- **Port 6379**: Redis cache (if not using Docker)

## System Requirements

### Minimum Requirements

- **CPU**: 2 cores (x86_64 or ARM64)
- **RAM**: 4 GB
- **Storage**: 10 GB available disk space
- **OS**: Linux (Ubuntu 20.04+), macOS (11+), or Windows (with WSL2)

### Recommended Requirements

- **CPU**: 4+ cores
- **RAM**: 8 GB+
- **Storage**: 20 GB+ SSD
- **OS**: Ubuntu 22.04 LTS or macOS 13+

### Production Requirements

- **CPU**: 8+ cores
- **RAM**: 16 GB+
- **Storage**: 100 GB+ SSD with regular backups
- **Database**: Dedicated PostgreSQL instance (RDS, Cloud SQL, etc.)
- **Cache**: Dedicated Redis instance (ElastiCache, Redis Cloud, etc.)
- **Load Balancer**: For high availability
- **Monitoring**: Prometheus + Grafana setup

## Installation Methods

### Docker Installation (Recommended)

Docker provides the simplest and most consistent installation experience across all platforms.

#### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/199os-customer-success-mcp.git
cd 199os-customer-success-mcp
```

#### Step 2: Create Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit the configuration file with your settings
# Use your preferred editor (nano, vim, code, etc.)
nano .env
```

#### Step 3: Configure Required Environment Variables

At minimum, configure these variables in your `.env` file:

```bash
# Database Configuration
DATABASE_URL=postgresql://csuser:cspassword@postgres:5432/customerdb
REDIS_URL=redis://redis:6379/0

# Security Configuration
ENCRYPTION_KEY=your-32-byte-encryption-key-here
JWT_SECRET=your-jwt-secret-key-here

# Platform Integrations (optional but recommended)
ZENDESK_SUBDOMAIN=yourcompany
ZENDESK_EMAIL=support@yourcompany.com
ZENDESK_API_TOKEN=your-zendesk-token

INTERCOM_ACCESS_TOKEN=your-intercom-token

MIXPANEL_PROJECT_TOKEN=your-mixpanel-token
MIXPANEL_API_SECRET=your-mixpanel-secret

SENDGRID_API_KEY=your-sendgrid-key
SENDGRID_FROM_EMAIL=noreply@yourcompany.com
```

#### Step 4: Build and Start Services

```bash
# Build the Docker image
docker-compose build

# Start all services in detached mode
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f cs-mcp
```

#### Step 5: Run Database Migrations

```bash
# Initialize the database schema
docker-compose exec cs-mcp alembic upgrade head

# Verify database tables
docker-compose exec postgres psql -U csuser -d customerdb -c "\dt"
```

#### Step 6: Run the Onboarding Wizard

```bash
# Start the interactive onboarding wizard
docker-compose exec cs-mcp python -m src.tools.onboarding_wizard

# Follow the prompts to configure your instance
```

### Local Development Installation

For developers who prefer running the application directly on their machine.

#### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip
sudo apt-get install -y postgresql postgresql-contrib redis-server
sudo apt-get install -y git build-essential libpq-dev
```

**macOS (using Homebrew):**
```bash
brew install python@3.11 postgresql@16 redis git
brew services start postgresql@16
brew services start redis
```

**Windows (using WSL2):**
```bash
# Inside WSL2 Ubuntu
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip
sudo apt-get install -y postgresql postgresql-contrib redis-server
```

#### Step 2: Clone and Setup Python Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/199os-customer-success-mcp.git
cd 199os-customer-success-mcp

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

#### Step 3: Install Python Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt

# Verify installation
python -c "import fastmcp; import pydantic; print('Dependencies installed successfully')"
```

#### Step 4: Setup Database

```bash
# Create PostgreSQL user and database
sudo -u postgres psql << EOF
CREATE USER csuser WITH PASSWORD 'cspassword';
CREATE DATABASE customerdb OWNER csuser;
GRANT ALL PRIVILEGES ON DATABASE customerdb TO csuser;
EOF

# Test database connection
psql -U csuser -h localhost -d customerdb -c "SELECT version();"
```

#### Step 5: Configure Redis

```bash
# Test Redis connection
redis-cli ping
# Should return: PONG

# Set Redis password (optional but recommended)
redis-cli CONFIG SET requirepass "your-redis-password"
```

#### Step 6: Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env

# Update DATABASE_URL for local setup
DATABASE_URL=postgresql://csuser:cspassword@localhost:5432/customerdb
REDIS_URL=redis://localhost:6379/0
```

#### Step 7: Initialize Database

```bash
# Run database migrations
alembic upgrade head

# Verify tables created
psql -U csuser -h localhost -d customerdb -c "\dt"
```

#### Step 8: Start the Server

```bash
# Run the MCP server
python -m src.server

# Server should start on http://localhost:8080
# Check health endpoint: curl http://localhost:8080/health
```

### Production Installation

For deploying to production environments with high availability and security.

#### Step 1: Provision Infrastructure

**AWS Example:**
```bash
# Provision RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier cs-mcp-db \
  --db-instance-class db.t3.large \
  --engine postgres \
  --engine-version 16.1 \
  --master-username csadmin \
  --master-user-password <secure-password> \
  --allocated-storage 100 \
  --backup-retention-period 7

# Provision ElastiCache Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id cs-mcp-cache \
  --cache-node-type cache.t3.medium \
  --engine redis \
  --engine-version 7.0 \
  --num-cache-nodes 2
```

#### Step 2: Setup Kubernetes Deployment

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cs-mcp
  namespace: customer-success
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cs-mcp
  template:
    metadata:
      labels:
        app: cs-mcp
    spec:
      containers:
      - name: cs-mcp
        image: your-registry/cs-mcp:latest
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: cs-mcp-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: cs-mcp-secrets
              key: redis-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### Step 3: Configure Load Balancer and TLS

```yaml
# kubernetes/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: cs-mcp-service
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: arn:aws:acm:...
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: http
spec:
  type: LoadBalancer
  selector:
    app: cs-mcp
  ports:
    - port: 443
      targetPort: 8080
      protocol: TCP
```

## Configuration

### Essential Configuration Files

1. **`.env`** - Main configuration file with environment variables
2. **`config/health_weights.json`** - Health score component weights
3. **`config/sla_targets.json`** - SLA response time targets
4. **`config/retention_triggers.json`** - Retention campaign triggers

### Configuration Validation

Run the configuration validator to ensure all settings are correct:

```bash
# Docker installation
docker-compose exec cs-mcp python -m src.utils.validate_config

# Local installation
python -m src.utils.validate_config
```

## Post-Installation Verification

### Step 1: Check Service Health

```bash
# Check MCP server health
curl http://localhost:8080/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected",
  "integrations": {
    "zendesk": "configured",
    "intercom": "configured",
    "mixpanel": "configured",
    "sendgrid": "configured"
  }
}
```

### Step 2: Run System Tests

```bash
# Run the test suite
docker-compose exec cs-mcp pytest tests/ -v

# Run specific test categories
docker-compose exec cs-mcp pytest tests/test_core_system_tools.py -v
docker-compose exec cs-mcp pytest tests/test_integrations/ -v
```

### Step 3: Test Core Functionality

```bash
# Register a test customer
curl -X POST http://localhost:8080/tools/register_client \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Company",
    "contact_email": "test@example.com",
    "subscription_tier": "professional"
  }'

# Calculate health score
curl -X POST http://localhost:8080/tools/calculate_health_score \
  -H "Content-Type: application/json" \
  -d '{"client_id": "test-client-id"}'
```

## Troubleshooting

### Common Installation Issues

#### Issue: Python Version Error
**Error:** `Python 3.10+ is required`
**Solution:**
```bash
# Check Python version
python3 --version

# Install Python 3.11 if needed
# Ubuntu/Debian
sudo apt-get install python3.11

# macOS
brew install python@3.11
```

#### Issue: Database Connection Failed
**Error:** `psycopg2.OperationalError: could not connect to server`
**Solution:**
```bash
# Check PostgreSQL is running
systemctl status postgresql  # Linux
brew services list  # macOS

# Check connection parameters
psql -U csuser -h localhost -d customerdb

# Verify DATABASE_URL format
echo $DATABASE_URL
```

#### Issue: Redis Connection Error
**Error:** `redis.exceptions.ConnectionError`
**Solution:**
```bash
# Check Redis is running
redis-cli ping

# Check Redis configuration
redis-cli CONFIG GET bind
redis-cli CONFIG GET protected-mode

# Update REDIS_URL if needed
export REDIS_URL=redis://localhost:6379/0
```

#### Issue: Docker Build Fails
**Error:** `docker-compose build` fails
**Solution:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild with no cache
docker-compose build --no-cache

# Check Docker disk space
docker system df
```

#### Issue: Port Already in Use
**Error:** `bind: address already in use`
**Solution:**
```bash
# Find process using port 8080
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Kill the process or change port in .env
MCP_PORT=8081
```

#### Issue: Migration Fails
**Error:** `alembic.util.exc.CommandError`
**Solution:**
```bash
# Reset database (CAUTION: deletes all data)
docker-compose exec postgres psql -U csuser -d customerdb -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Re-run migrations
docker-compose exec cs-mcp alembic upgrade head
```

## Uninstallation

### Docker Installation

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (CAUTION: deletes data)
docker-compose down -v

# Remove Docker image
docker rmi cs-mcp:latest
```

### Local Installation

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv/

# Drop database (optional)
sudo -u postgres psql -c "DROP DATABASE customerdb;"
sudo -u postgres psql -c "DROP USER csuser;"

# Remove repository
cd ..
rm -rf 199os-customer-success-mcp/
```

## Support

### Documentation

- [Quick Start Guide](QUICK_START.md)
- [Configuration Reference](CONFIGURATION.md)
- [API Documentation](docs/api/TOOL_REFERENCE.md)
- [Troubleshooting Guide](docs/operations/TROUBLESHOOTING.md)

### Getting Help

- **GitHub Issues**: https://github.com/yourusername/199os-customer-success-mcp/issues
- **Documentation**: https://docs.customer-success-mcp.com
- **Community Discord**: https://discord.gg/cs-mcp
- **Email Support**: support@customer-success-mcp.com

### Version Information

To check your installed version:

```bash
# Docker installation
docker-compose exec cs-mcp python -c "from src import __version__; print(__version__)"

# Local installation
python -c "from src import __version__; print(__version__)"
```

---

**Last Updated**: October 2025
**Version**: 1.0.0
**License**: MIT