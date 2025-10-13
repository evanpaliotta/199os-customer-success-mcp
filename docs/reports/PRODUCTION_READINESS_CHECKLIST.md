# Production Readiness Checklist
## 199OS Customer Success MCP Server

**Status:** 85% Production Ready
**Target Date:** [Set target launch date]
**Last Updated:** October 13, 2025

---

## 🔴 CRITICAL - Must Fix Before Launch

### [ ] 1. Remove Mock Data from Production Code
**File:** `src/tools/core_system_tools.py` (lines 186-328)

**Current Issue:**
```python
# ❌ Hardcoded mock data
client_overview = {
    "client_name": "Acme Corporation",
    "health_score": 82,
}
```

**Required Fix:**
```python
# ✅ Query from database
customer = db.query(CustomerAccount).filter_by(client_id=client_id).first()
if not customer:
    return {"status": "not_found", "error": f"Client {client_id} not found"}

client_overview = {
    "client_name": customer.client_name,
    "health_score": customer.health_score,
}
```

**Files to Update:**
- [ ] `src/tools/core_system_tools.py` - `get_client_overview()` function
- [ ] `src/tools/core_system_tools.py` - `get_client_timeline()` function
- [ ] `src/tools/core_system_tools.py` - `list_clients()` function
- [ ] Any other tools with mock data

**Test Plan:**
- [ ] Query returns real data from database
- [ ] Handles missing customers gracefully
- [ ] All relationships load correctly
- [ ] No performance degradation

**Assignee:** _______________
**Effort:** 3-5 days
**Priority:** CRITICAL 🔴

---

### [ ] 2. Increase Database Connection Pool
**File:** `src/database/__init__.py`

**Current Config:**
```python
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,         # ❌ Too small
    max_overflow=20,      # ❌ Total = 30 connections
    echo=False
)
```

**Required Fix:**
```python
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=50,           # ✅ Increased
    max_overflow=50,        # ✅ Total = 100 connections
    pool_timeout=60,        # ✅ Wait time
    pool_recycle=3600,      # ✅ Recycle hourly
    echo=False
)
```

**Test Plan:**
- [ ] Load test with 100 concurrent requests
- [ ] Monitor connection pool utilization
- [ ] Verify no connection exhaustion errors
- [ ] Check connection recycling works

**Assignee:** _______________
**Effort:** 1 hour
**Priority:** HIGH 🟠

---

### [ ] 3. Add Request Timeouts
**Files:** All tools, integrations, database queries

**Required Changes:**

**Tool-level timeouts:**
```python
@mcp.tool(timeout=30)  # ✅ 30 second timeout
async def calculate_health_score(ctx: Context, client_id: str):
    # Tool implementation
```

**Database query timeouts:**
```python
# Add to all database queries
result = db.query(CustomerAccount) \
    .filter_by(client_id=client_id) \
    .execution_options(timeout=5000) \  # ✅ 5 second timeout
    .first()
```

**External API timeouts:**
```python
# Add to all requests calls
response = requests.post(
    url,
    json=data,
    timeout=10  # ✅ 10 second timeout
)
```

**Files to Update:**
- [ ] All 54 MCP tools in `src/tools/*.py`
- [ ] All integration clients in `src/integrations/*.py`
- [ ] Database query functions

**Test Plan:**
- [ ] Verify timeouts trigger correctly
- [ ] Check error messages are clear
- [ ] Test with slow/unresponsive services
- [ ] Ensure no resource leaks

**Assignee:** _______________
**Effort:** 2-3 days
**Priority:** HIGH 🟠

---

### [ ] 4. Implement Monitoring with Prometheus
**New Files:** `src/observability/metrics.py`, `src/observability/middleware.py`

**Metrics to Track:**
```python
from prometheus_client import Counter, Histogram, Gauge

# Tool execution metrics
tool_execution_duration = Histogram(
    'mcp_tool_execution_duration_seconds',
    'Time spent executing MCP tool',
    ['tool_name', 'status']
)

tool_execution_total = Counter(
    'mcp_tool_execution_total',
    'Total tool executions',
    ['tool_name', 'status']
)

# Database metrics
database_query_duration = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['query_type']
)

database_connections_active = Gauge(
    'database_connections_active',
    'Active database connections'
)

# Integration metrics
integration_api_calls_total = Counter(
    'integration_api_calls_total',
    'Total external API calls',
    ['integration', 'status']
)

integration_api_duration = Histogram(
    'integration_api_duration_seconds',
    'External API call duration',
    ['integration', 'endpoint']
)
```

**Integration Points:**
- [ ] Add metrics to all 54 tools
- [ ] Instrument database queries
- [ ] Track external API calls
- [ ] Monitor connection pools
- [ ] Expose `/metrics` endpoint

**Test Plan:**
- [ ] Metrics endpoint returns valid Prometheus format
- [ ] Metrics update in real-time
- [ ] No performance impact from instrumentation
- [ ] Metrics persist across requests

**Assignee:** _______________
**Effort:** 2 days
**Priority:** HIGH 🟠

---

### [ ] 5. Set Up Alerting Rules
**File:** `config/alerting_rules.yml`

**Critical Alerts:**
```yaml
groups:
  - name: critical_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(mcp_tool_execution_total{status="error"}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: DatabaseConnectionPoolExhausted
        expr: database_connections_active >= 95
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly exhausted"

      - alert: SlowToolExecution
        expr: histogram_quantile(0.95, mcp_tool_execution_duration_seconds) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 tool execution latency > 5 seconds"

      - alert: IntegrationAPIDown
        expr: up{job="integration_healthcheck"} == 0
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "External integration API is down"
```

**Integration:**
- [ ] Configure Prometheus AlertManager
- [ ] Set up PagerDuty/Opsgenie integration
- [ ] Test alert firing and resolution
- [ ] Document escalation procedures

**Test Plan:**
- [ ] Trigger each alert condition manually
- [ ] Verify notifications sent correctly
- [ ] Check alert resolution works
- [ ] Test escalation paths

**Assignee:** _______________
**Effort:** 1 day
**Priority:** HIGH 🟠

---

## 🟠 HIGH PRIORITY - Recommended Before Launch

### [ ] 6. Add Distributed Tracing (OpenTelemetry)
**Files:** `src/observability/tracing.py`

**Implementation:**
```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

tracer_provider = TracerProvider()
otlp_exporter = OTLPSpanExporter(endpoint=os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT'))
tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
trace.set_tracer_provider(tracer_provider)
```

**Checkboxes:**
- [ ] Install OpenTelemetry dependencies
- [ ] Configure trace exporter
- [ ] Instrument all tools with spans
- [ ] Add trace context propagation
- [ ] Set up Jaeger or Zipkin backend
- [ ] Create tracing dashboard

**Assignee:** _______________
**Effort:** 3 days
**Priority:** HIGH 🟠

---

### [ ] 7. Set Up Log Aggregation
**Options:** ELK Stack, Datadog, Splunk

**Implementation Steps:**
- [ ] Choose log aggregation service
- [ ] Configure structured logging output (JSON)
- [ ] Set up log shipping (Filebeat or agent)
- [ ] Create log parsing rules
- [ ] Build search/filter dashboards
- [ ] Set up log-based alerts

**Key Logs to Aggregate:**
- Application logs (structlog output)
- Audit logs (security events)
- Database query logs (slow queries)
- Integration API logs (external calls)
- Error traces (exceptions)

**Test Plan:**
- [ ] Logs appear in aggregation service
- [ ] Search queries work correctly
- [ ] Log retention policies applied
- [ ] Performance impact acceptable

**Assignee:** _______________
**Effort:** 2 days
**Priority:** HIGH 🟠

---

### [ ] 8. Move Secrets to Secrets Manager
**Current:** Environment variables in `.env` file
**Target:** AWS Secrets Manager / HashiCorp Vault

**Implementation:**
```python
# src/config/secrets_manager.py
import boto3
from botocore.exceptions import ClientError

class SecretsManager:
    def __init__(self):
        self.client = boto3.client('secretsmanager')

    def get_secret(self, secret_name: str) -> dict:
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return json.loads(response['SecretString'])
        except ClientError as e:
            logger.error(f"Failed to retrieve secret: {e}")
            raise
```

**Secrets to Migrate:**
- [ ] Database credentials (DATABASE_URL)
- [ ] Encryption keys (ENCRYPTION_KEY, JWT_SECRET)
- [ ] Integration credentials (Zendesk, Intercom, etc.)
- [ ] API keys (MCP_API_KEY)
- [ ] Redis password

**Test Plan:**
- [ ] All secrets retrieved successfully
- [ ] Fallback to env vars during development
- [ ] Secret rotation works
- [ ] Access logs audited

**Assignee:** _______________
**Effort:** 1 day
**Priority:** HIGH 🟠

---

### [ ] 9. Add Redis Query Caching
**File:** `src/database/cache.py`

**Implementation:**
```python
import redis
from functools import wraps
import hashlib
import json

redis_client = redis.from_url(os.getenv('REDIS_URL'))

def cache_query(ttl=300):
    """Cache query results in Redis"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"query:{func.__name__}:{hashlib.md5(str(args).encode()).hexdigest()}"

            # Check cache
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)

            # Execute query
            result = func(*args, **kwargs)

            # Cache result
            redis_client.setex(key, ttl, json.dumps(result, default=str))
            return result
        return wrapper
    return decorator
```

**Queries to Cache:**
- [ ] Customer overview (5 min TTL)
- [ ] Health scores (5 min TTL)
- [ ] Segment lists (10 min TTL)
- [ ] Support ticket counts (1 min TTL)
- [ ] Analytics aggregations (15 min TTL)

**Test Plan:**
- [ ] Cache hit rate > 50%
- [ ] Cache invalidation on updates
- [ ] Performance improvement measured
- [ ] Memory usage acceptable

**Assignee:** _______________
**Effort:** 3 days
**Priority:** MEDIUM 🟡

---

### [ ] 10. Create Kubernetes Manifests
**Files:** `k8s/deployment.yaml`, `k8s/service.yaml`, `k8s/ingress.yaml`

**Resources to Create:**
- [ ] Deployment (3 replicas, rolling update strategy)
- [ ] Service (LoadBalancer or ClusterIP)
- [ ] ConfigMap (non-sensitive configuration)
- [ ] Secret (sensitive credentials)
- [ ] HorizontalPodAutoscaler (CPU/memory based)
- [ ] Ingress (external access)
- [ ] PersistentVolumeClaim (for logs if needed)

**Example Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cs-mcp-server
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: cs-mcp-server
  template:
    spec:
      containers:
      - name: cs-mcp-server
        image: 199os/customer-success-mcp:1.0.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
```

**Test Plan:**
- [ ] Deployment succeeds
- [ ] All pods become Ready
- [ ] Rolling updates work
- [ ] Auto-scaling triggers correctly
- [ ] Health checks pass

**Assignee:** _______________
**Effort:** 2 days
**Priority:** MEDIUM 🟡

---

## 🟡 MEDIUM PRIORITY - Recommended for Scale

### [ ] 11. Implement Repository Pattern
**Goal:** Decouple tools from database models

**Structure:**
```
src/repositories/
├── __init__.py
├── customer_repository.py
├── health_repository.py
├── onboarding_repository.py
└── support_repository.py

src/services/
├── __init__.py
├── health_service.py
├── onboarding_service.py
└── retention_service.py
```

**Example:**
```python
# src/repositories/customer_repository.py
class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_client_id(self, client_id: str) -> Optional[CustomerAccount]:
        return self.db.query(CustomerAccount).filter_by(client_id=client_id).first()

    def get_health_score(self, client_id: str) -> HealthScoreComponents:
        return self.db.query(HealthScoreComponents) \
            .filter_by(client_id=client_id) \
            .order_by(HealthScoreComponents.created_at.desc()) \
            .first()
```

**Files to Refactor:**
- [ ] Create repository classes (5 repositories)
- [ ] Create service classes (5 services)
- [ ] Update all 54 tools to use services
- [ ] Add unit tests for repositories
- [ ] Add unit tests for services

**Assignee:** _______________
**Effort:** 5-7 days
**Priority:** MEDIUM 🟡

---

### [ ] 12. Deploy Load Balancer + 3 Instances
**Infrastructure Setup:**

**Option A: Docker Compose**
```yaml
services:
  nginx:
    image: nginx:latest
    ports:
      - "8080:8080"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf

  cs-mcp-1:
    image: 199os/customer-success-mcp:1.0.0
    environment:
      - INSTANCE_ID=1

  cs-mcp-2:
    image: 199os/customer-success-mcp:1.0.0
    environment:
      - INSTANCE_ID=2

  cs-mcp-3:
    image: 199os/customer-success-mcp:1.0.0
    environment:
      - INSTANCE_ID=3
```

**Option B: Kubernetes**
```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 3  # 3 instances
```

**Nginx Configuration:**
```nginx
upstream mcp_backend {
    least_conn;  # Route to instance with fewest connections
    server cs-mcp-1:8080;
    server cs-mcp-2:8080;
    server cs-mcp-3:8080;
}

server {
    listen 8080;
    location / {
        proxy_pass http://mcp_backend;
        proxy_set_header X-Request-ID $request_id;
    }
}
```

**Test Plan:**
- [ ] Traffic distributes across all 3 instances
- [ ] Failover works when instance dies
- [ ] Session affinity (if needed) works
- [ ] Health checks remove unhealthy instances
- [ ] Load balancing algorithm works correctly

**Assignee:** _______________
**Effort:** 2 days
**Priority:** MEDIUM 🟡

---

### [ ] 13. Add Database Read Replicas
**Goal:** Offload read queries from primary database

**Setup:**
- [ ] Create 2 read replica instances
- [ ] Configure replication lag monitoring
- [ ] Update connection configuration

**Code Changes:**
```python
# src/database/__init__.py
primary_engine = create_engine(os.getenv('DATABASE_URL'))
replica_engines = [
    create_engine(os.getenv('DATABASE_REPLICA_1_URL')),
    create_engine(os.getenv('DATABASE_REPLICA_2_URL')),
]

def get_read_engine():
    """Round-robin load balancing"""
    import random
    return random.choice(replica_engines)

# Update repository to use read replicas
class CustomerRepository:
    def find_by_client_id(self, client_id: str):
        # Use read replica for read-only query
        db = sessionmaker(bind=get_read_engine())()
        return db.query(CustomerAccount).filter_by(client_id=client_id).first()
```

**Queries to Move to Replicas:**
- [ ] All SELECT queries (no writes)
- [ ] Analytics/reporting queries
- [ ] Dashboard queries
- [ ] Health score calculations

**Test Plan:**
- [ ] Queries route to replicas
- [ ] Writes still go to primary
- [ ] Replication lag acceptable (<1 second)
- [ ] Failover to primary if replicas down

**Assignee:** _______________
**Effort:** 2 days
**Priority:** MEDIUM 🟡

---

### [ ] 14. Set Up CI/CD Pipeline
**File:** `.github/workflows/deploy.yml`

**Pipeline Stages:**
1. **Test:**
   - Run unit tests
   - Run integration tests
   - Check code coverage (>80%)
   - Run linting (Black, Ruff)

2. **Build:**
   - Build Docker image
   - Tag with git SHA
   - Push to container registry
   - Scan for vulnerabilities

3. **Deploy:**
   - Deploy to staging
   - Run smoke tests
   - Deploy to production (manual approval)
   - Run health checks

**Example Workflow:**
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest tests/ --cov=src --cov-fail-under=80

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Build Docker image
        run: docker build -t 199os/customer-success-mcp:${{ github.sha }} .
      - name: Push to registry
        run: docker push 199os/customer-success-mcp:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/cs-mcp-server \
            cs-mcp-server=199os/customer-success-mcp:${{ github.sha }}
          kubectl rollout status deployment/cs-mcp-server
```

**Checkboxes:**
- [ ] Create CI/CD pipeline configuration
- [ ] Set up staging environment
- [ ] Configure manual approval gates
- [ ] Add rollback procedures
- [ ] Document deployment process

**Assignee:** _______________
**Effort:** 3 days
**Priority:** MEDIUM 🟡

---

### [ ] 15. Add Security Headers
**File:** `src/middleware/security_headers.py`

**Implementation:**
```python
@mcp.middleware()
async def security_headers(ctx: Context, next_handler):
    result = await next_handler()

    # Add security headers
    ctx.response.headers.update({
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    })

    return result
```

**Headers to Add:**
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY
- [ ] X-XSS-Protection: 1; mode=block
- [ ] Strict-Transport-Security (HSTS)
- [ ] Content-Security-Policy (CSP)
- [ ] Referrer-Policy
- [ ] Permissions-Policy

**Test Plan:**
- [ ] Headers present in all responses
- [ ] Security scan passes (OWASP ZAP)
- [ ] No functionality broken

**Assignee:** _______________
**Effort:** 1 day
**Priority:** MEDIUM 🟡

---

## 🔵 LOW PRIORITY - Future Enhancements

### [ ] 16. Implement Request Queuing (RQ/Celery)
**Goal:** Offload long-running tasks to background workers

**Assignee:** _______________
**Effort:** 5 days
**Priority:** LOW 🔵

---

### [ ] 17. Database Sharding Strategy
**Goal:** Partition data across multiple databases

**Assignee:** _______________
**Effort:** 10 days
**Priority:** LOW 🔵

---

### [ ] 18. Multi-Region Deployment
**Goal:** Deploy to multiple AWS regions for global availability

**Assignee:** _______________
**Effort:** 10 days
**Priority:** LOW 🔵

---

### [ ] 19. Add Chaos Engineering Tests
**Goal:** Test resilience under failure conditions

**Assignee:** _______________
**Effort:** 5 days
**Priority:** LOW 🔵

---

### [ ] 20. Implement OAuth 2.0 Authentication
**Goal:** Replace API key auth with OAuth

**Assignee:** _______________
**Effort:** 3 days
**Priority:** LOW 🔵

---

## 📊 Progress Tracking

### Overall Completion: [ ] 0 / 20 items (0%)

**By Priority:**
- 🔴 Critical: [ ] 0/5 items (0%)
- 🟠 High: [ ] 0/5 items (0%)
- 🟡 Medium: [ ] 0/5 items (0%)
- 🔵 Low: [ ] 0/5 items (0%)

**Estimated Total Effort:** 50-65 days (10-13 weeks)

**Critical Path to Launch:** Items 1-5 (7-12 days)

---

## 🎯 Launch Criteria

Production launch is approved when:

- [x] All CRITICAL items complete (5/5)
- [x] All HIGH priority items complete (5/5)
- [x] Staging environment testing passed
- [x] Security audit passed
- [x] Load testing passed (1,000 concurrent users)
- [x] Disaster recovery tested
- [x] Runbooks documented
- [x] On-call rotation established

---

## 📞 Team & Contacts

**Engineering Lead:** _______________
**DevOps Engineer:** _______________
**QA Engineer:** _______________
**Security Engineer:** _______________

**Review Frequency:** Weekly
**Next Review Date:** _______________

---

**Last Updated:** October 13, 2025
**Version:** 1.0.0
