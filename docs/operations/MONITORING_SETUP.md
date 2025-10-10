# Performance Monitoring Setup Guide

## Overview

The Customer Success MCP includes comprehensive performance monitoring using **Prometheus** metrics and **Grafana** dashboards. This guide covers setup, configuration, and usage of the monitoring system.

## Architecture

```
┌─────────────────────┐
│   CS MCP Server     │
│                     │
│  ┌───────────────┐  │
│  │ Performance   │  │
│  │ Monitor       │  │
│  │ (Decorators)  │  │
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │ Prometheus    │  │
│  │ Metrics       │  │
│  │ (Counters,    │  │
│  │  Histograms)  │  │
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │ /metrics      │  │◄──────┐
│  │ HTTP Endpoint │  │       │
│  │ (Port 9090)   │  │       │
│  └───────────────┘  │       │
└─────────────────────┘       │
                              │
                    ┌─────────▼──────────┐
                    │  Prometheus Server │
                    │  (Scrapes metrics) │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Grafana Dashboard │
                    │  (Visualization)   │
                    └────────────────────┘
```

## Installation

### Prerequisites

```bash
# Install Python dependencies
pip install prometheus-client psutil

# Install Prometheus (macOS)
brew install prometheus

# Install Grafana (macOS)
brew install grafana

# Or use Docker Compose (recommended)
docker-compose up -d prometheus grafana
```

### Docker Compose Setup

Add to your `docker-compose.yml`:

```yaml
version: '3.8'

services:
  cs-mcp:
    build: .
    ports:
      - "8080:8080"
      - "9090:9090"  # Metrics endpoint
    environment:
      - PROMETHEUS_ENABLED=true
      - METRICS_PORT=9090

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9091:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./docs/operations/GRAFANA_DASHBOARD.json:/etc/grafana/provisioning/dashboards/cs-mcp.json
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_SERVER_ROOT_URL=http://localhost:3000

volumes:
  prometheus-data:
  grafana-data:
```

### Prometheus Configuration

Create `config/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'cs-mcp'
    static_configs:
      - targets: ['cs-mcp:9090']
        labels:
          service: 'customer-success-mcp'
          environment: 'production'

  # Add alerting rules
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files:
  - '/etc/prometheus/alerts.yml'
```

### Alert Rules

Create `config/alerts.yml`:

```yaml
groups:
  - name: cs_mcp_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(cs_mcp_errors_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors/sec"

      - alert: SlowToolExecution
        expr: histogram_quantile(0.95, rate(cs_mcp_tool_execution_duration_seconds_bucket[5m])) > 5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Tool execution is slow"
          description: "p95 latency is {{ $value }}s"

      - alert: HighMemoryUsage
        expr: cs_mcp_memory_usage_bytes > 1073741824  # 1GB
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanize }} bytes"

      - alert: LowCacheHitRate
        expr: rate(cs_mcp_cache_hits_total[5m]) / (rate(cs_mcp_cache_hits_total[5m]) + rate(cs_mcp_cache_misses_total[5m])) < 0.7
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit rate"
          description: "Cache hit rate is {{ $value | humanizePercentage }}"

      - alert: DatabaseQuerySlow
        expr: histogram_quantile(0.95, rate(cs_mcp_database_query_duration_seconds_bucket[5m])) > 0.2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow database queries detected"
          description: "p95 query duration is {{ $value }}s"
```

## Metrics Reference

### Tool Execution Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `cs_mcp_tool_execution_total` | Counter | Total tool executions | `tool_name`, `status` |
| `cs_mcp_tool_execution_duration_seconds` | Histogram | Tool execution duration | `tool_name` |

**Example Queries:**
```promql
# Tool execution rate
rate(cs_mcp_tool_execution_total[5m])

# Tool execution p95 latency
histogram_quantile(0.95, rate(cs_mcp_tool_execution_duration_seconds_bucket[5m]))

# Success rate
sum(rate(cs_mcp_tool_execution_total{status="success"}[5m])) / sum(rate(cs_mcp_tool_execution_total[5m]))
```

### Database Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `cs_mcp_database_query_total` | Counter | Total database queries | `query_type` |
| `cs_mcp_database_query_duration_seconds` | Histogram | Query duration | `query_type` |

**Example Queries:**
```promql
# Query rate by type
rate(cs_mcp_database_query_total[5m])

# Slow queries (p95 > 50ms)
histogram_quantile(0.95, rate(cs_mcp_database_query_duration_seconds_bucket[5m])) > 0.05
```

### Platform API Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `cs_mcp_platform_api_calls_total` | Counter | Total API calls | `integration`, `endpoint`, `status` |
| `cs_mcp_platform_api_duration_seconds` | Histogram | API call duration | `integration`, `endpoint` |

**Example Queries:**
```promql
# API call rate by integration
rate(cs_mcp_platform_api_calls_total[5m])

# API error rate
rate(cs_mcp_platform_api_calls_total{status="error"}[5m])
```

### Cache Metrics

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `cs_mcp_cache_hits_total` | Counter | Total cache hits | `cache_type` |
| `cs_mcp_cache_misses_total` | Counter | Total cache misses | `cache_type` |

**Example Queries:**
```promql
# Cache hit rate
rate(cs_mcp_cache_hits_total[5m]) / (rate(cs_mcp_cache_hits_total[5m]) + rate(cs_mcp_cache_misses_total[5m]))
```

### Health Score Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `cs_mcp_health_score_calculation_seconds` | Histogram | Health score calculation duration |

**Target:** <100ms (p95)

### System Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `cs_mcp_active_connections` | Gauge | Number of active connections |
| `cs_mcp_memory_usage_bytes` | Gauge | Current memory usage |
| `cs_mcp_errors_total` | Counter | Total errors by type |

## Grafana Dashboard Setup

### Import Dashboard

1. Open Grafana: `http://localhost:3000`
2. Login (default: admin/admin)
3. Go to **Dashboards → Import**
4. Upload `docs/operations/GRAFANA_DASHBOARD.json`
5. Select Prometheus datasource
6. Click **Import**

### Dashboard Panels

The dashboard includes 14 panels:

1. **Tool Execution Rate** - Requests per second by tool
2. **Tool Execution Duration** - p50, p95, p99 latencies
3. **Error Rate** - Errors per second by type
4. **Success Rate** - Overall success percentage
5. **Active Connections** - Current connection count
6. **Memory Usage** - Process memory over time
7. **Database Query Duration** - p95 query latency
8. **Database Query Rate** - Queries per second
9. **Platform API Duration** - p95 API latency
10. **Platform API Rate** - API calls per second
11. **Cache Hit Rate** - Cache effectiveness
12. **Health Score Performance** - Health calculation speed
13. **Top 10 Slowest Tools** - Performance bottlenecks
14. **Most Called Tools** - Usage patterns

## Usage in Code

### Decorating Tools

```python
from src.monitoring.performance_monitor import monitor_tool_execution

@monitor_tool_execution()
async def my_tool(ctx, client_id: str):
    """My tool implementation"""
    # Tool logic here
    return result
```

### Decorating Database Queries

```python
from src.monitoring.performance_monitor import monitor_database_query

@monitor_database_query("select")
async def get_customer(client_id: str):
    """Get customer from database"""
    # Database query here
    return customer
```

### Decorating API Calls

```python
from src.monitoring.performance_monitor import monitor_api_call

@monitor_api_call("zendesk", "create_ticket")
async def create_zendesk_ticket(data):
    """Create ticket in Zendesk"""
    # API call here
    return ticket
```

### Recording Cache Operations

```python
from src.monitoring.performance_monitor import record_cache_hit, record_cache_miss

async def get_from_cache(key: str):
    value = await redis.get(key)
    if value:
        record_cache_hit("redis")
        return value
    else:
        record_cache_miss("redis")
        return None
```

### Monitoring Health Score Calculation

```python
from src.monitoring.performance_monitor import monitor_health_score_calculation

async def calculate_health_score(client_id: str):
    with monitor_health_score_calculation():
        # Health score calculation here
        score = compute_score()
    return score
```

## Performance Targets

| Operation | Target | Current | Status |
|-----------|--------|---------|--------|
| Tool execution (avg) | <500ms | TBD | ⚠️ Measure |
| Health score calculation | <100ms | TBD | ⚠️ Measure |
| Database query (indexed) | <50ms | TBD | ⚠️ Measure |
| Platform API call | <2s | TBD | ⚠️ Measure |
| Server startup | <10s | TBD | ⚠️ Measure |

## Running Performance Tests

```bash
# Run all performance tests
pytest tests/test_performance.py -v

# Run only benchmarks
pytest tests/test_performance.py -v -m benchmark

# Generate performance report
pytest tests/test_performance.py --benchmark-only --benchmark-json=output.json

# Establish baselines
pytest tests/test_performance.py::TestPerformanceBaselines::test_establish_baselines
```

## Troubleshooting

### Metrics endpoint returns 404

**Problem:** `/metrics` endpoint not accessible

**Solution:**
1. Ensure metrics server is started:
   ```python
   from src.monitoring.metrics_server import start_metrics_server
   start_metrics_server(port=9090)
   ```

2. Check if port 9090 is available:
   ```bash
   lsof -i :9090
   ```

### Prometheus not scraping metrics

**Problem:** Prometheus dashboard shows "Target Down"

**Solution:**
1. Check Prometheus targets: `http://localhost:9091/targets`
2. Verify CS MCP is running and accessible
3. Check firewall rules allow connection to port 9090
4. Review Prometheus logs:
   ```bash
   docker logs prometheus
   ```

### Grafana dashboard shows no data

**Problem:** Dashboard panels are empty

**Solution:**
1. Verify Prometheus datasource is configured in Grafana
2. Check Prometheus is scraping metrics successfully
3. Verify time range in Grafana dashboard
4. Run a test query in Prometheus:
   ```promql
   cs_mcp_tool_execution_total
   ```

### High memory usage

**Problem:** `cs_mcp_memory_usage_bytes` growing continuously

**Solution:**
1. Check for memory leaks in tool implementations
2. Review cache TTL settings (may need to evict more aggressively)
3. Monitor slow queries that may accumulate results
4. Consider increasing server memory allocation

## Best Practices

### 1. Set Appropriate Alert Thresholds

Customize alert rules based on your traffic patterns:

```yaml
# For high-traffic production
- alert: HighErrorRate
  expr: rate(cs_mcp_errors_total[5m]) > 0.05  # 5% error rate

# For low-traffic development
- alert: HighErrorRate
  expr: rate(cs_mcp_errors_total[5m]) > 0.01  # 1% error rate
```

### 2. Use Label Filtering

Filter metrics by specific tools or integrations:

```promql
# Only core tools
rate(cs_mcp_tool_execution_total{tool_name=~"register_client|get_client_overview"}[5m])

# Only Zendesk API calls
rate(cs_mcp_platform_api_calls_total{integration="zendesk"}[5m])
```

### 3. Monitor Trends Over Time

Use longer time ranges to identify trends:

```promql
# Compare current week to last week
(rate(cs_mcp_tool_execution_total[1w]) - rate(cs_mcp_tool_execution_total[1w] offset 1w))
```

### 4. Correlate Metrics

Correlate tool performance with external factors:

- Deploy events (via annotations)
- Traffic spikes (API call rate)
- Database load (query duration)
- Cache effectiveness (hit rate)

### 5. Regular Performance Reviews

Schedule weekly/monthly reviews of:

- Top 10 slowest tools → optimize
- Tools with high error rates → debug
- Cache hit rates → tune TTL
- Database query performance → add indexes

## Production Checklist

Before deploying to production:

- [ ] Prometheus server running and scraping metrics
- [ ] Grafana dashboard imported and working
- [ ] Alert rules configured and tested
- [ ] Notification channels set up (Slack, PagerDuty, email)
- [ ] Performance baselines established
- [ ] Load testing completed
- [ ] Monitoring runbook created
- [ ] Team trained on dashboard usage

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)
- [prometheus_client Python Library](https://github.com/prometheus/client_python)
- [Performance Testing Best Practices](https://www.python.org/dev/peps/pep-0008/)

## Support

For monitoring-related issues:

1. Check this documentation first
2. Review Prometheus/Grafana logs
3. Run performance tests: `pytest tests/test_performance.py -v`
4. File an issue on GitHub with:
   - Metrics endpoint output: `curl http://localhost:9090/metrics`
   - Error logs
   - Dashboard screenshots
