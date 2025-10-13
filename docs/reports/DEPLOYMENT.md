# Deployment Guide - 199OS Customer Success MCP Server

**Complete Production Deployment Guide**

This comprehensive guide covers all aspects of deploying the 199OS Customer Success MCP Server in production environments, from prerequisites through monitoring and scaling.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Methods](#deployment-methods)
3. [Configuration](#configuration)
4. [External Integrations Setup](#external-integrations-setup)
5. [Database Setup](#database-setup)
6. [Production Checklist](#production-checklist)
7. [Monitoring & Logging](#monitoring--logging)
8. [Troubleshooting](#troubleshooting)
9. [Rollback Procedures](#rollback-procedures)
10. [Scaling Recommendations](#scaling-recommendations)

---

## Prerequisites

### System Requirements

**Minimum Production Requirements:**
- **CPU:** 4 cores (8 cores recommended for high-volume deployments)
- **RAM:** 8GB minimum (16GB recommended)
- **Disk:** 50GB SSD minimum (100GB+ for long-term data retention)
- **Network:** 100 Mbps minimum bandwidth

**Operating System:**
- Ubuntu 20.04+ LTS (recommended)
- CentOS 8+ / Rocky Linux 8+
- macOS 12+ (development only)
- Windows Server 2019+ with WSL2 (development only)

### Software Dependencies

**Required:**
- **Python:** 3.10, 3.11, or 3.12
- **PostgreSQL:** 14+ (15+ recommended for performance)
- **Redis:** 7+ (for caching and session management)
- **Docker:** 24+ and Docker Compose 2.20+ (for containerized deployment)
- **Git:** 2.30+ (for version control)

**Optional:**
- **Nginx:** 1.22+ (reverse proxy and load balancing)
- **Kubernetes:** 1.27+ (for container orchestration)
- **Prometheus:** 2.40+ (metrics collection)
- **Grafana:** 9.0+ (metrics visualization)

### Required Credentials

Before deployment, obtain API credentials for the following services:

**Critical Integrations:**
1. **Zendesk** (Support Platform)
   - Subdomain (e.g., `your-company.zendesk.com`)
   - Email address for API access
   - API token

2. **Intercom** (Customer Messaging)
   - Access token
   - App ID

3. **Mixpanel** (Product Analytics)
   - Project token
   - API secret

4. **SendGrid** (Email Delivery)
   - API key
   - Verified sender email address
   - Verified sender domain (for production)

**Optional Integrations:**
- Gainsight (CS Platform)
- Amplitude (Product Analytics)
- Salesforce (CRM)
- HubSpot (CRM)

### Network Requirements

**Inbound Ports:**
- `8080` - MCP Server HTTP (default, configurable)
- `443` - HTTPS (if using SSL termination)
- `22` - SSH (for server management)

**Outbound Ports:**
- `443` - HTTPS (for API integrations)
- `5432` - PostgreSQL (if using external database)
- `6379` - Redis (if using external cache)

**Firewall Rules:**
- Allow outbound HTTPS to integration platforms
- Restrict inbound access to known IP ranges
- Enable security groups for cloud deployments

---

## Deployment Methods

### Method 1: Docker Deployment (Recommended)

Docker deployment provides isolation, consistency, and easy rollback capabilities.

#### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/199os/customer-success-mcp.git
cd customer-success-mcp

# Checkout latest stable release
git checkout v1.0.0  # Replace with latest version
```

#### Step 2: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration with your values
nano .env  # or vim, vi, emacs
```

**Required Variables (see Configuration section for details):**
```bash
# Database
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@postgres:5432/cs_mcp_db

# Redis
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=YOUR_REDIS_PASSWORD

# Security
MASTER_PASSWORD=YOUR_MASTER_PASSWORD
ENCRYPTION_KEY=YOUR_ENCRYPTION_KEY
JWT_SECRET=YOUR_JWT_SECRET

# Integrations
ZENDESK_SUBDOMAIN=your-subdomain
ZENDESK_EMAIL=your-email@company.com
ZENDESK_API_TOKEN=YOUR_ZENDESK_TOKEN

INTERCOM_ACCESS_TOKEN=YOUR_INTERCOM_TOKEN
INTERCOM_APP_ID=YOUR_INTERCOM_APP_ID

MIXPANEL_PROJECT_TOKEN=YOUR_MIXPANEL_TOKEN
MIXPANEL_API_SECRET=YOUR_MIXPANEL_SECRET

SENDGRID_API_KEY=YOUR_SENDGRID_KEY
SENDGRID_FROM_EMAIL=noreply@yourcompany.com
```

#### Step 3: Build and Start Containers

```bash
# Build the Docker image
docker-compose build

# Start all services (MCP server, PostgreSQL, Redis)
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f mcp-server
```

#### Step 4: Initialize Database

```bash
# Run database migrations
docker-compose exec mcp-server python -m alembic upgrade head

# Verify database schema
docker-compose exec postgres psql -U postgres -d cs_mcp_db -c "\dt"
```

#### Step 5: Verify Deployment

```bash
# Check server health
curl http://localhost:8080/health

# Expected response:
# {"status": "healthy", "version": "1.0.0", "uptime": "0:05:23"}

# Test tool availability (should list 54 tools)
curl http://localhost:8080/tools | jq '.tools | length'
```

#### Docker Compose Configuration

**Production docker-compose.yml:**
```yaml
version: '3.8'

services:
  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: cs-mcp-server
    restart: unless-stopped
    ports:
      - "8080:8080"
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@postgres:5432/cs_mcp_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - cs-network
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"

  postgres:
    image: postgres:15-alpine
    container_name: cs-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=cs_mcp_db
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=C --lc-ctype=C
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - cs-network
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    container_name: cs-redis
    restart: unless-stopped
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 2gb
      --maxmemory-policy allkeys-lru
      --appendonly yes
      --appendfsync everysec
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - cs-network
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"

  nginx:
    image: nginx:1.25-alpine
    container_name: cs-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - mcp-server
    networks:
      - cs-network
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"

volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local

networks:
  cs-network:
    driver: bridge
```

---

### Method 2: Local Development Deployment

For local development and testing environments.

#### Step 1: System Preparation

```bash
# Install Python (if not installed)
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# macOS (using Homebrew)
brew install python@3.11

# Verify installation
python3.11 --version
```

#### Step 2: Install PostgreSQL

**Ubuntu/Debian:**
```bash
# Install PostgreSQL
sudo apt install postgresql-15 postgresql-contrib-15

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE cs_mcp_db;"
sudo -u postgres psql -c "CREATE USER cs_user WITH ENCRYPTED PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE cs_mcp_db TO cs_user;"
```

**macOS:**
```bash
# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL
brew services start postgresql@15

# Create database
createdb cs_mcp_db
```

#### Step 3: Install Redis

**Ubuntu/Debian:**
```bash
# Install Redis
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set: requirepass your_redis_password

# Restart Redis
sudo systemctl restart redis
sudo systemctl enable redis
```

**macOS:**
```bash
# Install Redis
brew install redis

# Start Redis
brew services start redis

# Set password (optional for development)
redis-cli CONFIG SET requirepass "your_password"
```

#### Step 4: Clone and Setup Project

```bash
# Clone repository
git clone https://github.com/199os/customer-success-mcp.git
cd customer-success-mcp

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

#### Step 5: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env

# Update database URL for local PostgreSQL
DATABASE_URL=postgresql://cs_user:your_password@localhost:5432/cs_mcp_db

# Update Redis URL
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password
```

#### Step 6: Initialize Database

```bash
# Run migrations
alembic upgrade head

# Verify database
psql -U cs_user -d cs_mcp_db -c "\dt"

# Load initial data (optional)
python scripts/load_sample_data.py
```

#### Step 7: Start Server

```bash
# Start in development mode
python server.py

# Or start with debug logging
LOG_LEVEL=DEBUG python server.py

# Or start in background
nohup python server.py > logs/server.log 2>&1 &
```

#### Step 8: Verify Deployment

```bash
# Check server health
curl http://localhost:8080/health

# Check available tools
curl http://localhost:8080/tools | jq '.tools[] | .name'

# Test a simple tool
curl -X POST http://localhost:8080/tools/register_client \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Test Company",
    "company_name": "Test Company Inc.",
    "industry": "Technology",
    "tier": "standard"
  }' | jq
```

---

### Method 3: AWS Production Deployment

Deploy to Amazon Web Services for production-grade infrastructure.

#### Architecture Overview

```
AWS Production Architecture
├── Route 53 (DNS)
├── CloudFront (CDN)
├── Application Load Balancer (ALB)
├── ECS Fargate (Container Orchestration)
│   ├── MCP Server (multiple tasks)
│   └── Auto Scaling
├── RDS PostgreSQL (Multi-AZ)
├── ElastiCache Redis (Cluster Mode)
├── S3 (Logs and Backups)
├── CloudWatch (Monitoring)
├── Secrets Manager (Credentials)
└── VPC (Network Isolation)
```

#### Prerequisites

```bash
# Install AWS CLI
# macOS
brew install awscli

# Ubuntu/Debian
sudo apt install awscli

# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region, Output format
```

#### Step 1: Create VPC and Networking

```bash
# Create VPC
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=cs-mcp-vpc}]'

# Create public subnets (2 for HA)
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=cs-mcp-public-1a}]'

aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=cs-mcp-public-1b}]'

# Create private subnets (2 for HA)
aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.10.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=cs-mcp-private-1a}]'

aws ec2 create-subnet \
  --vpc-id vpc-xxxxx \
  --cidr-block 10.0.11.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=cs-mcp-private-1b}]'

# Create Internet Gateway
aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=cs-mcp-igw}]'

# Attach IGW to VPC
aws ec2 attach-internet-gateway \
  --vpc-id vpc-xxxxx \
  --internet-gateway-id igw-xxxxx

# Create NAT Gateway
aws ec2 allocate-address --domain vpc
aws ec2 create-nat-gateway \
  --subnet-id subnet-xxxxx \
  --allocation-id eipalloc-xxxxx
```

#### Step 2: Deploy RDS PostgreSQL

```bash
# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name cs-mcp-db-subnet \
  --db-subnet-group-description "CS MCP Database Subnet Group" \
  --subnet-ids subnet-xxxxx subnet-yyyyy

# Create security group for RDS
aws ec2 create-security-group \
  --group-name cs-mcp-db-sg \
  --description "Security group for CS MCP database" \
  --vpc-id vpc-xxxxx

# Create RDS instance
aws rds create-db-instance \
  --db-instance-identifier cs-mcp-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.4 \
  --master-username admin \
  --master-user-password YOUR_SECURE_PASSWORD \
  --allocated-storage 100 \
  --storage-type gp3 \
  --storage-encrypted \
  --multi-az \
  --db-subnet-group-name cs-mcp-db-subnet \
  --vpc-security-group-ids sg-xxxxx \
  --backup-retention-period 7 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "sun:04:00-sun:05:00" \
  --enable-cloudwatch-logs-exports '["postgresql"]' \
  --deletion-protection

# Wait for RDS to be available
aws rds wait db-instance-available --db-instance-identifier cs-mcp-db

# Get endpoint
aws rds describe-db-instances \
  --db-instance-identifier cs-mcp-db \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text
```

#### Step 3: Deploy ElastiCache Redis

```bash
# Create cache subnet group
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name cs-mcp-cache-subnet \
  --cache-subnet-group-description "CS MCP Cache Subnet Group" \
  --subnet-ids subnet-xxxxx subnet-yyyyy

# Create security group for ElastiCache
aws ec2 create-security-group \
  --group-name cs-mcp-cache-sg \
  --description "Security group for CS MCP cache" \
  --vpc-id vpc-xxxxx

# Create Redis cluster
aws elasticache create-replication-group \
  --replication-group-id cs-mcp-redis \
  --replication-group-description "CS MCP Redis Cluster" \
  --engine redis \
  --engine-version 7.0 \
  --cache-node-type cache.t3.medium \
  --num-cache-clusters 2 \
  --automatic-failover-enabled \
  --cache-subnet-group-name cs-mcp-cache-subnet \
  --security-group-ids sg-xxxxx \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --auth-token YOUR_REDIS_AUTH_TOKEN

# Wait for cluster to be available
aws elasticache wait replication-group-available \
  --replication-group-id cs-mcp-redis

# Get endpoint
aws elasticache describe-replication-groups \
  --replication-group-id cs-mcp-redis \
  --query 'ReplicationGroups[0].NodeGroups[0].PrimaryEndpoint.Address' \
  --output text
```

#### Step 4: Store Secrets in AWS Secrets Manager

```bash
# Create secrets
aws secretsmanager create-secret \
  --name cs-mcp/database \
  --description "CS MCP Database Credentials" \
  --secret-string '{
    "username": "admin",
    "password": "YOUR_DB_PASSWORD",
    "host": "cs-mcp-db.xxxxx.us-east-1.rds.amazonaws.com",
    "port": 5432,
    "dbname": "cs_mcp_db"
  }'

aws secretsmanager create-secret \
  --name cs-mcp/redis \
  --description "CS MCP Redis Credentials" \
  --secret-string '{
    "host": "cs-mcp-redis.xxxxx.cache.amazonaws.com",
    "port": 6379,
    "password": "YOUR_REDIS_PASSWORD"
  }'

aws secretsmanager create-secret \
  --name cs-mcp/integrations \
  --description "CS MCP Integration API Keys" \
  --secret-string '{
    "zendesk_subdomain": "your-subdomain",
    "zendesk_email": "your-email@company.com",
    "zendesk_api_token": "YOUR_ZENDESK_TOKEN",
    "intercom_access_token": "YOUR_INTERCOM_TOKEN",
    "intercom_app_id": "YOUR_APP_ID",
    "mixpanel_project_token": "YOUR_MIXPANEL_TOKEN",
    "mixpanel_api_secret": "YOUR_MIXPANEL_SECRET",
    "sendgrid_api_key": "YOUR_SENDGRID_KEY"
  }'
```

#### Step 5: Create ECS Cluster and Task Definition

```bash
# Create ECS cluster
aws ecs create-cluster \
  --cluster-name cs-mcp-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy \
    capacityProvider=FARGATE,weight=1 \
    capacityProvider=FARGATE_SPOT,weight=1

# Create task execution role
aws iam create-role \
  --role-name ecsTaskExecutionRole \
  --assume-role-policy-document file://task-execution-assume-role.json

aws iam attach-role-policy \
  --role-name ecsTaskExecutionRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

# Create CloudWatch log group
aws logs create-log-group --log-group-name /ecs/cs-mcp-server

# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

**task-definition.json:**
```json
{
  "family": "cs-mcp-server",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT_ID:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "cs-mcp-server",
      "image": "199os/customer-success-mcp:latest",
      "essential": true,
      "portMappings": [
        {
          "containerPort": 8080,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "SERVER_PORT",
          "value": "8080"
        },
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:cs-mcp/database"
        },
        {
          "name": "REDIS_URL",
          "valueFrom": "arn:aws:secretsmanager:REGION:ACCOUNT_ID:secret:cs-mcp/redis"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/cs-mcp-server",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### Step 6: Create Application Load Balancer

```bash
# Create security group for ALB
aws ec2 create-security-group \
  --group-name cs-mcp-alb-sg \
  --description "Security group for CS MCP ALB" \
  --vpc-id vpc-xxxxx

# Allow HTTP/HTTPS traffic
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol tcp \
  --port 443 \
  --cidr 0.0.0.0/0

# Create ALB
aws elbv2 create-load-balancer \
  --name cs-mcp-alb \
  --subnets subnet-xxxxx subnet-yyyyy \
  --security-groups sg-xxxxx \
  --scheme internet-facing \
  --type application \
  --ip-address-type ipv4

# Create target group
aws elbv2 create-target-group \
  --name cs-mcp-tg \
  --protocol HTTP \
  --port 8080 \
  --vpc-id vpc-xxxxx \
  --target-type ip \
  --health-check-enabled \
  --health-check-protocol HTTP \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:REGION:ACCOUNT_ID:loadbalancer/app/cs-mcp-alb/xxxxx \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:REGION:ACCOUNT_ID:targetgroup/cs-mcp-tg/xxxxx
```

#### Step 7: Create ECS Service with Auto Scaling

```bash
# Create ECS service
aws ecs create-service \
  --cluster cs-mcp-cluster \
  --service-name cs-mcp-service \
  --task-definition cs-mcp-server:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --platform-version LATEST \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxxxx,subnet-yyyyy],securityGroups=[sg-xxxxx],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:REGION:ACCOUNT_ID:targetgroup/cs-mcp-tg/xxxxx,containerName=cs-mcp-server,containerPort=8080" \
  --health-check-grace-period-seconds 60 \
  --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100"

# Configure auto scaling
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/cs-mcp-cluster/cs-mcp-service \
  --min-capacity 2 \
  --max-capacity 10

# Create scaling policy for CPU
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/cs-mcp-cluster/cs-mcp-service \
  --policy-name cpu-scale-out \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 300
  }'

# Create scaling policy for memory
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/cs-mcp-cluster/cs-mcp-service \
  --policy-name memory-scale-out \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 80.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageMemoryUtilization"
    },
    "ScaleOutCooldown": 60,
    "ScaleInCooldown": 300
  }'
```

#### Step 8: Configure CloudWatch Monitoring

```bash
# Create CloudWatch dashboard
aws cloudwatch put-dashboard \
  --dashboard-name CS-MCP-Production \
  --dashboard-body file://cloudwatch-dashboard.json

# Create alarms
aws cloudwatch put-metric-alarm \
  --alarm-name cs-mcp-high-cpu \
  --alarm-description "Alert when CPU exceeds 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=ServiceName,Value=cs-mcp-service Name=ClusterName,Value=cs-mcp-cluster

aws cloudwatch put-metric-alarm \
  --alarm-name cs-mcp-high-memory \
  --alarm-description "Alert when memory exceeds 85%" \
  --metric-name MemoryUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 85 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --dimensions Name=ServiceName,Value=cs-mcp-service Name=ClusterName,Value=cs-mcp-cluster

aws cloudwatch put-metric-alarm \
  --alarm-name cs-mcp-unhealthy-targets \
  --alarm-description "Alert when unhealthy targets detected" \
  --metric-name UnHealthyHostCount \
  --namespace AWS/ApplicationELB \
  --statistic Average \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 2
```

---

### Method 4: GCP Production Deployment

Deploy to Google Cloud Platform for production-grade infrastructure.

#### Prerequisites

```bash
# Install gcloud CLI
# macOS
brew install google-cloud-sdk

# Ubuntu/Debian
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
sudo apt update && sudo apt install google-cloud-sdk

# Initialize gcloud
gcloud init
gcloud auth login
```

#### Step 1: Create GKE Cluster

```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable redis.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Create GKE cluster
gcloud container clusters create cs-mcp-cluster \
  --region us-central1 \
  --node-locations us-central1-a,us-central1-b,us-central1-c \
  --machine-type n2-standard-4 \
  --num-nodes 1 \
  --min-nodes 1 \
  --max-nodes 10 \
  --enable-autoscaling \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-stackdriver-kubernetes \
  --enable-ip-alias \
  --enable-shielded-nodes \
  --shielded-secure-boot \
  --shielded-integrity-monitoring \
  --workload-pool=YOUR_PROJECT_ID.svc.id.goog

# Get cluster credentials
gcloud container clusters get-credentials cs-mcp-cluster --region us-central1
```

#### Step 2: Create Cloud SQL PostgreSQL

```bash
# Create Cloud SQL instance
gcloud sql instances create cs-mcp-db \
  --database-version=POSTGRES_15 \
  --tier=db-custom-4-16384 \
  --region=us-central1 \
  --network=default \
  --availability-type=regional \
  --backup-start-time=03:00 \
  --enable-bin-log \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=4 \
  --storage-size=100GB \
  --storage-type=SSD \
  --storage-auto-increase \
  --storage-auto-increase-limit=500 \
  --database-flags=max_connections=200,shared_buffers=256MB

# Create database
gcloud sql databases create cs_mcp_db --instance=cs-mcp-db

# Create user
gcloud sql users create cs_user \
  --instance=cs-mcp-db \
  --password=YOUR_SECURE_PASSWORD

# Get connection name
gcloud sql instances describe cs-mcp-db \
  --format='value(connectionName)'
```

#### Step 3: Create Memorystore Redis

```bash
# Create Redis instance
gcloud redis instances create cs-mcp-redis \
  --size=5 \
  --region=us-central1 \
  --tier=standard \
  --redis-version=redis_7_0 \
  --auth-enabled \
  --transit-encryption-mode=SERVER_AUTHENTICATION

# Get host and auth string
gcloud redis instances describe cs-mcp-redis \
  --region=us-central1 \
  --format='value(host)'

gcloud redis instances get-auth-string cs-mcp-redis \
  --region=us-central1
```

#### Step 4: Store Secrets in Secret Manager

```bash
# Create secrets
echo -n "postgresql://cs_user:YOUR_PASSWORD@/cs_mcp_db?host=/cloudsql/YOUR_PROJECT:us-central1:cs-mcp-db" | \
  gcloud secrets create database-url --data-file=-

echo -n "redis://cs-mcp-redis-host:6379?password=YOUR_REDIS_PASSWORD" | \
  gcloud secrets create redis-url --data-file=-

echo -n "YOUR_ZENDESK_TOKEN" | \
  gcloud secrets create zendesk-api-token --data-file=-

echo -n "YOUR_INTERCOM_TOKEN" | \
  gcloud secrets create intercom-access-token --data-file=-

echo -n "YOUR_MIXPANEL_TOKEN" | \
  gcloud secrets create mixpanel-project-token --data-file=-

echo -n "YOUR_SENDGRID_KEY" | \
  gcloud secrets create sendgrid-api-key --data-file=-

# Grant access to GKE service account
gcloud secrets add-iam-policy-binding database-url \
  --member="serviceAccount:YOUR_PROJECT_ID.svc.id.goog[default/cs-mcp-sa]" \
  --role="roles/secretmanager.secretAccessor"
```

#### Step 5: Deploy to GKE

**kubernetes-deployment.yaml:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cs-mcp
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cs-mcp-sa
  namespace: cs-mcp
  annotations:
    iam.gke.io/gcp-service-account: cs-mcp-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cs-mcp-server
  namespace: cs-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cs-mcp-server
  template:
    metadata:
      labels:
        app: cs-mcp-server
    spec:
      serviceAccountName: cs-mcp-sa
      containers:
      - name: cs-mcp-server
        image: gcr.io/YOUR_PROJECT_ID/cs-mcp-server:latest
        ports:
        - containerPort: 8080
        env:
        - name: SERVER_PORT
          value: "8080"
        - name: LOG_LEVEL
          value: "INFO"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-url
              key: latest
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-url
              key: latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
      - name: cloud-sql-proxy
        image: gcr.io/cloudsql-docker/gce-proxy:latest
        command:
          - "/cloud_sql_proxy"
          - "-instances=YOUR_PROJECT:us-central1:cs-mcp-db=tcp:5432"
        securityContext:
          runAsNonRoot: true
---
apiVersion: v1
kind: Service
metadata:
  name: cs-mcp-service
  namespace: cs-mcp
spec:
  type: LoadBalancer
  selector:
    app: cs-mcp-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cs-mcp-hpa
  namespace: cs-mcp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cs-mcp-server
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Deploy:**
```bash
# Build and push Docker image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/cs-mcp-server:latest

# Apply Kubernetes manifests
kubectl apply -f kubernetes-deployment.yaml

# Verify deployment
kubectl get pods -n cs-mcp
kubectl get svc -n cs-mcp

# Get external IP
kubectl get svc cs-mcp-service -n cs-mcp -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

---

### Method 5: Azure Production Deployment

Deploy to Microsoft Azure for production-grade infrastructure.

#### Prerequisites

```bash
# Install Azure CLI
# macOS
brew install azure-cli

# Ubuntu/Debian
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login
```

#### Step 1: Create Resource Group

```bash
# Create resource group
az group create \
  --name cs-mcp-rg \
  --location eastus

# Set default resource group
az configure --defaults group=cs-mcp-rg location=eastus
```

#### Step 2: Create Azure Database for PostgreSQL

```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --name cs-mcp-db \
  --resource-group cs-mcp-rg \
  --location eastus \
  --admin-user csadmin \
  --admin-password YOUR_SECURE_PASSWORD \
  --sku-name Standard_D4s_v3 \
  --tier GeneralPurpose \
  --version 15 \
  --storage-size 128 \
  --backup-retention 7 \
  --high-availability Enabled \
  --zone 1

# Create database
az postgres flexible-server db create \
  --resource-group cs-mcp-rg \
  --server-name cs-mcp-db \
  --database-name cs_mcp_db

# Configure firewall (allow Azure services)
az postgres flexible-server firewall-rule create \
  --resource-group cs-mcp-rg \
  --name cs-mcp-db \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

#### Step 3: Create Azure Cache for Redis

```bash
# Create Redis cache
az redis create \
  --name cs-mcp-redis \
  --resource-group cs-mcp-rg \
  --location eastus \
  --sku Standard \
  --vm-size c1 \
  --enable-non-ssl-port false \
  --redis-version 6

# Get access keys
az redis list-keys \
  --name cs-mcp-redis \
  --resource-group cs-mcp-rg
```

#### Step 4: Create Container Registry

```bash
# Create ACR
az acr create \
  --name csmcpregistry \
  --resource-group cs-mcp-rg \
  --sku Standard \
  --admin-enabled true

# Login to ACR
az acr login --name csmcpregistry

# Build and push image
docker build -t csmcpregistry.azurecr.io/cs-mcp-server:latest .
docker push csmcpregistry.azurecr.io/cs-mcp-server:latest
```

#### Step 5: Create Azure Container Instances

```bash
# Create container instance
az container create \
  --name cs-mcp-server \
  --resource-group cs-mcp-rg \
  --image csmcpregistry.azurecr.io/cs-mcp-server:latest \
  --cpu 2 \
  --memory 4 \
  --registry-login-server csmcpregistry.azurecr.io \
  --registry-username $(az acr credential show --name csmcpregistry --query username -o tsv) \
  --registry-password $(az acr credential show --name csmcpregistry --query passwords[0].value -o tsv) \
  --dns-name-label cs-mcp-server \
  --ports 8080 \
  --environment-variables \
    SERVER_PORT=8080 \
    LOG_LEVEL=INFO \
  --secure-environment-variables \
    DATABASE_URL=postgresql://csadmin:YOUR_PASSWORD@cs-mcp-db.postgres.database.azure.com:5432/cs_mcp_db \
    REDIS_URL=rediss://:YOUR_REDIS_KEY@cs-mcp-redis.redis.cache.windows.net:6380

# Get public IP
az container show \
  --name cs-mcp-server \
  --resource-group cs-mcp-rg \
  --query ipAddress.fqdn \
  --output tsv
```

---

## Configuration

### Complete Environment Variables Reference

The CS MCP Server uses environment variables for all configuration. Below is a complete reference of all 60+ variables.

#### Server Configuration

```bash
# Server Identity and Network
SERVER_NAME=199OS-CustomerSuccess
# The display name for the MCP server
SERVER_PORT=8080
# Port the server listens on (default: 8080)

# Logging
LOG_LEVEL=INFO
# Logging verbosity: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json
# Log output format: json (recommended for production), text
LOG_FILE=/app/logs/server.log
# Path to log file (optional, logs to stdout if not set)
LOG_ROTATION=true
# Enable daily log rotation
LOG_RETENTION_DAYS=30
# Number of days to keep logs
```

#### Database Configuration (PostgreSQL)

```bash
# Connection String
DATABASE_URL=postgresql://user:password@host:port/database
# Full PostgreSQL connection URL
# Examples:
#   - Local: postgresql://postgres:password@localhost:5432/cs_mcp_db
#   - Docker: postgresql://postgres:password@postgres:5432/cs_mcp_db
#   - AWS RDS: postgresql://admin:password@cs-mcp-db.xxxxx.us-east-1.rds.amazonaws.com:5432/cs_mcp_db
#   - Cloud SQL: postgresql://user:password@/cs_mcp_db?host=/cloudsql/PROJECT:REGION:INSTANCE

# Connection Pool Settings
DB_POOL_SIZE=20
# Number of connections in the pool (recommend: 20-50 for production)
DB_MAX_OVERFLOW=10
# Maximum connections beyond pool_size
DB_POOL_TIMEOUT=30
# Seconds to wait for a connection from the pool
DB_POOL_RECYCLE=3600
# Seconds before recycling connections (prevents stale connections)
DB_ECHO=false
# Log all SQL statements (true for debugging, false for production)

# SSL Configuration
DB_SSL_MODE=require
# SSL mode: disable, allow, prefer, require, verify-ca, verify-full
DB_SSL_CERT=/path/to/client-cert.pem
# Path to client SSL certificate (optional)
DB_SSL_KEY=/path/to/client-key.pem
# Path to client SSL key (optional)
DB_SSL_ROOT_CERT=/path/to/ca-cert.pem
# Path to CA certificate (optional)
```

#### Redis Configuration

```bash
# Connection
REDIS_URL=redis://localhost:6379/0
# Redis connection URL
# Formats:
#   - Local: redis://localhost:6379/0
#   - With password: redis://:password@localhost:6379/0
#   - TLS: rediss://:password@host:6380/0
#   - AWS ElastiCache: redis://cs-mcp-redis.xxxxx.cache.amazonaws.com:6379
REDIS_PASSWORD=your-redis-password
# Redis authentication password

# Connection Pool
REDIS_MAX_CONNECTIONS=50
# Maximum number of connections in the pool
REDIS_SOCKET_TIMEOUT=5
# Socket timeout in seconds
REDIS_SOCKET_CONNECT_TIMEOUT=5
# Socket connection timeout in seconds
REDIS_SOCKET_KEEPALIVE=true
# Enable TCP keepalive
REDIS_HEALTH_CHECK_INTERVAL=30
# Seconds between health checks

# Caching Configuration
CACHE_DEFAULT_TTL=3600
# Default cache TTL in seconds (1 hour)
CACHE_LONG_TTL=86400
# Long cache TTL in seconds (24 hours)
CACHE_SHORT_TTL=300
# Short cache TTL in seconds (5 minutes)
CACHE_ENABLED=true
# Enable/disable caching globally
```

#### Rate Limiting

```bash
# Global Rate Limits
MAX_REQUESTS_PER_MINUTE=1000
# Maximum requests per minute across all clients
MAX_REQUESTS_PER_HOUR=10000
# Maximum requests per hour across all clients

# Per-Client Rate Limits
RATE_LIMIT_PER_CLIENT_PER_MINUTE=100
# Maximum requests per client per minute
RATE_LIMIT_PER_CLIENT_PER_HOUR=1000
# Maximum requests per client per hour

# Rate Limit Storage
RATE_LIMIT_STORAGE=redis
# Where to store rate limit data: redis (recommended), memory
```

#### Security Configuration

```bash
# Encryption Keys (CRITICAL - Generate unique values for production)
MASTER_PASSWORD=your-strong-master-password-here
# Master password for encrypting stored credentials
# Generate with: openssl rand -base64 32

ENCRYPTION_KEY=your-encryption-key-here
# Encryption key for sensitive data (AES-256)
# Generate with: openssl rand -hex 32

JWT_SECRET=your-jwt-secret-here
# Secret for JWT token generation
# Generate with: openssl rand -base64 64

# API Authentication
MCP_API_KEY=your-mcp-api-key-here
# API key for authenticating MCP requests
REQUIRE_API_KEY=true
# Enforce API key authentication

# Webhook Security
WEBHOOK_SECRET=your-webhook-secret
# Secret for verifying incoming webhooks (HMAC signatures)

# Session Configuration
SESSION_SECRET=your-session-secret
# Secret for session management
SESSION_TIMEOUT=3600
# Session timeout in seconds (1 hour)

# CORS Configuration
CORS_ENABLED=true
# Enable CORS headers
CORS_ORIGINS=https://yourapp.com,https://app.yourcompany.com
# Allowed CORS origins (comma-separated)
CORS_ALLOW_CREDENTIALS=true
# Allow credentials in CORS requests
```

#### Learning System Configuration

```bash
# Learning Behavior
LEARNING_COMPLETION_THRESHOLD=0.70
# Confidence threshold for learning questions (0.0 - 1.0)
# Higher values = ask more questions, lower values = ask fewer

LEARNING_FREQUENCY=often
# How often to ask learning questions: always, often, occasionally, rarely

LEARNING_ENABLED=true
# Enable/disable adaptive learning system

# Preference Storage
PREFERENCES_DIR=./config/preferences
# Directory for storing learned preferences
PREFERENCES_BACKUP=true
# Enable automatic backup of preferences
```

#### Zendesk Integration (Support Platform)

```bash
ZENDESK_SUBDOMAIN=your-subdomain
# Your Zendesk subdomain (e.g., company.zendesk.com → "company")

ZENDESK_EMAIL=your-email@company.com
# Email address for Zendesk API authentication

ZENDESK_API_TOKEN=your-zendesk-api-token
# Zendesk API token
# Generate at: Admin > Channels > API > Add API Token

ZENDESK_ENABLED=true
# Enable/disable Zendesk integration

# Rate Limiting
ZENDESK_MAX_RETRIES=3
# Maximum retry attempts for failed requests
ZENDESK_RETRY_DELAY=1
# Initial retry delay in seconds (exponential backoff)
ZENDESK_TIMEOUT=30
# Request timeout in seconds

# Circuit Breaker
ZENDESK_CIRCUIT_BREAKER_THRESHOLD=5
# Number of failures before opening circuit
ZENDESK_CIRCUIT_BREAKER_TIMEOUT=60
# Seconds to wait before retrying after circuit opens
```

#### Intercom Integration (Customer Messaging)

```bash
INTERCOM_ACCESS_TOKEN=your-intercom-access-token
# Intercom access token
# Generate at: Settings > Developers > Developer Hub > Access Tokens

INTERCOM_APP_ID=your-intercom-app-id
# Intercom application ID
# Find at: Settings > Installation > Web

INTERCOM_ENABLED=true
# Enable/disable Intercom integration

# Configuration
INTERCOM_MAX_RETRIES=3
# Maximum retry attempts
INTERCOM_RETRY_DELAY=1
# Initial retry delay in seconds
INTERCOM_TIMEOUT=30
# Request timeout in seconds
INTERCOM_API_VERSION=2.10
# Intercom API version
```

#### Mixpanel Integration (Product Analytics)

```bash
MIXPANEL_PROJECT_TOKEN=your-mixpanel-project-token
# Mixpanel project token
# Find at: Project Settings > Project Token

MIXPANEL_API_SECRET=your-mixpanel-api-secret
# Mixpanel API secret for query API
# Find at: Project Settings > API Secret

MIXPANEL_ENABLED=true
# Enable/disable Mixpanel integration

# Batch Processing
MIXPANEL_BATCH_SIZE=50
# Number of events to send in a single batch
MIXPANEL_BATCH_TIMEOUT=5
# Seconds to wait before sending partial batch

# Configuration
MIXPANEL_MAX_RETRIES=3
# Maximum retry attempts
MIXPANEL_RETRY_DELAY=1
# Initial retry delay in seconds
```

#### SendGrid Integration (Email Delivery)

```bash
SENDGRID_API_KEY=your-sendgrid-api-key
# SendGrid API key
# Generate at: Settings > API Keys > Create API Key

SENDGRID_FROM_EMAIL=noreply@yourcompany.com
# Sender email address (must be verified)

SENDGRID_FROM_NAME=Your Company
# Sender name displayed in emails

SENDGRID_ENABLED=true
# Enable/disable SendGrid integration

# Configuration
SENDGRID_MAX_RETRIES=3
# Maximum retry attempts
SENDGRID_RETRY_DELAY=1
# Initial retry delay in seconds
SENDGRID_TIMEOUT=30
# Request timeout in seconds

# Batch Processing
SENDGRID_BATCH_SIZE=1000
# Maximum emails per batch
SENDGRID_BATCH_DELAY=0.1
# Delay between batches in seconds

# Templates
SENDGRID_TEMPLATE_DIR=./templates/sendgrid
# Directory for email templates
```

#### Optional Integrations

```bash
# Gainsight (CS Platform)
GAINSIGHT_API_KEY=your-gainsight-api-key
GAINSIGHT_BASE_URL=https://your-instance.gainsightcloud.com
GAINSIGHT_ENABLED=false

# Amplitude (Product Analytics)
AMPLITUDE_API_KEY=your-amplitude-api-key
AMPLITUDE_SECRET_KEY=your-amplitude-secret-key
AMPLITUDE_ENABLED=false

# Salesforce (CRM)
SALESFORCE_CLIENT_ID=your-salesforce-client-id
SALESFORCE_CLIENT_SECRET=your-salesforce-client-secret
SALESFORCE_USERNAME=your-salesforce-username
SALESFORCE_PASSWORD=your-salesforce-password
SALESFORCE_SECURITY_TOKEN=your-salesforce-security-token
SALESFORCE_ENABLED=false

# HubSpot (CRM)
HUBSPOT_API_KEY=your-hubspot-api-key
HUBSPOT_ENABLED=false
```

#### Health Score Configuration

```bash
# Health Score Weights (must sum to 1.0)
HEALTH_SCORE_USAGE_WEIGHT=0.30
# Weight for product usage metrics (30%)
HEALTH_SCORE_ENGAGEMENT_WEIGHT=0.25
# Weight for customer engagement (25%)
HEALTH_SCORE_SUPPORT_WEIGHT=0.15
# Weight for support interaction quality (15%)
HEALTH_SCORE_SATISFACTION_WEIGHT=0.20
# Weight for customer satisfaction (20%)
HEALTH_SCORE_ADOPTION_WEIGHT=0.10
# Weight for feature adoption (10%)

# Health Score Thresholds
HEALTH_SCORE_EXCELLENT_THRESHOLD=80
# Score >= 80 is "Excellent"
HEALTH_SCORE_GOOD_THRESHOLD=60
# Score >= 60 is "Good"
HEALTH_SCORE_AT_RISK_THRESHOLD=40
# Score >= 40 is "At Risk", < 40 is "Critical"

# Health Score Calculation
HEALTH_SCORE_UPDATE_INTERVAL=3600
# Seconds between health score recalculations (1 hour)
HEALTH_SCORE_LOOKBACK_DAYS=30
# Number of days to include in health score calculation
```

#### Performance and Optimization

```bash
# Worker Configuration
WORKER_THREADS=4
# Number of worker threads for async operations

# Request Timeouts
REQUEST_TIMEOUT=30
# Default request timeout in seconds
LONG_RUNNING_TIMEOUT=300
# Timeout for long-running operations (5 minutes)

# Batch Processing
DEFAULT_BATCH_SIZE=100
# Default batch size for bulk operations
MAX_BATCH_SIZE=1000
# Maximum batch size
```

#### Monitoring and Observability

```bash
# Metrics
METRICS_ENABLED=true
# Enable metrics collection
METRICS_PORT=9090
# Port for Prometheus metrics endpoint

# Health Checks
HEALTH_CHECK_ENABLED=true
# Enable /health endpoint
HEALTH_CHECK_INCLUDE_DB=true
# Include database in health check
HEALTH_CHECK_INCLUDE_REDIS=true
# Include Redis in health check
HEALTH_CHECK_INCLUDE_INTEGRATIONS=false
# Include external integrations in health check (can slow down checks)

# Tracing
TRACING_ENABLED=false
# Enable distributed tracing
TRACING_SERVICE_NAME=cs-mcp-server
# Service name for tracing
TRACING_JAEGER_ENDPOINT=http://jaeger:14268/api/traces
# Jaeger collector endpoint
```

---

## External Integrations Setup

### Zendesk Setup

See comprehensive guide: [`docs/integrations/ZENDESK_SETUP.md`](/Users/evanpaliotta/199os-customer-success-mcp/docs/integrations/ZENDESK_SETUP.md)

**Quick Setup:**

1. **Obtain API Credentials:**
   - Login to Zendesk Admin Center
   - Navigate to: Admin > Channels > API
   - Click "Add API Token"
   - Copy the generated token

2. **Configure Environment Variables:**
   ```bash
   ZENDESK_SUBDOMAIN=your-company
   ZENDESK_EMAIL=your-email@company.com
   ZENDESK_API_TOKEN=your-api-token
   ZENDESK_ENABLED=true
   ```

3. **Test Connection:**
   ```bash
   curl -X POST http://localhost:8080/tools/test_zendesk_connection \
     -H "Content-Type: application/json" | jq
   ```

### Intercom Setup

See comprehensive guide: [`docs/integrations/INTERCOM_SETUP.md`](/Users/evanpaliotta/199os-customer-success-mcp/docs/integrations/INTERCOM_SETUP.md)

**Quick Setup:**

1. **Obtain API Credentials:**
   - Login to Intercom
   - Navigate to: Settings > Developers > Developer Hub
   - Create new app or select existing
   - Copy Access Token and App ID

2. **Configure Environment Variables:**
   ```bash
   INTERCOM_ACCESS_TOKEN=your-access-token
   INTERCOM_APP_ID=your-app-id
   INTERCOM_ENABLED=true
   ```

3. **Test Connection:**
   ```bash
   curl -X POST http://localhost:8080/tools/test_intercom_connection \
     -H "Content-Type: application/json" | jq
   ```

### Mixpanel Setup

See comprehensive guide: [`docs/integrations/MIXPANEL_SETUP.md`](/Users/evanpaliotta/199os-customer-success-mcp/docs/integrations/MIXPANEL_SETUP.md)

**Quick Setup:**

1. **Obtain API Credentials:**
   - Login to Mixpanel
   - Navigate to: Project Settings
   - Copy Project Token and API Secret

2. **Configure Environment Variables:**
   ```bash
   MIXPANEL_PROJECT_TOKEN=your-project-token
   MIXPANEL_API_SECRET=your-api-secret
   MIXPANEL_ENABLED=true
   ```

3. **Test Connection:**
   ```bash
   curl -X POST http://localhost:8080/tools/test_mixpanel_connection \
     -H "Content-Type: application/json" | jq
   ```

### SendGrid Setup

See comprehensive guide: [`docs/integrations/SENDGRID_SETUP.md`](/Users/evanpaliotta/199os-customer-success-mcp/docs/integrations/SENDGRID_SETUP.md)

**Quick Setup:**

1. **Obtain API Key:**
   - Login to SendGrid
   - Navigate to: Settings > API Keys
   - Click "Create API Key"
   - Select "Full Access" permissions
   - Copy the generated key

2. **Verify Sender Email:**
   - Navigate to: Settings > Sender Authentication
   - Click "Verify a Single Sender"
   - Enter and verify your email address

3. **Configure Environment Variables:**
   ```bash
   SENDGRID_API_KEY=your-api-key
   SENDGRID_FROM_EMAIL=noreply@yourcompany.com
   SENDGRID_FROM_NAME=Your Company
   SENDGRID_ENABLED=true
   ```

4. **Test Email Sending:**
   ```bash
   curl -X POST http://localhost:8080/tools/send_email \
     -H "Content-Type: application/json" \
     -d '{
       "to_email": "test@example.com",
       "subject": "Test Email",
       "html_content": "<p>This is a test email.</p>"
     }' | jq
   ```

---

## Database Setup

### PostgreSQL Installation

See installation instructions in [Deployment Methods](#deployment-methods) section.

### Database Schema and Migrations

#### Initialize Database Schema

```bash
# Using Alembic migrations
alembic upgrade head

# Verify schema
psql -U cs_user -d cs_mcp_db -c "\dt"
```

#### Database Tables

The CS MCP Server uses the following database tables:

**Core Tables:**
- `clients` - Customer client records
- `health_scores` - Historical health score data
- `onboarding_plans` - Customer onboarding plans
- `training_programs` - Training and certification programs
- `milestones` - Onboarding milestone tracking

**Engagement Tables:**
- `interactions` - Customer interactions and touchpoints
- `communications` - Email and message history
- `support_tickets` - Support ticket tracking
- `feedback` - Customer feedback and surveys

**Analytics Tables:**
- `usage_metrics` - Product usage analytics
- `feature_adoption` - Feature adoption tracking
- `churn_predictions` - Churn risk scores
- `expansion_opportunities` - Upsell/cross-sell opportunities

**System Tables:**
- `audit_logs` - Security and activity audit trail
- `preferences` - Learned user preferences
- `rate_limits` - Rate limiting state

### Database Indexes

Critical indexes for performance:

```sql
-- Client lookups
CREATE INDEX idx_clients_client_id ON clients(client_id);
CREATE INDEX idx_clients_lifecycle_stage ON clients(lifecycle_stage);
CREATE INDEX idx_clients_health_score ON clients(health_score);

-- Health score queries
CREATE INDEX idx_health_scores_client_id ON health_scores(client_id);
CREATE INDEX idx_health_scores_timestamp ON health_scores(timestamp);

-- Interaction queries
CREATE INDEX idx_interactions_client_id ON interactions(client_id);
CREATE INDEX idx_interactions_timestamp ON interactions(timestamp);

-- Support ticket queries
CREATE INDEX idx_support_tickets_client_id ON support_tickets(client_id);
CREATE INDEX idx_support_tickets_status ON support_tickets(status);

-- Audit log queries
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_client_id ON audit_logs(client_id);
```

### Database Backup and Restore

#### Automated Backups

**Using pg_dump (recommended for PostgreSQL):**

```bash
# Create backup script
cat > /usr/local/bin/backup-cs-mcp-db.sh <<'EOF'
#!/bin/bash
BACKUP_DIR=/backups/cs-mcp-db
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/cs_mcp_db_$TIMESTAMP.sql.gz"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U cs_user -h localhost cs_mcp_db | gzip > $BACKUP_FILE

# Keep only last 30 days of backups
find $BACKUP_DIR -name "cs_mcp_db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
EOF

# Make executable
chmod +x /usr/local/bin/backup-cs-mcp-db.sh

# Schedule daily backups (cron)
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/backup-cs-mcp-db.sh") | crontab -
```

**Cloud Backups:**

**AWS RDS:**
```bash
# Automated backups are enabled by default
# Manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier cs-mcp-db \
  --db-snapshot-identifier cs-mcp-db-manual-$(date +%Y%m%d)
```

**GCP Cloud SQL:**
```bash
# Enable automated backups
gcloud sql instances patch cs-mcp-db \
  --backup-start-time=03:00

# Manual backup
gcloud sql backups create \
  --instance=cs-mcp-db \
  --description="Manual backup $(date)"
```

#### Restore from Backup

```bash
# Restore from pg_dump backup
gunzip -c /backups/cs-mcp-db/cs_mcp_db_20251010_030000.sql.gz | psql -U cs_user -d cs_mcp_db

# AWS RDS restore
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier cs-mcp-db-restored \
  --db-snapshot-identifier cs-mcp-db-manual-20251010

# GCP Cloud SQL restore
gcloud sql backups restore BACKUP_ID \
  --instance=cs-mcp-db
```

---

## Production Checklist

Use this checklist to ensure production readiness before deployment.

### Security

- [ ] **Generate unique encryption keys** (don't use example values)
  - [ ] `MASTER_PASSWORD` generated with `openssl rand -base64 32`
  - [ ] `ENCRYPTION_KEY` generated with `openssl rand -hex 32`
  - [ ] `JWT_SECRET` generated with `openssl rand -base64 64`
  - [ ] `WEBHOOK_SECRET` generated securely
  - [ ] All secrets stored in secure secret management (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault)

- [ ] **Configure secure database connections**
  - [ ] SSL/TLS enabled (`DB_SSL_MODE=require` or higher)
  - [ ] Strong database password (16+ characters, mixed case, numbers, symbols)
  - [ ] Database not exposed to public internet
  - [ ] Database firewall rules configured

- [ ] **Configure secure Redis connections**
  - [ ] Redis authentication enabled (`REDIS_PASSWORD` set)
  - [ ] Redis not exposed to public internet
  - [ ] TLS encryption enabled for Redis (if using `rediss://`)

- [ ] **API security configured**
  - [ ] `MCP_API_KEY` set and secure
  - [ ] `REQUIRE_API_KEY=true` in production
  - [ ] CORS origins configured (`CORS_ORIGINS` set to specific domains)

### Infrastructure

- [ ] **Database configured for production**
  - [ ] Multi-AZ or High Availability enabled
  - [ ] Automated backups enabled (7+ day retention)
  - [ ] Connection pooling configured (`DB_POOL_SIZE=20-50`)
  - [ ] Database monitoring enabled

- [ ] **Redis configured for production**
  - [ ] Cluster mode or replication enabled (for HA)
  - [ ] Maxmemory and eviction policy set
  - [ ] Persistence enabled (AOF or RDB)

- [ ] **Resource limits configured**
  - [ ] CPU and memory limits set (Docker/Kubernetes)
  - [ ] Disk space monitoring configured
  - [ ] Log rotation enabled

- [ ] **Network security**
  - [ ] Firewall rules configured
  - [ ] Security groups configured (cloud)
  - [ ] VPC/network isolation (cloud)
  - [ ] TLS/SSL certificates installed
  - [ ] Reverse proxy configured (Nginx, ALB)

### Configuration

- [ ] **Environment variables reviewed**
  - [ ] All required variables set
  - [ ] No sensitive data in code or version control
  - [ ] `LOG_LEVEL=INFO` (not DEBUG in production)
  - [ ] `DB_ECHO=false` (no SQL logging in production)

- [ ] **Integration credentials verified**
  - [ ] Zendesk credentials tested
  - [ ] Intercom credentials tested
  - [ ] Mixpanel credentials tested
  - [ ] SendGrid credentials tested and sender verified
  - [ ] All enabled integrations have valid credentials

- [ ] **Rate limiting configured**
  - [ ] Global rate limits set appropriately
  - [ ] Per-client rate limits configured
  - [ ] Rate limit storage configured (Redis recommended)

- [ ] **Health score configuration**
  - [ ] Weights sum to 1.0
  - [ ] Thresholds appropriate for business
  - [ ] Update interval configured

### Monitoring and Observability

- [ ] **Logging configured**
  - [ ] Log level appropriate (`INFO` for production)
  - [ ] Log format set to JSON (`LOG_FORMAT=json`)
  - [ ] Log rotation enabled
  - [ ] Log aggregation configured (CloudWatch, Stackdriver, etc.)

- [ ] **Metrics collection enabled**
  - [ ] Prometheus metrics enabled (`METRICS_ENABLED=true`)
  - [ ] Metrics endpoint accessible
  - [ ] Grafana dashboards configured (optional)

- [ ] **Health checks configured**
  - [ ] `/health` endpoint enabled
  - [ ] Database included in health check
  - [ ] Redis included in health check
  - [ ] Load balancer health checks configured

- [ ] **Alerting configured**
  - [ ] High CPU/memory alerts
  - [ ] High error rate alerts
  - [ ] Database connection alerts
  - [ ] Integration failure alerts
  - [ ] On-call rotation configured

### Testing

- [ ] **Deployment tested**
  - [ ] Server starts successfully
  - [ ] Database migrations complete
  - [ ] All 54 tools available
  - [ ] Health check returns healthy

- [ ] **Integration testing**
  - [ ] Zendesk integration tested
  - [ ] Intercom integration tested
  - [ ] Mixpanel integration tested
  - [ ] SendGrid integration tested

- [ ] **Performance testing**
  - [ ] Load testing completed
  - [ ] Response times acceptable (<2s per tool)
  - [ ] Resource usage acceptable under load
  - [ ] Auto-scaling tested (if configured)

### Documentation

- [ ] **Operations documentation**
  - [ ] Deployment runbook created
  - [ ] Rollback procedures documented
  - [ ] Troubleshooting guide available
  - [ ] On-call runbook created

- [ ] **Team training**
  - [ ] Team familiar with deployment process
  - [ ] Team familiar with monitoring dashboards
  - [ ] Team familiar with troubleshooting procedures
  - [ ] Escalation procedures documented

### Compliance

- [ ] **Data privacy**
  - [ ] GDPR compliance reviewed (if applicable)
  - [ ] Data retention policies configured
  - [ ] PII handling reviewed
  - [ ] Data encryption at rest and in transit

- [ ] **Audit logging**
  - [ ] Audit logging enabled
  - [ ] Audit logs retained per compliance requirements
  - [ ] Access to audit logs restricted

---

## Monitoring & Logging

### Structured Logging

The CS MCP Server uses `structlog` for structured JSON logging.

**Log Levels:**
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical failures requiring immediate attention

**Log Output Example:**
```json
{
  "event": "tool_executed",
  "tool_name": "register_client",
  "client_id": "cs_1728567890_acme_corp",
  "duration_ms": 234,
  "status": "success",
  "timestamp": "2025-10-10T14:30:00.123Z",
  "level": "info"
}
```

### Prometheus Metrics

Enable Prometheus metrics for monitoring:

```bash
# Enable in .env
METRICS_ENABLED=true
METRICS_PORT=9090

# Access metrics endpoint
curl http://localhost:9090/metrics
```

**Available Metrics:**
- `cs_mcp_requests_total` - Total requests by tool and status
- `cs_mcp_request_duration_seconds` - Request duration histogram
- `cs_mcp_db_connections_active` - Active database connections
- `cs_mcp_cache_hits_total` - Cache hit count
- `cs_mcp_cache_misses_total` - Cache miss count
- `cs_mcp_integration_requests_total` - Integration requests by platform
- `cs_mcp_integration_errors_total` - Integration errors by platform

### Grafana Dashboard

Import the provided Grafana dashboard for visualization:

1. **Create Prometheus data source:**
   - Navigate to Configuration > Data Sources
   - Add Prometheus data source
   - URL: `http://prometheus:9090`

2. **Import dashboard:**
   - Navigate to Dashboards > Import
   - Upload `grafana-dashboard.json` from the repository
   - Select Prometheus data source

**Dashboard Panels:**
- Request rate and latency
- Error rate by tool
- Database connection pool usage
- Cache hit ratio
- Integration health
- Resource usage (CPU, memory)

### CloudWatch Integration (AWS)

Configure CloudWatch for AWS deployments:

```python
# Add to server.py or initialization.py
import boto3
import watchtower

# Configure CloudWatch logging
cloudwatch_handler = watchtower.CloudWatchLogHandler(
    log_group='/aws/ecs/cs-mcp-server',
    stream_name='cs-mcp-{strftime:%Y-%m-%d}',
    send_interval=10,
    create_log_group=True
)

logger.add(cloudwatch_handler)
```

**CloudWatch Alarms:**
```bash
# Create alarms (see AWS deployment section)
aws cloudwatch put-metric-alarm \
  --alarm-name cs-mcp-high-error-rate \
  --alarm-description "Alert when error rate > 5%" \
  --metric-name ErrorRate \
  --namespace CS-MCP \
  --statistic Average \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### Log Aggregation

**Using ELK Stack:**

```yaml
# docker-compose.yml addition
services:
  elasticsearch:
    image: elasticsearch:8.10.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  logstash:
    image: logstash:8.10.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: kibana:8.10.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

---

## Troubleshooting

### Common Issues

See comprehensive troubleshooting guide: [`TROUBLESHOOTING.md`](/Users/evanpaliotta/199os-customer-success-mcp/TROUBLESHOOTING.md)

**Quick Troubleshooting:**

1. **Server won't start:**
   ```bash
   # Check logs
   docker-compose logs mcp-server

   # Common causes:
   # - Database connection failure (check DATABASE_URL)
   # - Redis connection failure (check REDIS_URL)
   # - Port already in use (check SERVER_PORT)
   # - Missing environment variables
   ```

2. **Database connection errors:**
   ```bash
   # Test database connection
   psql $DATABASE_URL -c "SELECT 1"

   # Check PostgreSQL is running
   systemctl status postgresql
   # or
   docker-compose ps postgres
   ```

3. **Redis connection errors:**
   ```bash
   # Test Redis connection
   redis-cli -h <host> -p <port> -a <password> ping

   # Check Redis is running
   systemctl status redis
   # or
   docker-compose ps redis
   ```

4. **Integration failures:**
   ```bash
   # Test integration connections
   curl -X POST http://localhost:8080/tools/test_zendesk_connection
   curl -X POST http://localhost:8080/tools/test_intercom_connection
   curl -X POST http://localhost:8080/tools/test_mixpanel_connection

   # Check credentials in .env
   # Verify network connectivity to integration platforms
   ```

---

## Rollback Procedures

### Docker Rollback

```bash
# List recent images
docker images 199os/customer-success-mcp

# Rollback to previous version
docker-compose stop
docker-compose pull 199os/customer-success-mcp:v1.0.0
docker-compose up -d

# Verify rollback
docker-compose ps
curl http://localhost:8080/health
```

### Database Rollback

```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Restore from backup (if needed)
gunzip -c /backups/cs-mcp-db/cs_mcp_db_20251010_030000.sql.gz | psql -U cs_user -d cs_mcp_db
```

### AWS ECS Rollback

```bash
# List task definition revisions
aws ecs list-task-definitions --family-prefix cs-mcp-server

# Update service to previous revision
aws ecs update-service \
  --cluster cs-mcp-cluster \
  --service cs-mcp-service \
  --task-definition cs-mcp-server:1

# Monitor rollback
aws ecs describe-services \
  --cluster cs-mcp-cluster \
  --services cs-mcp-service
```

### Kubernetes Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/cs-mcp-server -n cs-mcp

# Rollback to specific revision
kubectl rollout undo deployment/cs-mcp-server --to-revision=2 -n cs-mcp

# Check rollback status
kubectl rollout status deployment/cs-mcp-server -n cs-mcp
```

---

## Scaling Recommendations

### Vertical Scaling (Scale Up)

**When to scale up:**
- CPU usage consistently >70%
- Memory usage consistently >80%
- Database connection pool exhausted
- High request latency (>2 seconds)

**Recommended configurations by load:**

**Low Volume (<1000 req/min):**
```
MCP Server: 2 CPU, 4GB RAM
PostgreSQL: db.t3.medium (2 vCPU, 4GB RAM)
Redis: cache.t3.medium (2 vCPU, 3.09GB RAM)
```

**Medium Volume (1000-5000 req/min):**
```
MCP Server: 4 CPU, 8GB RAM
PostgreSQL: db.t3.large (2 vCPU, 8GB RAM)
Redis: cache.m5.large (2 vCPU, 6.38GB RAM)
```

**High Volume (5000-10000 req/min):**
```
MCP Server: 8 CPU, 16GB RAM
PostgreSQL: db.m5.xlarge (4 vCPU, 16GB RAM)
Redis: cache.m5.xlarge (4 vCPU, 12.93GB RAM)
```

**Enterprise Volume (>10000 req/min):**
```
MCP Server: 16 CPU, 32GB RAM (multiple instances)
PostgreSQL: db.m5.2xlarge (8 vCPU, 32GB RAM)
Redis: cache.m5.2xlarge (8 vCPU, 26.04GB RAM)
```

### Horizontal Scaling (Scale Out)

**MCP Server Horizontal Scaling:**

```yaml
# Kubernetes HPA example
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cs-mcp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cs-mcp-server
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**Load Balancer Configuration:**

```nginx
# Nginx load balancer
upstream cs_mcp_backend {
    least_conn;
    server cs-mcp-1:8080 max_fails=3 fail_timeout=30s;
    server cs-mcp-2:8080 max_fails=3 fail_timeout=30s;
    server cs-mcp-3:8080 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    listen 80;
    server_name cs-mcp.yourcompany.com;

    location / {
        proxy_pass http://cs_mcp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
```

### Database Scaling

**Read Replicas:**
```bash
# AWS RDS read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier cs-mcp-db-replica-1 \
  --source-db-instance-identifier cs-mcp-db \
  --db-instance-class db.m5.large

# Configure application to use read replicas
DATABASE_READ_REPLICAS=postgresql://user:pass@replica1:5432/cs_mcp_db,postgresql://user:pass@replica2:5432/cs_mcp_db
```

**Connection Pooling (PgBouncer):**
```bash
# Deploy PgBouncer for connection pooling
docker run -d \
  --name pgbouncer \
  -e DATABASE_URL="postgresql://user:pass@postgres:5432/cs_mcp_db" \
  -e POOL_MODE=transaction \
  -e MAX_CLIENT_CONN=1000 \
  -e DEFAULT_POOL_SIZE=50 \
  -p 6432:6432 \
  pgbouncer/pgbouncer

# Update DATABASE_URL to use PgBouncer
DATABASE_URL=postgresql://user:pass@pgbouncer:6432/cs_mcp_db
```

### Redis Scaling

**Redis Cluster:**
```bash
# AWS ElastiCache cluster mode
aws elasticache create-replication-group \
  --replication-group-id cs-mcp-redis-cluster \
  --replication-group-description "CS MCP Redis Cluster" \
  --engine redis \
  --cache-node-type cache.m5.large \
  --num-node-groups 3 \
  --replicas-per-node-group 2 \
  --automatic-failover-enabled \
  --cluster-mode enabled
```

---

## Additional Resources

**Documentation:**
- [Quick Start Guide](/Users/evanpaliotta/199os-customer-success-mcp/QUICK_START.md)
- [API Reference](/Users/evanpaliotta/199os-customer-success-mcp/API_REFERENCE.md)
- [Troubleshooting Guide](/Users/evanpaliotta/199os-customer-success-mcp/TROUBLESHOOTING.md)
- [Security Documentation](/Users/evanpaliotta/199os-customer-success-mcp/SECURITY.md)
- [Architecture Documentation](/Users/evanpaliotta/199os-customer-success-mcp/ARCHITECTURE.md)

**Integration Guides:**
- [Zendesk Setup](/Users/evanpaliotta/199os-customer-success-mcp/docs/integrations/ZENDESK_SETUP.md)
- [Intercom Setup](/Users/evanpaliotta/199os-customer-success-mcp/docs/integrations/INTERCOM_SETUP.md)
- [Mixpanel Setup](/Users/evanpaliotta/199os-customer-success-mcp/docs/integrations/MIXPANEL_SETUP.md)
- [SendGrid Setup](/Users/evanpaliotta/199os-customer-success-mcp/docs/integrations/SENDGRID_SETUP.md)

**Support:**
- Documentation: https://docs.199os.com (coming soon)
- Issues: GitHub Issues
- Email: support@199os.com

---

**Last Updated:** October 10, 2025
**Version:** 1.0.0
**Status:** Production Ready
