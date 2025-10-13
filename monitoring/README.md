# Monitoring Stack for Customer Success MCP

Production-ready monitoring infrastructure using Prometheus, Grafana, and Alertmanager.

## Quick Start

### Start Monitoring Stack

```bash
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### Access Dashboards

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/CHANGE_ME_admin_password)
- **Alertmanager**: http://localhost:9093

## Components

### Prometheus (Port 9090)
- **Purpose**: Metrics collection and storage
- **Retention**: 30 days
- **Scrape Interval**: 15 seconds
- **Configuration**: `prometheus.yml`

### Grafana (Port 3000)
- **Purpose**: Metrics visualization
- **Default Credentials**: admin/CHANGE_ME_admin_password
- **Dashboards**: Auto-provisioned from `grafana/dashboards/`

### Alertmanager (Port 9093)
- **Purpose**: Alert routing and notification
- **Configuration**: `alertmanager.yml`
- **Routes**: Email, Slack, PagerDuty

### Exporters

| Exporter | Port | Purpose |
|----------|------|---------|
| Node Exporter | 9100 | System metrics (CPU, memory, disk) |
| cAdvisor | 8080 | Container metrics |
| Postgres Exporter | 9187 | Database metrics |
| Redis Exporter | 9121 | Cache metrics |
| Blackbox Exporter | 9115 | External endpoint monitoring |

## Alert Rules

See `alerts.yml` for comprehensive alert definitions:

### Critical Alerts
- MCP Server Down
- Database Down
- Database Connection Pool Exhausted
- Critical Disk Space (<5%)
- Health Check Failing

### High Severity Alerts
- Redis Down
- High Error Rate (>1%)
- Database Deadlocks
- Unauthorized Access Attempts
- Integration Down

### Warning Alerts
- High Response Time (>2s)
- High CPU/Memory Usage (>80%)
- Database Slow Queries
- Rate Limit Rejections

## Configuration

### 1. Update Alertmanager Notifications

Edit `alertmanager.yml` and replace placeholders:

```yaml
# SMTP Configuration
smtp_auth_password: 'CHANGE_ME_smtp_password'

# Slack Webhooks
api_url: 'CHANGE_ME_slack_webhook_url'

# PagerDuty
service_key: 'CHANGE_ME_pagerduty_service_key'
```

### 2. Update Database Credentials

Edit `docker-compose.monitoring.yml`:

```yaml
postgres-exporter:
  environment:
    - DATA_SOURCE_NAME=postgresql://username:password@postgres:5432/cs_mcp_production
```

### 3. Update Redis Password

```yaml
redis-exporter:
  environment:
    - REDIS_PASSWORD=${REDIS_PASSWORD}
```

## Monitoring Best Practices

### 1. Alert Fatigue Prevention
- Set appropriate thresholds (not too sensitive)
- Use `for:` clauses to avoid transient alerts
- Group related alerts
- Use inhibition rules to prevent cascading alerts

### 2. Dashboard Organization
- Create role-specific dashboards (Ops, Dev, Business)
- Use consistent color schemes (green=good, yellow=warning, red=critical)
- Include time range selectors
- Add annotation support for deployments

### 3. Retention Strategy
- Prometheus: 30 days local storage
- Long-term storage: Configure `remote_write` to external service
- Consider downsampling for older data

### 4. Security
- Change default Grafana admin password
- Use HTTPS for production (configure reverse proxy)
- Restrict network access to monitoring ports
- Enable authentication for Prometheus/Alertmanager

## Grafana Dashboards

### Pre-configured Dashboards

1. **MCP Server Overview**
   - Request rate, error rate, response times
   - Active connections, rate limit metrics
   - Health check status

2. **Database Performance**
   - Connection pool utilization
   - Query performance (slow queries, deadlocks)
   - Replication lag
   - Database size and growth

3. **System Resources**
   - CPU, memory, disk usage
   - Network I/O
   - Container metrics

4. **Integration Health**
   - External API availability
   - Integration latency
   - Error rates per integration

### Adding Custom Dashboards

1. Create dashboard in Grafana UI
2. Export as JSON
3. Save to `grafana/dashboards/`
4. Restart Grafana

## Alert Testing

### Test Alert Rules

```bash
# Trigger test alert
curl -X POST http://localhost:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning"
    },
    "annotations": {
      "summary": "This is a test alert"
    }
  }]'
```

### Silence Alerts

```bash
# Create silence for maintenance window
amtool silence add alertname=HighCPUUsage --duration=2h --comment="Maintenance window"
```

## Troubleshooting

### Prometheus Not Scraping Targets

```bash
# Check Prometheus logs
docker logs mcp-prometheus

# Check target status
curl http://localhost:9090/api/v1/targets

# Reload configuration
curl -X POST http://localhost:9090/-/reload
```

### Alertmanager Not Sending Notifications

```bash
# Check Alertmanager logs
docker logs mcp-alertmanager

# Test SMTP configuration
docker exec mcp-alertmanager amtool config routes test

# Check alert status
curl http://localhost:9093/api/v1/alerts
```

### Grafana Data Source Issues

1. Go to Configuration > Data Sources
2. Click "Test" button
3. Check Prometheus URL: `http://prometheus:9090`

## Production Deployment

### High Availability Setup

For production, deploy with:
- Multiple Prometheus instances (federation or Thanos)
- Clustered Alertmanager (3+ nodes)
- External Grafana database (PostgreSQL/MySQL)
- Persistent volumes for data retention

### Cloud Integration

#### AWS CloudWatch
```yaml
# Add to prometheus.yml
remote_write:
  - url: https://aps-workspaces.us-east-1.amazonaws.com/workspaces/ws-xxx/api/v1/remote_write
    sigv4:
      region: us-east-1
```

#### Datadog
```yaml
# Add to prometheus.yml
remote_write:
  - url: https://api.datadoghq.com/api/v1/series
    basic_auth:
      password: YOUR_DATADOG_API_KEY
```

## Maintenance

### Backup Prometheus Data

```bash
# Snapshot data
docker exec mcp-prometheus \
  curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot

# Copy snapshot
docker cp mcp-prometheus:/prometheus/snapshots/SNAPSHOT_NAME ./backup/
```

### Update Monitoring Stack

```bash
# Pull latest images
docker-compose -f docker-compose.monitoring.yml pull

# Restart with new images
docker-compose -f docker-compose.monitoring.yml up -d
```

### Clean Up Old Data

```bash
# Remove old Prometheus data (automatic with 30d retention)
# To manually clean:
docker exec mcp-prometheus \
  curl -X POST http://localhost:9090/api/v1/admin/tsdb/clean_tombstones
```

## Metrics Reference

### Custom MCP Metrics

The MCP server exposes these custom metrics at `/metrics`:

```
# Request metrics
http_requests_total{method,path,status}
http_request_duration_seconds{method,path}

# Rate limiting
rate_limit_checks_total{client_id,tool_name}
rate_limit_rejections_total{client_id,tool_name,limit_type}

# Health checks
health_check_status{check_type}
health_check_response_time_ms{check_type}

# Database
database_connection_pool_size
database_connection_pool_active

# Tool execution
mcp_tool_executions_total{tool_name,status}
mcp_tool_duration_seconds{tool_name}
```

## Support

For issues or questions:
- Check logs: `docker-compose -f docker-compose.monitoring.yml logs`
- Review Prometheus targets: http://localhost:9090/targets
- Check Alertmanager status: http://localhost:9093/#/status
- Grafana health: http://localhost:3000/api/health

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [PromQL Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
