# Production Deployment Checklist

**Version:** 1.0.0
**Last Updated:** October 10, 2025
**Target Environment:** Production

This comprehensive checklist ensures that all critical components are validated before deploying the Customer Success MCP to production. Complete all items in sequence before going live.

---

## Pre-Deployment

### Code Quality
- [ ] All tests passing (`pytest tests/ -v --cov=src`)
- [ ] Test coverage >80% (check `htmlcov/index.html`)
- [ ] Linting passing (`black --check src/ tests/`)
- [ ] Type checking passing (`mypy src/`)
- [ ] Security linting passing (`ruff check src/`)
- [ ] No critical or high severity vulnerabilities (`bandit -r src/`)
- [ ] Python dependencies up to date (`safety check`)

### Testing
- [ ] Unit tests passing (all 306+ tests)
- [ ] Integration tests passing (Zendesk, Intercom, Mixpanel, SendGrid)
- [ ] Model validation tests passing (27 models)
- [ ] Input validation tests passing (SQL injection, XSS, path traversal)
- [ ] End-to-end tests passing (complete customer lifecycle)
- [ ] Load testing completed (100+ concurrent requests)
- [ ] Performance benchmarks established (p95 latency <1s)
- [ ] Backup and restore procedures tested

### Documentation
- [ ] README.md up to date
- [ ] INSTALLATION.md reviewed and tested
- [ ] QUICK_START.md verified with fresh environment
- [ ] CONFIGURATION.md complete with all 60+ environment variables
- [ ] Platform integration guides reviewed (Zendesk, Intercom, Mixpanel, SendGrid)
- [ ] API documentation reviewed (TOOL_REFERENCE.md)
- [ ] RUNBOOK.md created for operations team
- [ ] Architecture diagrams current
- [ ] Changelog updated for this release

### Database
- [ ] Database migrations tested (up and down)
- [ ] Migration scripts reviewed for data integrity
- [ ] Rollback procedures tested
- [ ] Indexes validated for performance
- [ ] Foreign key constraints verified
- [ ] Data backup strategy documented
- [ ] Migration downtime estimated and approved

---

## Configuration

### Environment Variables
- [ ] Production `.env` file created (DO NOT commit to version control)
- [ ] DATABASE_URL configured (PostgreSQL 16+ connection string)
- [ ] REDIS_URL configured (Redis 7+ connection string)
- [ ] LOG_LEVEL set to appropriate level (INFO or WARNING for production)
- [ ] LOG_FORMAT set to JSON for structured logging
- [ ] ENVIRONMENT set to "production"

### Security Configuration
- [ ] ENCRYPTION_KEY generated (32+ bytes, base64 encoded)
  ```bash
  python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
  ```
- [ ] JWT_SECRET generated (32+ characters)
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [ ] Database credentials secured (use AWS Secrets Manager, Azure Key Vault, or equivalent)
- [ ] Platform API keys secured (never in code or version control)
- [ ] Credential files encrypted using credential manager
- [ ] TLS/SSL certificates obtained and verified
- [ ] Certificate auto-renewal configured

### Customer Success Configuration
- [ ] Health score weights validated (sum to 1.0)
  - USAGE_WEIGHT: 0.35
  - ENGAGEMENT_WEIGHT: 0.25
  - SUPPORT_WEIGHT: 0.15
  - SATISFACTION_WEIGHT: 0.15
  - PAYMENT_WEIGHT: 0.10
- [ ] Churn risk threshold configured (default: 40.0)
- [ ] High-value account threshold configured (default: $50,000)
- [ ] SLA targets configured:
  - P0 (Critical): 1 hour
  - P1 (High): 4 hours
  - P2 (Medium): 24 hours
  - P3 (Low): 72 hours
  - P4 (Planning): 168 hours
- [ ] Onboarding duration configured (default: 90 days)
- [ ] Retention campaign triggers configured:
  - Health score <60
  - Usage decline >30%
  - Support ticket volume increase >50%

### Platform Integrations
- [ ] Zendesk credentials configured (ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_TOKEN)
- [ ] Intercom credentials configured (INTERCOM_ACCESS_TOKEN)
- [ ] Mixpanel credentials configured (MIXPANEL_PROJECT_TOKEN, MIXPANEL_API_SECRET)
- [ ] SendGrid credentials configured (SENDGRID_API_KEY, SENDGRID_FROM_EMAIL)
- [ ] Platform integrations tested (create test ticket, send test email, track test event)
- [ ] Rate limits documented for each platform
- [ ] API timeout settings configured (default: 30s)
- [ ] Retry logic configured (3 retries with exponential backoff)

---

## Infrastructure

### Compute Resources
- [ ] Docker host provisioned (AWS ECS, Azure Container Instances, GCP Cloud Run, or EC2/VM)
- [ ] Instance type selected (minimum 2 vCPU, 4GB RAM)
- [ ] Auto-scaling configured (min: 2 instances, max: 10 instances)
- [ ] Instance health checks configured
- [ ] SSH access restricted to bastion host or VPN

### Database Infrastructure
- [ ] PostgreSQL 16+ provisioned (AWS RDS, Azure Database, GCP Cloud SQL, or self-hosted)
- [ ] Database instance size: minimum db.t3.medium (2 vCPU, 4GB RAM)
- [ ] Multi-AZ deployment enabled for high availability
- [ ] Automated backups configured (daily, 7-day retention minimum)
- [ ] Point-in-time recovery enabled
- [ ] Database encryption at rest enabled
- [ ] Database connection pooling configured (max connections: 100)
- [ ] Database monitoring enabled

### Cache Infrastructure
- [ ] Redis 7+ provisioned (AWS ElastiCache, Azure Cache, GCP Memorystore, or self-hosted)
- [ ] Redis instance size: minimum cache.t3.medium (2 vCPU, 3.09GB RAM)
- [ ] Redis cluster mode evaluated (use for >10k customers)
- [ ] Redis persistence enabled (RDB + AOF)
- [ ] Redis maxmemory policy set (allkeys-lru recommended)
- [ ] Redis connection pooling configured

### Networking
- [ ] Load balancer configured (AWS ALB, Azure Load Balancer, GCP Load Balancer)
- [ ] HTTPS only (HTTP redirects to HTTPS)
- [ ] SSL/TLS certificates installed and verified
- [ ] DNS configured (e.g., cs-mcp.yourcompany.com)
- [ ] CDN configured (CloudFront, Cloudflare, Fastly) - optional but recommended
- [ ] Firewall rules configured:
  - Allow: 443 (HTTPS) from internet
  - Allow: 22 (SSH) from bastion/VPN only
  - Block: 8080 (MCP server port) from internet (use load balancer only)
  - Allow: 5432 (PostgreSQL) from app servers only
  - Allow: 6379 (Redis) from app servers only
- [ ] DDoS protection enabled
- [ ] Rate limiting configured at load balancer (100 requests/minute per IP)

### Container Configuration
- [ ] Docker image built with multi-stage Dockerfile
- [ ] Docker image tagged with version (e.g., `cs-mcp:1.0.0`)
- [ ] Docker image scanned for vulnerabilities (`trivy image cs-mcp:1.0.0`)
- [ ] Docker image pushed to container registry (ECR, ACR, GCR, Docker Hub)
- [ ] Container runs as non-root user (csops UID 1000)
- [ ] Container resource limits set:
  - CPU: 1.0-2.0 vCPU
  - Memory: 2GB-4GB
- [ ] Container health check configured (HTTP GET /health every 30s)
- [ ] Container restart policy set (on-failure)

---

## Monitoring & Logging

### Application Monitoring
- [ ] Prometheus configured and scraping `/metrics` endpoint
- [ ] Prometheus retention set (15 days minimum)
- [ ] Grafana dashboards imported (see `docs/operations/GRAFANA_DASHBOARD.json`)
- [ ] Key metrics tracked:
  - Tool execution rate (requests/sec)
  - Tool execution duration (p50, p95, p99)
  - Error rate (errors/sec)
  - Database query duration
  - Platform API call duration
  - Cache hit rate
  - Memory usage
  - CPU usage

### Logging
- [ ] Structured logging enabled (JSON format)
- [ ] Log aggregation configured (CloudWatch, Stackdriver, ELK stack, Splunk)
- [ ] Log retention policy set (30 days minimum)
- [ ] Log rotation configured (daily or 100MB)
- [ ] Log levels appropriate:
  - Production: INFO or WARNING
  - Staging: DEBUG
- [ ] Sensitive data redacted from logs (passwords, API keys, PII)
- [ ] Audit logging enabled for security events

### Alerting
- [ ] Error alerting configured (PagerDuty, OpsGenie, Slack)
- [ ] Alert thresholds set:
  - Error rate >1% for 5 minutes
  - p95 latency >1s for 5 minutes
  - Database connection pool >80% for 5 minutes
  - Memory usage >85% for 5 minutes
  - Disk space <10% remaining
- [ ] On-call rotation established
- [ ] Alert escalation policy configured
- [ ] Alert runbooks created (see RUNBOOK.md)

### Uptime Monitoring
- [ ] External uptime monitoring configured (Pingdom, UptimeRobot, StatusCake)
- [ ] Health check endpoint monitored (`GET /health`)
- [ ] Check frequency: every 1-5 minutes
- [ ] Alert on 3 consecutive failures
- [ ] Status page configured (optional)

### Database Monitoring
- [ ] Database performance metrics tracked:
  - Query duration (p95, p99)
  - Connection count
  - Cache hit ratio
  - Replication lag (if applicable)
  - Disk I/O
  - Storage usage
- [ ] Slow query log enabled (queries >1s)
- [ ] Database alerts configured:
  - Connection pool >80%
  - Replication lag >5 seconds
  - Storage >80% full

### Backup Monitoring
- [ ] Backup success/failure alerts configured
- [ ] Backup completion time tracked
- [ ] Backup integrity tests scheduled (weekly)
- [ ] Restore procedure tested (quarterly)
- [ ] Backup retention policy enforced (7 daily, 4 weekly, 12 monthly)

---

## Security

### Access Control
- [ ] Server runs as non-root user (csops UID 1000)
- [ ] Principle of least privilege applied to all service accounts
- [ ] IAM roles configured with minimal permissions
- [ ] SSH key-based authentication only (password auth disabled)
- [ ] MFA enabled for all admin accounts
- [ ] Bastion host or VPN required for server access
- [ ] Database credentials rotated regularly (90 days)
- [ ] API keys rotated regularly (90 days)

### Application Security
- [ ] Input validation enabled on all tools
- [ ] SQL injection prevention verified (parameterized queries only)
- [ ] XSS prevention verified (no unescaped user input)
- [ ] Path traversal prevention verified (validate file paths)
- [ ] Rate limiting configured at application level
- [ ] CORS configured appropriately
- [ ] Security headers configured:
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Strict-Transport-Security: max-age=31536000

### Compliance
- [ ] Audit logging enabled for all sensitive operations:
  - User authentication
  - Customer data access
  - Configuration changes
  - Platform integration calls
- [ ] GDPR compliance features enabled (if applicable):
  - Data export functionality
  - Data deletion functionality
  - Consent tracking
  - Data retention policies
- [ ] SOC 2 controls implemented (if applicable)
- [ ] HIPAA controls implemented (if applicable)

### Security Testing
- [ ] Penetration test completed (if required)
- [ ] Security scan results reviewed and approved:
  - Bandit (Python security issues)
  - Safety (dependency vulnerabilities)
  - Trivy (container vulnerabilities)
  - OWASP ZAP (web application vulnerabilities) - optional
- [ ] Vulnerability remediation plan for any findings
- [ ] Security incident response plan documented

---

## Launch

### Pre-Launch Checklist
- [ ] All above sections completed and verified
- [ ] Deployment plan reviewed and approved
- [ ] Rollback plan documented and tested
- [ ] Team notified of deployment schedule
- [ ] Maintenance window scheduled (if downtime required)
- [ ] Customer communication sent (if applicable)

### Deployment Steps
1. [ ] Database migrations applied
   ```bash
   # Run from app server or bastion host
   alembic upgrade head
   ```
2. [ ] Database migration verification
   ```bash
   # Verify all tables created
   psql $DATABASE_URL -c "\dt"
   # Verify all indexes created
   psql $DATABASE_URL -c "\di"
   ```
3. [ ] Docker image deployed
   ```bash
   # Example for ECS
   aws ecs update-service --cluster cs-mcp-prod --service cs-mcp --force-new-deployment
   ```
4. [ ] Container health checks passing
   ```bash
   # Check container health
   docker ps --filter "health=healthy"
   # Or check load balancer target health
   aws elbv2 describe-target-health --target-group-arn $TARGET_GROUP_ARN
   ```
5. [ ] Application startup validation passing
   - Python version check
   - Dependency validation
   - Configuration file validation
   - Security configuration validation
   - Startup health checks (database, Redis, disk, ports)

### Smoke Tests
- [ ] Health endpoint responding (`GET /health` returns 200)
- [ ] Metrics endpoint responding (`GET /metrics` returns Prometheus metrics)
- [ ] Database connectivity verified (check logs for successful connection)
- [ ] Redis connectivity verified (check logs for successful connection)
- [ ] Register test customer
  ```bash
  # Use MCP client or API
  register_client(
    client_id="cs_test_smoketest",
    client_name="Test Company",
    industry="Technology"
  )
  ```
- [ ] Calculate health score for test customer
  ```bash
  calculate_health_score(client_id="cs_test_smoketest")
  ```
- [ ] Create test Zendesk ticket
  ```bash
  handle_support_ticket(
    client_id="cs_test_smoketest",
    subject="Test Ticket",
    description="Smoke test"
  )
  ```
- [ ] Send test email via SendGrid
  ```bash
  send_personalized_email(
    client_id="cs_test_smoketest",
    template="welcome",
    recipient="test@example.com"
  )
  ```
- [ ] Track test event in Mixpanel
  ```bash
  track_usage_engagement(
    client_id="cs_test_smoketest",
    event_name="login",
    properties={"source": "smoke_test"}
  )
  ```
- [ ] MCP client connected successfully (Claude Desktop or API client)
- [ ] Verify test data in database
- [ ] Clean up test data

### Platform Integrations Verification
- [ ] Zendesk integration verified
  - Test ticket created in Zendesk
  - Test ticket retrieved successfully
  - No API errors in logs
- [ ] Intercom integration verified
  - Test message sent successfully
  - Test user created in Intercom
  - No API errors in logs
- [ ] Mixpanel integration verified
  - Test event tracked successfully
  - Event visible in Mixpanel dashboard
  - No API errors in logs
- [ ] SendGrid integration verified
  - Test email sent successfully
  - Email received in inbox
  - No API errors in logs

---

## Post-Launch

### Immediate Monitoring (First 1 Hour)
- [ ] Monitor error rates (target: <1%)
  - Check Grafana dashboard every 5 minutes
  - Review application logs for errors
  - Check Sentry/error tracking for exceptions
- [ ] Monitor performance (p95 latency <1s)
  - Check Prometheus metrics
  - Review slow query log
  - Monitor database connection pool
- [ ] Monitor resource usage
  - CPU usage <70%
  - Memory usage <80%
  - Disk usage not growing unexpectedly
- [ ] Review logs for errors or warnings
  - Application logs
  - Database logs
  - Load balancer logs
  - Platform integration logs
- [ ] Verify all background jobs running (if applicable)

### First 24 Hours
- [ ] Test customer workflows end-to-end
  - Register customer
  - Create onboarding plan
  - Track usage
  - Calculate health score
  - Send email campaign
  - Create support ticket
- [ ] Collect user feedback
  - Check customer support channels
  - Review error reports
  - Monitor social media/community
- [ ] Monitor platform integration usage
  - Check rate limit warnings
  - Verify API call success rates
  - Review webhook processing
- [ ] Schedule first database backup
- [ ] Verify backup completed successfully
- [ ] Test database restore (from backup to staging)

### First Week
- [ ] Conduct post-deployment retrospective
  - What went well?
  - What could be improved?
  - Any incidents or issues?
- [ ] Document lessons learned
- [ ] Update runbook with any new procedures
- [ ] Identify and prioritize any bugs or issues
- [ ] Plan next release cycle
- [ ] Review and adjust monitoring thresholds if needed
- [ ] Conduct security review (check audit logs)
- [ ] Customer success check-in (if applicable)

### Ongoing Operations
- [ ] Weekly health checks (see RUNBOOK.md)
- [ ] Monthly security reviews
- [ ] Quarterly disaster recovery drills
- [ ] Continuous performance optimization
- [ ] Regular dependency updates (security patches)
- [ ] Database maintenance (vacuum, analyze, reindex)

---

## Rollback Plan

If critical issues are discovered post-launch, follow the rollback procedure:

### Rollback Criteria
Rollback immediately if:
- Error rate >5% for 10 minutes
- Data corruption detected
- Security breach detected
- Critical functionality not working
- Performance degradation >2x expected

### Rollback Procedure
1. [ ] Alert team of rollback decision
2. [ ] Stop new deployments
3. [ ] Revert to previous Docker image version
   ```bash
   # Example for ECS
   aws ecs update-service --cluster cs-mcp-prod --service cs-mcp --task-definition cs-mcp:PREVIOUS_VERSION
   ```
4. [ ] Rollback database migrations (if needed)
   ```bash
   alembic downgrade -1  # Or specific revision
   ```
5. [ ] Verify rollback successful
   - Health checks passing
   - Error rate normalized
   - Performance restored
6. [ ] Notify customers (if applicable)
7. [ ] Conduct incident post-mortem
8. [ ] Document root cause and prevention steps

---

## Sign-Off

### Deployment Team Sign-Off
- [ ] Backend Engineer: ________________________ Date: _______
- [ ] DevOps Engineer: ________________________ Date: _______
- [ ] QA Engineer: ______________________________ Date: _______
- [ ] Security Engineer: _______________________ Date: _______

### Stakeholder Approval
- [ ] Engineering Manager: _____________________ Date: _______
- [ ] Product Manager: __________________________ Date: _______
- [ ] CTO/VP Engineering: ______________________ Date: _______

---

## References

- [INSTALLATION.md](./INSTALLATION.md) - Installation guide
- [CONFIGURATION.md](./CONFIGURATION.md) - Configuration reference
- [RUNBOOK.md](./docs/operations/RUNBOOK.md) - Operational procedures
- [CS_MCP_DEVELOPMENT_PLAN.md](./CS_MCP_DEVELOPMENT_PLAN.md) - Development plan

---

**Version History:**
- v1.0.0 (2025-10-10) - Initial production deployment checklist
