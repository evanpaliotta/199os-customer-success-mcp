# Customer Success MCP Operations Runbook

**Version:** 1.0.0
**Last Updated:** October 10, 2025
**Audience:** DevOps, SRE, On-Call Engineers

This runbook contains standard operating procedures, incident response playbooks, and maintenance tasks for the Customer Success MCP in production.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Common Operational Tasks](#common-operational-tasks)
3. [Incident Response Procedures](#incident-response-procedures)
4. [Rollback Procedures](#rollback-procedures)
5. [Database Maintenance](#database-maintenance)
6. [Scaling Procedures](#scaling-procedures)
7. [Monitoring and Alerting](#monitoring-and-alerting)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Emergency Contacts](#emergency-contacts)

---

## Architecture Overview

### System Components

```
┌─────────────┐
│   Client    │ (Claude Desktop, API Client)
│    (MCP)    │
└──────┬──────┘
       │ MCP Protocol (stdio/HTTP)
       ▼
┌─────────────────────────────────────┐
│     Load Balancer (HTTPS)           │
│  cs-mcp.yourcompany.com:443         │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌──────────────┐
│  CS MCP      │  │  CS MCP      │
│  Instance 1  │  │  Instance 2  │
│  Port 8080   │  │  Port 8080   │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                │
    ┌───────────┼───────────────┐
    │           │               │
    ▼           ▼               ▼
┌────────┐ ┌────────┐  ┌──────────────┐
│ Postgr │ │ Redis  │  │  Platform    │
│  SQL   │ │ Cache  │  │ Integrations │
│  DB    │ │        │  │ (Zendesk,    │
│        │ │        │  │  Intercom,   │
└────────┘ └────────┘  │  Mixpanel,   │
                       │  SendGrid)   │
                       └──────────────┘
```

### Key Endpoints

- **Application:** `https://cs-mcp.yourcompany.com`
- **Health Check:** `https://cs-mcp.yourcompany.com/health`
- **Metrics:** `https://cs-mcp.yourcompany.com/metrics` (internal only)
- **Database:** `cs-mcp-prod.cluster-xxx.region.rds.amazonaws.com:5432`
- **Redis:** `cs-mcp-prod.xxx.cache.amazonaws.com:6379`

### Technology Stack

- **Application:** Python 3.11, FastMCP, Pydantic
- **Database:** PostgreSQL 16
- **Cache:** Redis 7
- **Container:** Docker (non-root user: csops)
- **Orchestration:** AWS ECS / Kubernetes (deployment-specific)
- **Monitoring:** Prometheus, Grafana
- **Logging:** CloudWatch / ELK Stack

---

## Common Operational Tasks

### Checking System Health

#### Quick Health Check
```bash
# Check application health
curl https://cs-mcp.yourcompany.com/health

# Expected response: {"status": "healthy", "timestamp": "..."}
```

#### Comprehensive Health Check
```bash
# Check all service health
./scripts/health-check.sh

# Or manually:
# 1. Application
curl https://cs-mcp.yourcompany.com/health

# 2. Database
psql $DATABASE_URL -c "SELECT 1;"

# 3. Redis
redis-cli -u $REDIS_URL ping

# 4. Container status
docker ps --filter "name=cs-mcp" --filter "health=healthy"
```

### Viewing Logs

#### Application Logs
```bash
# Tail latest logs (CloudWatch)
aws logs tail /aws/ecs/cs-mcp-prod --follow

# Filter for errors
aws logs tail /aws/ecs/cs-mcp-prod --follow --filter-pattern "ERROR"

# Search logs by time range
aws logs tail /aws/ecs/cs-mcp-prod --since 1h --until 30m
```

#### Docker Container Logs
```bash
# View container logs
docker logs cs-mcp-container --tail 100 --follow

# Filter for specific patterns
docker logs cs-mcp-container 2>&1 | grep -i "error"
```

#### Database Logs
```bash
# PostgreSQL slow query log
psql $DATABASE_URL -c "SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
WHERE mean_time > 1000
ORDER BY total_time DESC
LIMIT 20;"
```

### Restarting Services

#### Restart Application (Rolling Restart)
```bash
# AWS ECS
aws ecs update-service \
  --cluster cs-mcp-prod \
  --service cs-mcp \
  --force-new-deployment

# Kubernetes
kubectl rollout restart deployment/cs-mcp -n production

# Docker Compose
docker-compose restart cs-mcp
```

#### Restart Redis Cache
```bash
# AWS ElastiCache (creates maintenance window)
aws elasticache reboot-cache-cluster \
  --cache-cluster-id cs-mcp-prod-redis \
  --cache-node-ids-to-reboot "0001"

# Self-hosted
redis-cli -u $REDIS_URL SHUTDOWN
# Redis will auto-restart if managed by systemd/supervisor
```

#### Restart Database (Use with Caution)
```bash
# AWS RDS (triggers failover to standby)
aws rds reboot-db-instance --db-instance-identifier cs-mcp-prod

# Note: This causes ~30-60 seconds of downtime
# Only reboot during maintenance window
```

### Viewing Metrics

#### Prometheus Queries
```bash
# Query Prometheus directly
curl -G http://prometheus.yourcompany.com/api/v1/query \
  --data-urlencode 'query=tool_execution_duration_seconds{quantile="0.95"}'

# Or use Grafana dashboards:
# https://grafana.yourcompany.com/d/cs-mcp-overview
```

#### Common Metrics to Check
```promql
# Error rate
rate(tool_execution_total{status="error"}[5m])

# Request rate
rate(tool_execution_total[5m])

# P95 latency
histogram_quantile(0.95, rate(tool_execution_duration_seconds_bucket[5m]))

# Database connection pool usage
database_connections_active / database_connections_max

# Cache hit rate
cache_hits_total / (cache_hits_total + cache_misses_total)

# Memory usage
container_memory_usage_bytes / container_memory_limit_bytes
```

### Managing Configuration

#### Update Environment Variables
```bash
# AWS ECS: Update task definition
# 1. Create new task definition revision with updated env vars
aws ecs register-task-definition \
  --cli-input-json file://task-definition-updated.json

# 2. Update service to use new task definition
aws ecs update-service \
  --cluster cs-mcp-prod \
  --service cs-mcp \
  --task-definition cs-mcp:NEW_REVISION

# Kubernetes: Update ConfigMap
kubectl edit configmap cs-mcp-config -n production
kubectl rollout restart deployment/cs-mcp -n production
```

#### Rotate Secrets
```bash
# 1. Generate new encryption key
NEW_KEY=$(python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())")

# 2. Update in secrets manager
aws secretsmanager update-secret \
  --secret-id cs-mcp-prod/encryption-key \
  --secret-string "$NEW_KEY"

# 3. Restart application to pick up new secret
aws ecs update-service --cluster cs-mcp-prod --service cs-mcp --force-new-deployment

# Note: For encryption keys, consider supporting multiple keys for rotation
```

### Clearing Cache

#### Clear All Redis Cache
```bash
# WARNING: This will impact performance until cache is repopulated
redis-cli -u $REDIS_URL FLUSHALL

# Safer: Clear specific keys by pattern
redis-cli -u $REDIS_URL --scan --pattern "health_score:*" | xargs redis-cli -u $REDIS_URL DEL
```

#### Clear Specific Customer Cache
```bash
# Clear cache for specific customer
redis-cli -u $REDIS_URL DEL "customer:cs_123456_acme"
redis-cli -u $REDIS_URL DEL "health_score:cs_123456_acme"
```

---

## Incident Response Procedures

### Incident Severity Levels

| Severity | Definition | Response Time | Escalation |
|----------|------------|---------------|------------|
| **P0 - Critical** | Complete service outage, data loss | Immediate | All hands on deck |
| **P1 - High** | Major feature unavailable, significant degradation | 15 minutes | On-call engineer + manager |
| **P2 - Medium** | Minor feature unavailable, limited impact | 1 hour | On-call engineer |
| **P3 - Low** | Cosmetic issue, workaround available | 4 hours | On-call engineer |

### General Incident Response Flow

```
1. DETECT → Alert fires or user report
   ↓
2. ACKNOWLEDGE → On-call engineer acknowledges alert
   ↓
3. ASSESS → Determine severity and impact
   ↓
4. MITIGATE → Apply immediate fix or workaround
   ↓
5. COMMUNICATE → Update status page and stakeholders
   ↓
6. RESOLVE → Implement permanent fix
   ↓
7. POST-MORTEM → Document root cause and prevention
```

### Common Incident Playbooks

#### Playbook 1: High Error Rate

**Symptoms:**
- Alert: "Error rate >1% for 5 minutes"
- Errors in logs
- Customer complaints

**Investigation Steps:**
1. Check Grafana dashboard for error rate spike
2. View application logs for error patterns
   ```bash
   aws logs tail /aws/ecs/cs-mcp-prod --follow --filter-pattern "ERROR"
   ```
3. Identify affected tools/endpoints
4. Check for recent deployments or configuration changes
5. Check platform integration status (Zendesk, Intercom, etc.)

**Common Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Platform API down | Enable graceful degradation, wait for API recovery |
| Database connection exhausted | Restart application to reset connection pool, increase pool size |
| Invalid configuration | Rollback to previous configuration |
| Code bug in recent deployment | Rollback to previous version |
| Rate limit exceeded | Implement backoff, increase rate limits with vendor |

**Mitigation:**
```bash
# If due to bad deployment, rollback immediately
aws ecs update-service --cluster cs-mcp-prod --service cs-mcp --task-definition cs-mcp:PREVIOUS_VERSION

# If due to platform API, check integration status
curl https://status.zendesk.com/api/v2/status.json
curl https://www.intercomstatus.com/api/v2/status.json

# If database connection issue, restart app
aws ecs update-service --cluster cs-mcp-prod --service cs-mcp --force-new-deployment
```

#### Playbook 2: High Latency

**Symptoms:**
- Alert: "P95 latency >1s for 5 minutes"
- Slow response times
- Customer complaints about performance

**Investigation Steps:**
1. Check Grafana dashboard for latency metrics by tool
2. Check database slow query log
   ```bash
   psql $DATABASE_URL -c "SELECT query, mean_time FROM pg_stat_statements WHERE mean_time > 1000 ORDER BY mean_time DESC LIMIT 10;"
   ```
3. Check Redis cache hit rate
   ```promql
   cache_hits_total / (cache_hits_total + cache_misses_total)
   ```
4. Check external API latency
5. Check resource utilization (CPU, memory, disk I/O)

**Common Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Slow database queries | Add indexes, optimize queries, scale database |
| Low cache hit rate | Increase cache TTL, warm up cache |
| External API slow | Increase timeout, implement caching, contact vendor |
| High load | Scale horizontally (add instances) |
| Memory leak | Restart application, investigate root cause |

**Mitigation:**
```bash
# Scale up instances
aws ecs update-service --cluster cs-mcp-prod --service cs-mcp --desired-count 4

# Clear slow query cache (PostgreSQL)
psql $DATABASE_URL -c "SELECT pg_stat_reset();"

# Warm up Redis cache for top customers
python scripts/warm_cache.py --top-customers 100
```

#### Playbook 3: Database Connection Failure

**Symptoms:**
- Alert: "Database connection failed"
- Error logs: "could not connect to server"
- All requests failing

**Investigation Steps:**
1. Check database instance status
   ```bash
   aws rds describe-db-instances --db-instance-identifier cs-mcp-prod | jq '.DBInstances[0].DBInstanceStatus'
   ```
2. Check database connectivity from app server
   ```bash
   psql $DATABASE_URL -c "SELECT 1;"
   ```
3. Check network connectivity and security groups
4. Check database connection pool status
5. Check for database maintenance windows

**Mitigation:**
```bash
# If database is down
# 1. Check AWS RDS console for status
# 2. Initiate failover if multi-AZ
aws rds failover-db-cluster --db-cluster-identifier cs-mcp-prod

# If connection pool exhausted
# Restart application
aws ecs update-service --cluster cs-mcp-prod --service cs-mcp --force-new-deployment

# If security group issue
# Update security group to allow app server IPs
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxx \
  --protocol tcp \
  --port 5432 \
  --source-group sg-app-servers
```

#### Playbook 4: Redis Cache Failure

**Symptoms:**
- Alert: "Redis connection failed"
- Increased database load
- Higher latency
- Error logs: "Redis connection timeout"

**Investigation Steps:**
1. Check Redis instance status
   ```bash
   aws elasticache describe-cache-clusters --cache-cluster-id cs-mcp-prod-redis | jq '.CacheClusters[0].CacheClusterStatus'
   ```
2. Check Redis connectivity
   ```bash
   redis-cli -u $REDIS_URL ping
   ```
3. Check Redis memory usage
4. Check for Redis evictions

**Mitigation:**
```bash
# Application should continue working (degraded performance)
# Redis failures are non-critical due to graceful degradation

# If Redis is down
# 1. Restart Redis (if self-hosted)
redis-cli -u $REDIS_URL SHUTDOWN

# 2. Or restore from backup (AWS ElastiCache)
aws elasticache restore-cache-cluster-from-snapshot \
  --cache-cluster-id cs-mcp-prod-redis \
  --snapshot-name cs-mcp-backup-latest

# 3. Monitor database load (may need to scale database temporarily)
```

#### Playbook 5: Disk Space Full

**Symptoms:**
- Alert: "Disk space <10% remaining"
- Application crashes
- Cannot write logs

**Investigation Steps:**
1. Check disk usage
   ```bash
   df -h
   du -sh /* | sort -h
   ```
2. Identify large files/directories
   ```bash
   find /app -type f -size +100M -exec ls -lh {} \;
   ```
3. Check log file sizes
   ```bash
   du -sh /app/logs/*
   ```

**Mitigation:**
```bash
# Clear old log files
find /app/logs -name "*.log" -mtime +7 -delete

# Compress old logs
find /app/logs -name "*.log" -mtime +1 -exec gzip {} \;

# Rotate logs
logrotate -f /etc/logrotate.d/cs-mcp

# If still critical, increase disk size (requires restart)
# AWS ECS: Update volume size in task definition
# EC2: Extend EBS volume
```

#### Playbook 6: Platform Integration Failure

**Symptoms:**
- Zendesk/Intercom/Mixpanel/SendGrid API calls failing
- Errors: "API rate limit exceeded", "Authentication failed", "Connection timeout"

**Investigation Steps:**
1. Check platform status pages
   - Zendesk: https://status.zendesk.com
   - Intercom: https://www.intercomstatus.com
   - Mixpanel: https://status.mixpanel.com
   - SendGrid: https://status.sendgrid.com
2. Check API credentials are valid
3. Check rate limit headers in logs
4. Test API manually
   ```bash
   # Zendesk
   curl -H "Authorization: Bearer $ZENDESK_API_TOKEN" https://yoursubdomain.zendesk.com/api/v2/tickets.json

   # Intercom
   curl -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" https://api.intercom.io/me
   ```

**Mitigation:**
```bash
# Application implements graceful degradation
# No immediate action needed unless platform API is critical

# If rate limited
# 1. Reduce API call frequency (configure in .env)
# 2. Implement exponential backoff (already implemented)
# 3. Contact vendor to increase rate limits

# If authentication failed
# 1. Verify credentials
# 2. Rotate API keys
# 3. Update credentials in secrets manager

# If platform is down
# Monitor platform status page and wait for recovery
# Application will automatically retry with backoff
```

---

## Rollback Procedures

### When to Rollback

Rollback immediately if:
- Error rate >5% for 10 minutes
- Data corruption detected
- Security breach detected
- Critical functionality broken
- Performance degradation >2x expected

### Application Rollback

#### Step 1: Identify Previous Version
```bash
# List recent deployments
aws ecs list-task-definitions --family-prefix cs-mcp --sort DESC | head -5

# Or check Git tags
git tag -l --sort=-version:refname | head -5
```

#### Step 2: Rollback Application
```bash
# AWS ECS: Update service to previous task definition
aws ecs update-service \
  --cluster cs-mcp-prod \
  --service cs-mcp \
  --task-definition cs-mcp:PREVIOUS_REVISION

# Kubernetes: Rollback deployment
kubectl rollout undo deployment/cs-mcp -n production

# Docker Compose: Pull and restart previous image
docker-compose pull cs-mcp:PREVIOUS_TAG
docker-compose up -d cs-mcp
```

#### Step 3: Verify Rollback
```bash
# Check service status
aws ecs describe-services --cluster cs-mcp-prod --services cs-mcp | jq '.services[0].deployments'

# Check health
curl https://cs-mcp.yourcompany.com/health

# Check metrics
# Monitor error rate and latency for 10 minutes
```

### Database Migration Rollback

#### Step 1: Identify Migration Version
```bash
# Check current migration
alembic current

# List recent migrations
alembic history | head -10
```

#### Step 2: Rollback Migration
```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade abc123

# Rollback all migrations (DANGEROUS)
alembic downgrade base
```

#### Step 3: Verify Rollback
```bash
# Check migration version
alembic current

# Verify table structure
psql $DATABASE_URL -c "\d customers"

# Check for data integrity
psql $DATABASE_URL -c "SELECT COUNT(*) FROM customers;"
```

### Configuration Rollback

#### Step 1: Retrieve Previous Configuration
```bash
# AWS Secrets Manager: List versions
aws secretsmanager list-secret-version-ids --secret-id cs-mcp-prod/config

# Get previous version
aws secretsmanager get-secret-value --secret-id cs-mcp-prod/config --version-stage AWSPREVIOUS
```

#### Step 2: Restore Configuration
```bash
# Update to previous version
aws secretsmanager update-secret \
  --secret-id cs-mcp-prod/config \
  --secret-string "$(aws secretsmanager get-secret-value --secret-id cs-mcp-prod/config --version-stage AWSPREVIOUS --query SecretString --output text)"

# Restart application
aws ecs update-service --cluster cs-mcp-prod --service cs-mcp --force-new-deployment
```

---

## Database Maintenance

### Routine Maintenance Schedule

| Task | Frequency | Timing | Duration |
|------|-----------|--------|----------|
| Backup verification | Daily | 02:00 UTC | 15 min |
| Vacuum analyze | Weekly | Sunday 03:00 UTC | 1-2 hours |
| Reindex | Monthly | 1st Sunday 04:00 UTC | 2-4 hours |
| Statistics update | Daily | 01:00 UTC | 10 min |
| Connection pool cleanup | Weekly | Sunday 02:00 UTC | 5 min |

### Database Backup

#### Manual Backup
```bash
# Full database backup
pg_dump $DATABASE_URL -Fc -f cs-mcp-backup-$(date +%Y%m%d-%H%M%S).dump

# Backup specific table
pg_dump $DATABASE_URL -t customers -Fc -f customers-backup-$(date +%Y%m%d-%H%M%S).dump

# Upload to S3
aws s3 cp cs-mcp-backup-*.dump s3://cs-mcp-backups/manual/
```

#### Verify Backup
```bash
# List backup contents
pg_restore --list cs-mcp-backup-TIMESTAMP.dump | head -20

# Test restore to staging
pg_restore -d $STAGING_DATABASE_URL --clean --if-exists cs-mcp-backup-TIMESTAMP.dump
```

### Database Restore

#### Full Restore
```bash
# 1. Stop application (prevent writes during restore)
aws ecs update-service --cluster cs-mcp-prod --service cs-mcp --desired-count 0

# 2. Download backup from S3
aws s3 cp s3://cs-mcp-backups/daily/cs-mcp-backup-20251010.dump .

# 3. Restore database
pg_restore -d $DATABASE_URL --clean --if-exists cs-mcp-backup-20251010.dump

# 4. Verify restore
psql $DATABASE_URL -c "SELECT COUNT(*) FROM customers;"

# 5. Start application
aws ecs update-service --cluster cs-mcp-prod --service cs-mcp --desired-count 2
```

#### Point-in-Time Restore (AWS RDS)
```bash
# Restore to specific timestamp
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier cs-mcp-prod \
  --target-db-instance-identifier cs-mcp-prod-restored \
  --restore-time 2025-10-10T12:00:00Z

# Wait for restore to complete
aws rds wait db-instance-available --db-instance-identifier cs-mcp-prod-restored

# Update application to use restored database (update DATABASE_URL)
```

### Database Optimization

#### Vacuum and Analyze
```bash
# Vacuum all tables (reclaim space)
psql $DATABASE_URL -c "VACUUM VERBOSE;"

# Analyze tables (update statistics)
psql $DATABASE_URL -c "ANALYZE VERBOSE;"

# Vacuum and analyze together (common)
psql $DATABASE_URL -c "VACUUM ANALYZE VERBOSE;"

# Vacuum specific table
psql $DATABASE_URL -c "VACUUM ANALYZE customers;"
```

#### Reindex
```bash
# Reindex specific table
psql $DATABASE_URL -c "REINDEX TABLE customers;"

# Reindex specific index
psql $DATABASE_URL -c "REINDEX INDEX idx_customers_health_score;"

# Reindex all tables (long-running)
psql $DATABASE_URL -c "REINDEX DATABASE cs_mcp_prod;"
```

#### Query Performance Analysis
```bash
# Find slow queries
psql $DATABASE_URL -c "SELECT query, calls, total_time, mean_time, min_time, max_time
FROM pg_stat_statements
WHERE mean_time > 100
ORDER BY total_time DESC
LIMIT 20;"

# Explain query plan
psql $DATABASE_URL -c "EXPLAIN ANALYZE SELECT * FROM customers WHERE health_score < 50;"

# Check index usage
psql $DATABASE_URL -c "SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY schemaname, tablename;"
```

---

## Scaling Procedures

### Horizontal Scaling (Add/Remove Instances)

#### Scale Up (Handle Increased Load)
```bash
# AWS ECS: Increase desired count
aws ecs update-service \
  --cluster cs-mcp-prod \
  --service cs-mcp \
  --desired-count 4

# Kubernetes: Scale deployment
kubectl scale deployment/cs-mcp --replicas=4 -n production

# Verify scaling
aws ecs describe-services --cluster cs-mcp-prod --services cs-mcp | jq '.services[0].runningCount'
```

#### Scale Down (Reduce Costs)
```bash
# Gradually reduce during low-traffic periods
aws ecs update-service \
  --cluster cs-mcp-prod \
  --service cs-mcp \
  --desired-count 2

# Monitor metrics before scaling down further
# Ensure CPU <60%, memory <70%, error rate <0.1%
```

#### Auto-Scaling Configuration
```bash
# AWS ECS: Configure auto-scaling based on CPU
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/cs-mcp-prod/cs-mcp \
  --min-capacity 2 \
  --max-capacity 10

aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/cs-mcp-prod/cs-mcp \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration file://scaling-policy.json
```

### Vertical Scaling (Increase Resources)

#### Scale Up Instance Size
```bash
# AWS ECS: Update task definition with more CPU/memory
# 1. Edit task definition JSON
vim task-definition.json
# Update: "cpu": "2048", "memory": "4096"

# 2. Register new task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# 3. Update service
aws ecs update-service \
  --cluster cs-mcp-prod \
  --service cs-mcp \
  --task-definition cs-mcp:NEW_REVISION
```

### Database Scaling

#### Vertical Scaling (Increase Instance Size)
```bash
# AWS RDS: Modify instance class
aws rds modify-db-instance \
  --db-instance-identifier cs-mcp-prod \
  --db-instance-class db.r5.xlarge \
  --apply-immediately

# Note: This causes ~30 seconds downtime for single-AZ, minimal for multi-AZ
```

#### Read Replicas (Horizontal Scaling for Reads)
```bash
# Create read replica
aws rds create-db-instance-read-replica \
  --db-instance-identifier cs-mcp-prod-read-1 \
  --source-db-instance-identifier cs-mcp-prod

# Update application to use read replica for read-only queries
# Set READ_DATABASE_URL in environment variables
```

### Redis Scaling

#### Increase Cache Size
```bash
# AWS ElastiCache: Modify node type
aws elasticache modify-cache-cluster \
  --cache-cluster-id cs-mcp-prod-redis \
  --cache-node-type cache.r5.large \
  --apply-immediately
```

---

## Monitoring and Alerting

### Key Metrics to Monitor

#### Application Metrics
- **Error Rate:** Should be <1%
  ```promql
  rate(tool_execution_total{status="error"}[5m]) / rate(tool_execution_total[5m]) * 100
  ```
- **Request Rate:** Monitor for unusual spikes or drops
  ```promql
  rate(tool_execution_total[5m])
  ```
- **Latency (P95):** Should be <1s
  ```promql
  histogram_quantile(0.95, rate(tool_execution_duration_seconds_bucket[5m]))
  ```

#### Infrastructure Metrics
- **CPU Usage:** Should be <70%
- **Memory Usage:** Should be <80%
- **Disk Usage:** Should have >10% free
- **Network I/O:** Monitor for saturation

#### Database Metrics
- **Connection Pool:** Should be <80% utilized
- **Query Duration:** P95 <100ms, P99 <500ms
- **Cache Hit Ratio:** Should be >80%
- **Replication Lag:** Should be <5 seconds

#### External Dependencies
- **Platform API Success Rate:** Should be >99%
- **Platform API Latency:** P95 <2s

### Alert Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Error Rate | >0.5% | >1% | Investigate errors, check platform integrations |
| P95 Latency | >800ms | >1s | Check database queries, cache hit rate |
| CPU Usage | >60% | >80% | Scale horizontally, investigate CPU-intensive code |
| Memory Usage | >70% | >85% | Scale vertically, investigate memory leaks |
| Database Connections | >70% | >85% | Increase pool size, investigate connection leaks |
| Disk Space | <20% | <10% | Clear logs, increase disk size |

---

## Troubleshooting Guide

### Application Won't Start

**Symptoms:** Container keeps restarting, health checks fail

**Check:**
1. View container logs for errors
2. Verify environment variables are set correctly
3. Check database and Redis connectivity
4. Verify encryption keys and secrets are valid
5. Check disk space and permissions

**Solutions:**
```bash
# View startup errors
docker logs cs-mcp-container --tail 100

# Test configuration
python -m src.initialization --skip-validation=false

# Verify secrets
aws secretsmanager get-secret-value --secret-id cs-mcp-prod/config
```

### Slow Performance

**Symptoms:** High latency, timeouts, customer complaints

**Check:**
1. Database slow query log
2. Cache hit rate
3. External API latency
4. Resource utilization (CPU, memory, disk I/O)
5. Network connectivity

**Solutions:**
```bash
# Identify slow queries
psql $DATABASE_URL -c "SELECT * FROM pg_stat_statements WHERE mean_time > 100 ORDER BY total_time DESC LIMIT 10;"

# Check cache hit rate
redis-cli -u $REDIS_URL INFO stats | grep keyspace

# Add database indexes
psql $DATABASE_URL -c "CREATE INDEX CONCURRENTLY idx_name ON table(column);"

# Scale horizontally
aws ecs update-service --cluster cs-mcp-prod --service cs-mcp --desired-count 4
```

### Memory Leak

**Symptoms:** Memory usage continuously increasing, eventually OOM

**Check:**
1. Monitor memory usage over time
2. Check for circular references in code
3. Check for unclosed database connections
4. Check for large objects in memory

**Solutions:**
```bash
# Restart application (temporary fix)
aws ecs update-service --cluster cs-mcp-prod --service cs-mcp --force-new-deployment

# Investigate with memory profiler
# Add memory_profiler to requirements.txt
python -m memory_profiler src/server.py

# Check for connection leaks
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity WHERE state != 'idle';"
```

### Platform Integration Errors

**Symptoms:** API calls failing, timeout errors

**Check:**
1. Platform status pages
2. API credentials validity
3. Rate limit headers
4. Network connectivity
5. Application logs for specific errors

**Solutions:**
```bash
# Check platform status
curl https://status.zendesk.com/api/v2/status.json

# Test API manually
curl -H "Authorization: Bearer $ZENDESK_API_TOKEN" https://yoursubdomain.zendesk.com/api/v2/tickets.json

# Rotate API keys
# Update in secrets manager and restart application

# Increase timeout
# Update PLATFORM_API_TIMEOUT in .env
```

---

## Emergency Contacts

### On-Call Rotation
- **Primary On-Call:** Check PagerDuty schedule
- **Secondary On-Call:** Check PagerDuty schedule
- **Escalation:** Engineering Manager → VP Engineering → CTO

### Platform Support Contacts

#### Zendesk
- **Status:** https://status.zendesk.com
- **Support:** https://support.zendesk.com
- **Priority Support:** priority@zendesk.com (if subscribed)

#### Intercom
- **Status:** https://www.intercomstatus.com
- **Support:** https://www.intercom.com/help
- **Support Email:** team@intercom.com

#### Mixpanel
- **Status:** https://status.mixpanel.com
- **Support:** https://mixpanel.com/get-support
- **Support Email:** support@mixpanel.com

#### SendGrid
- **Status:** https://status.sendgrid.com
- **Support:** https://support.sendgrid.com
- **Priority Support:** priority@sendgrid.com (if subscribed)

### Infrastructure Contacts

#### AWS Support
- **Support Cases:** https://console.aws.amazon.com/support/
- **Phone:** 1-888-273-6847 (US)
- **Business Support:** 1-hour response for production system down
- **Enterprise Support:** 15-minute response for business-critical system down

### Internal Contacts

- **Engineering Manager:** manager@yourcompany.com
- **DevOps Team:** devops@yourcompany.com
- **Security Team:** security@yourcompany.com
- **Customer Success Team:** cs@yourcompany.com

---

## Post-Incident Review Template

After resolving any P0 or P1 incident, complete a post-mortem within 48 hours:

### Incident Summary
- **Date/Time:** [Start time - End time]
- **Severity:** [P0/P1/P2]
- **Duration:** [Total duration]
- **Impact:** [Number of customers affected, revenue impact]

### Timeline
| Time | Event |
|------|-------|
| 12:00 | Alert fired |
| 12:05 | Engineer acknowledged |
| 12:10 | Root cause identified |
| 12:30 | Mitigation applied |
| 12:45 | Incident resolved |

### Root Cause
[Detailed description of what caused the incident]

### Resolution
[What was done to resolve the incident]

### Action Items
- [ ] [Action item 1] - Owner: [Name] - Due: [Date]
- [ ] [Action item 2] - Owner: [Name] - Due: [Date]
- [ ] [Action item 3] - Owner: [Name] - Due: [Date]

### Lessons Learned
- **What went well:**
- **What could be improved:**
- **What will we do differently:**

---

## Change Log

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-10-10 | Initial runbook creation | CS MCP Team |

---

**Last Reviewed:** October 10, 2025
**Next Review:** January 10, 2026 (Quarterly)
