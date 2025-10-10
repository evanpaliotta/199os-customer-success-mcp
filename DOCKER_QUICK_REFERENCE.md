# Docker Quick Reference

## Quick Start

```bash
# 1. Start Docker Desktop (if not running)
open -a Docker

# 2. Verify Docker improvements
./verify_docker_improvements.sh

# 3. Start all services
docker-compose up -d

# 4. Check health status
docker-compose ps

# 5. View logs
docker-compose logs -f customer-success-mcp
```

---

## Common Commands

### Building

```bash
# Build production image
docker build -t cs-mcp:production .

# Build with no cache (clean build)
docker build --no-cache -t cs-mcp:production .

# Check image size
docker images cs-mcp:production
```

### Running

```bash
# Start services in background
docker-compose up -d

# Start services with logs
docker-compose up

# Stop services
docker-compose down

# Restart single service
docker-compose restart customer-success-mcp
```

### Verification

```bash
# Check who runs the container
docker run --rm cs-mcp:production whoami
# Expected: csops

# Check UID
docker run --rm cs-mcp:production id -u
# Expected: 1000

# Verify no build tools
docker run --rm cs-mcp:production which gcc
# Expected: not found

# List installed packages
docker run --rm cs-mcp:production pip list
```

### Health Checks

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' 199os-cs-mcp

# View health check logs
docker inspect --format='{{json .State.Health}}' 199os-cs-mcp | jq

# Manual health check
docker exec 199os-cs-mcp python -c "import socket; sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); result = sock.connect_ex(('localhost', 8080)); sock.close(); exit(0 if result == 0 else 1)"
```

### Logs

```bash
# All services
docker-compose logs -f

# Single service
docker-compose logs -f customer-success-mcp

# Last 100 lines
docker-compose logs --tail=100 customer-success-mcp

# With timestamps
docker-compose logs -f -t customer-success-mcp
```

### Debugging

```bash
# Enter container shell
docker exec -it 199os-cs-mcp /bin/bash

# Check environment variables
docker exec 199os-cs-mcp env

# Test database connection
docker exec 199os-cs-mcp pg_isready -h postgres -U postgres

# Test Redis connection
docker exec 199os-cs-mcp redis-cli -h redis -a password ping

# Check running processes
docker exec 199os-cs-mcp ps aux
```

### Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove old images
docker image prune -f

# Full cleanup (careful!)
docker system prune -a
```

---

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs customer-success-mcp

# Check health
docker-compose ps

# Verify dependencies
docker-compose ps postgres redis
```

### Health check failing

```bash
# Check what's failing
docker inspect --format='{{json .State.Health}}' 199os-cs-mcp | jq

# Test server manually
docker exec 199os-cs-mcp curl -f http://localhost:8080 || echo "Server not responding"

# Test database
docker exec 199os-cs-mcp pg_isready -h postgres -U postgres

# Test Redis
docker exec 199os-cs-mcp redis-cli -h redis -a password ping
```

### Permission errors

```bash
# Check file ownership
docker exec 199os-cs-mcp ls -la /app/logs

# Fix permissions on host
sudo chown -R $(whoami):$(whoami) logs data config credentials

# Verify container user
docker exec 199os-cs-mcp id
```

### Database connection issues

```bash
# Check PostgreSQL is healthy
docker-compose ps postgres

# Test connection
docker exec 199os-cs-mcp pg_isready -h postgres -U postgres

# View PostgreSQL logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d
```

### Out of memory

```bash
# Check resource usage
docker stats

# Increase limits in docker-compose.yml
# Under deploy.resources.limits
memory: 4G  # Increase from 2G

# Restart services
docker-compose down
docker-compose up -d
```

---

## Performance Monitoring

```bash
# Real-time resource usage
docker stats 199os-cs-mcp

# Container processes
docker top 199os-cs-mcp

# Disk usage
docker system df

# Image layers
docker history cs-mcp:production
```

---

## Security

```bash
# Scan for vulnerabilities
docker scan cs-mcp:production

# Or use Trivy
trivy image cs-mcp:production

# Check running as non-root
docker exec 199os-cs-mcp whoami

# Verify no capabilities
docker inspect --format='{{.HostConfig.CapDrop}}' 199os-cs-mcp
```

---

## Production Deployment

```bash
# Tag for registry
docker tag cs-mcp:production your-registry/cs-mcp:1.0.0

# Push to registry
docker push your-registry/cs-mcp:1.0.0

# Pull on production server
docker pull your-registry/cs-mcp:1.0.0

# Run with production config
docker-compose -f docker-compose.prod.yml up -d
```

---

## File Locations

### Dockerfile
`/Users/evanpaliotta/199os-customer-success-mcp/Dockerfile`
- Multi-stage build configuration
- Security settings
- Health check definition

### docker-compose.yml
`/Users/evanpaliotta/199os-customer-success-mcp/docker-compose.yml`
- Service orchestration
- Health checks
- Resource limits
- Logging configuration

### .dockerignore
`/Users/evanpaliotta/199os-customer-success-mcp/.dockerignore`
- Excludes files from build context
- Reduces image size

### Verification Script
`/Users/evanpaliotta/199os-customer-success-mcp/verify_docker_improvements.sh`
- Automated testing script
- Verifies all improvements

### Summary Documentation
`/Users/evanpaliotta/199os-customer-success-mcp/DOCKER_UPGRADE_SUMMARY.md`
- Complete upgrade documentation
- Before/after comparison
- Testing instructions

---

## Key Metrics

### Target Metrics
- Image size: <500MB
- Build time: <5 min
- Container startup: <5s
- Health check: 30s interval
- Memory (idle): <512MB
- CPU (idle): <0.5

### Check Metrics

```bash
# Image size
docker images cs-mcp:production --format "{{.Size}}"

# Build time
time docker build -t cs-mcp:production .

# Container startup time
time docker-compose up -d

# Memory usage
docker stats 199os-cs-mcp --no-stream --format "{{.MemUsage}}"

# CPU usage
docker stats 199os-cs-mcp --no-stream --format "{{.CPUPerc}}"
```

---

## Environment Variables

Key environment variables for docker-compose.yml:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@postgres:5432/cs_mcp_db

# Redis
REDIS_URL=redis://:password@redis:6379/0

# Application
LOG_LEVEL=INFO
PORT=8080
PYTHONUNBUFFERED=1

# Security (set in .env file, not in docker-compose.yml)
ENCRYPTION_KEY=<generate-32-byte-key>
JWT_SECRET=<generate-secret>
```

---

## Next Steps After Verification

1. Review `DOCKER_UPGRADE_SUMMARY.md` for complete details
2. Test health checks: `docker-compose ps`
3. Verify logs: `docker-compose logs -f`
4. Proceed to next milestone: Platform Integrations (Week 3-4)
5. Continue with CS_MCP_DEVELOPMENT_PLAN.md

---

## Support

For issues or questions:
- Check `DOCKER_UPGRADE_SUMMARY.md`
- Review logs: `docker-compose logs`
- File GitHub issue with verification script output
- Contact: 199|OS Customer Success Team
