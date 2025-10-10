# Performance Monitoring - Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies (30 seconds)
```bash
pip install prometheus-client psutil
```

### Step 2: Start the Server (10 seconds)
```bash
python server.py
```

The metrics server will automatically start on port 9090.

### Step 3: View Metrics (10 seconds)
```bash
# Open metrics endpoint in browser
open http://localhost:9090/metrics

# Or use curl
curl http://localhost:9090/metrics
```

You should see output like:
```
# HELP cs_mcp_tool_execution_total Total number of tool executions
# TYPE cs_mcp_tool_execution_total counter
cs_mcp_tool_execution_total{status="success",tool_name="register_client"} 5.0

# HELP cs_mcp_tool_execution_duration_seconds Tool execution duration in seconds
# TYPE cs_mcp_tool_execution_duration_seconds histogram
cs_mcp_tool_execution_duration_seconds_bucket{le="0.01",tool_name="register_client"} 2.0
cs_mcp_tool_execution_duration_seconds_bucket{le="0.025",tool_name="register_client"} 4.0
...
```

### Step 4: Run Performance Tests (2 minutes)
```bash
# Run all performance tests
pytest tests/test_performance.py -v

# Establish baselines
pytest tests/test_performance.py::TestPerformanceBaselines::test_establish_baselines -v
```

### Step 5: Setup Grafana (Optional, 2 minutes)
```bash
# Start Grafana with Docker
docker run -d -p 3000:3000 --name=grafana grafana/grafana

# Open Grafana
open http://localhost:3000

# Login (admin/admin)
# Add Prometheus datasource: http://host.docker.internal:9091
# Import dashboard: docs/operations/GRAFANA_DASHBOARD.json
```

## What's Included

### Metrics Available (9 types)
- Tool execution rate and duration
- Database query performance
- Platform API call performance
- Health score calculation time
- Cache hit/miss rates
- Error rates by type
- Active connections
- Memory usage

### Automatic Logging
- ⚠️ Warning: Operations >1 second
- ❌ Error: Operations >5 seconds
- All metrics logged to structured logs

### Performance Targets
| Operation | Target |
|-----------|--------|
| Tool execution | <500ms |
| Health score | <100ms |
| DB query | <50ms |
| API call | <2s |

## Using the Monitoring

### In Your Code

#### Monitor a Tool
```python
from src.monitoring import monitor_tool_execution

@mcp.tool()
@monitor_tool_execution()
async def my_tool(ctx: Context, data: str):
    """This tool is now monitored!"""
    # Your code here
    return {"status": "success"}
```

#### Monitor Database Queries
```python
from src.monitoring import monitor_database_query

@monitor_database_query("select")
async def get_customer(client_id: str):
    """Database query with monitoring"""
    # Your database code
    return customer_data
```

#### Monitor API Calls
```python
from src.monitoring import monitor_api_call

@monitor_api_call("zendesk", "create_ticket")
async def create_ticket(data: dict):
    """API call with monitoring"""
    # Your API code
    return ticket
```

#### Monitor Cache Operations
```python
from src.monitoring import record_cache_hit, record_cache_miss

async def get_from_cache(key: str):
    value = await cache.get(key)
    if value:
        record_cache_hit("redis")
        return value
    else:
        record_cache_miss("redis")
        return None
```

## Configuration

### Environment Variables
```bash
# Enable/disable monitoring (default: true)
export PROMETHEUS_ENABLED=true

# Metrics server port (default: 9090)
export METRICS_PORT=9090

# Metrics server host (default: 0.0.0.0)
export METRICS_HOST=0.0.0.0
```

Add to your `.env` file:
```
PROMETHEUS_ENABLED=true
METRICS_PORT=9090
METRICS_HOST=0.0.0.0
```

## Viewing Metrics

### Option 1: Raw Metrics (No setup required)
```bash
curl http://localhost:9090/metrics
```

### Option 2: Prometheus (Recommended)
```bash
# Create prometheus.yml
cat > prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cs-mcp'
    static_configs:
      - targets: ['localhost:9090']
EOF

# Run Prometheus
docker run -d \
  -p 9091:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Open Prometheus
open http://localhost:9091
```

### Option 3: Grafana (Best visualization)
See Step 5 above.

## Troubleshooting

### Metrics endpoint returns 404
```bash
# Check if prometheus-client is installed
pip install prometheus-client

# Restart server
python server.py
```

### No metrics appearing
```bash
# Execute some tools to generate metrics
# Then check metrics endpoint
curl http://localhost:9090/metrics | grep cs_mcp
```

### Permission denied on port 9090
```bash
# Use a different port
export METRICS_PORT=9091
python server.py
```

## Next Steps

1. **Read the full documentation:**
   - [MONITORING_SETUP.md](docs/operations/MONITORING_SETUP.md)
   - [PERFORMANCE_INTEGRATION_EXAMPLE.md](docs/operations/PERFORMANCE_INTEGRATION_EXAMPLE.md)
   - [PERFORMANCE_MONITORING_SUMMARY.md](docs/operations/PERFORMANCE_MONITORING_SUMMARY.md)

2. **Add monitoring to your tools:**
   - See examples in [PERFORMANCE_INTEGRATION_EXAMPLE.md](docs/operations/PERFORMANCE_INTEGRATION_EXAMPLE.md)

3. **Setup alerts:**
   - Configure Prometheus alerts (see MONITORING_SETUP.md)

4. **Import Grafana dashboard:**
   - Use [GRAFANA_DASHBOARD.json](docs/operations/GRAFANA_DASHBOARD.json)

## Quick Commands Reference

```bash
# Install dependencies
pip install prometheus-client psutil

# Start server with monitoring
python server.py

# View metrics
curl http://localhost:9090/metrics

# Run performance tests
pytest tests/test_performance.py -v

# Check monitoring system
pytest tests/test_performance.py::TestMonitoringSystem -v

# Start Prometheus (Docker)
docker run -d -p 9091:9090 -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus

# Start Grafana (Docker)
docker run -d -p 3000:3000 grafana/grafana
```

## Support

For issues or questions:
1. Check [MONITORING_SETUP.md](docs/operations/MONITORING_SETUP.md) troubleshooting section
2. Review [PERFORMANCE_MONITORING_SUMMARY.md](docs/operations/PERFORMANCE_MONITORING_SUMMARY.md)
3. File an issue on GitHub with metrics output: `curl http://localhost:9090/metrics > metrics.txt`

## Status

✅ **Performance monitoring is ready to use!**

All you need to do:
1. Install dependencies: `pip install prometheus-client psutil`
2. Start server: `python server.py`
3. View metrics: `curl http://localhost:9090/metrics`

The monitoring system will automatically:
- Track all tool executions
- Log slow operations
- Expose metrics for Prometheus
- Calculate performance statistics

**No additional configuration required!**
