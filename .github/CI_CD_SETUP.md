# CI/CD Setup Guide

This document explains the Continuous Integration and Continuous Deployment (CI/CD) workflows for the Customer Success MCP Server.

## Overview

The project includes 4 GitHub Actions workflows:

1. **test.yml** - Automated testing with coverage reporting
2. **lint.yml** - Code quality and security checks
3. **build.yml** - Docker image building and publishing
4. **deploy.yml** - Staging and production deployments

## Workflows

### 1. Test Workflow (test.yml)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Matrix:**
- Python 3.10, 3.11, 3.12
- PostgreSQL 16 (service container)
- Redis 7 (service container)

**Steps:**
1. Checkout code
2. Set up Python (with pip caching)
3. Install dependencies
4. Configure test environment
5. Run database migrations
6. Run pytest with coverage (minimum 80%)
7. Upload coverage to Codecov (Python 3.11 only)
8. Upload coverage HTML report as artifact

**Environment Variables Required:**
- None (uses service containers)

**Secrets Required:**
- `CODECOV_TOKEN` - For uploading coverage reports

**Coverage Threshold:**
- Minimum: 80%
- Fails build if below threshold

### 2. Lint Workflow (lint.yml)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Steps:**
1. Checkout code
2. Set up Python 3.11
3. Install linting tools (Black, Ruff, mypy)
4. Run Black formatting check
5. Run Ruff linting
6. Run mypy type checking (warning only)
7. Run Bandit security scan (warning only)
8. Run Safety dependency check (warning only)
9. Upload security reports as artifacts

**Environment Variables Required:**
- None

**Secrets Required:**
- None

**Tools:**
- **Black**: Code formatting (enforced)
- **Ruff**: Fast Python linter (enforced)
- **mypy**: Type checking (warning only)
- **Bandit**: Security vulnerability scanner
- **Safety**: Dependency vulnerability checker

### 3. Build Workflow (build.yml)

**Triggers:**
- Push to `main` branch
- Push of tags matching `v*.*.*`
- Pull requests to `main`

**Steps:**
1. Checkout code
2. Set up Docker Buildx
3. Extract Docker metadata (tags, labels)
4. Build Docker image
5. Run Trivy security scan
6. Upload Trivy results to GitHub Security
7. Test Docker image health check
8. Login to Docker Hub (on main/tags only)
9. Push image to Docker Hub (on main/tags only)
10. Generate release notes (on tags only)
11. Create GitHub Release (on tags only)

**Environment Variables Required:**
- `REGISTRY`: docker.io (default)
- `IMAGE_NAME`: 199os/customer-success-mcp

**Secrets Required:**
- `DOCKER_USERNAME` - Docker Hub username
- `DOCKER_PASSWORD` - Docker Hub password or access token
- `GITHUB_TOKEN` - Automatically provided by GitHub

**Docker Tags:**
- `latest` - Latest commit on main branch
- `v1.2.3` - Semantic version from git tag
- `v1.2` - Major.minor version
- `v1` - Major version
- `main` - Main branch builds
- `pr-123` - Pull request builds

**Security Scanning:**
- Trivy scans for CRITICAL and HIGH vulnerabilities
- Results uploaded to GitHub Security tab
- Build does not fail on vulnerabilities (warning only)

### 4. Deploy Workflow (deploy.yml)

**Triggers:**
- Push of tags matching `v*.*.*`
- Manual workflow dispatch

**Environments:**
- **staging** - Automatic deployment, no approval required
- **production** - Manual approval required via GitHub Environments

**Staging Deployment Steps:**
1. Checkout code
2. Deploy to staging environment
3. Wait for deployment readiness
4. Run smoke tests
5. Notify deployment status

**Production Deployment Steps:**
1. Checkout code
2. Manual approval gate (configured in GitHub)
3. Create pre-deployment database backup
4. Deploy to production
5. Wait for deployment readiness
6. Run comprehensive health checks
7. Verify critical workflows
8. Monitor error rates
9. Rollback on failure
10. Send post-deployment notification

**Environment Variables Required:**
- Custom deployment variables (depends on infrastructure)

**Secrets Required:**
- Deployment credentials (AWS, Kubernetes, etc.)
- Notification webhooks (Slack, PagerDuty, etc.)

**Note:** The deploy workflow contains placeholder commands. You must customize it for your specific infrastructure (ECS, Kubernetes, Docker Swarm, etc.).

## Setup Instructions

### 1. GitHub Repository Setup

1. Create a new repository on GitHub
2. Push your code to the repository
3. Enable GitHub Actions in repository settings

### 2. Configure Secrets

Navigate to **Settings → Secrets and variables → Actions** and add:

**Required Secrets:**
- `CODECOV_TOKEN` - Get from https://codecov.io after linking repository
- `DOCKER_USERNAME` - Your Docker Hub username
- `DOCKER_PASSWORD` - Your Docker Hub access token (recommended) or password

**Optional Secrets (for deployment):**
- `AWS_ACCESS_KEY_ID` - If deploying to AWS
- `AWS_SECRET_ACCESS_KEY` - If deploying to AWS
- `KUBE_CONFIG` - If deploying to Kubernetes
- `SLACK_WEBHOOK` - For deployment notifications

### 3. Configure GitHub Environments

For the deploy workflow to work with manual approvals:

1. Go to **Settings → Environments**
2. Create environment: `staging`
   - No protection rules (auto-deploy)
   - Add environment secrets if needed
3. Create environment: `production`
   - Enable "Required reviewers" (add team members)
   - Enable "Wait timer" if desired (e.g., 5 minutes)
   - Add environment secrets

### 4. Configure Codecov

1. Sign up at https://codecov.io
2. Link your GitHub repository
3. Copy the upload token
4. Add as `CODECOV_TOKEN` secret in GitHub

### 5. Configure Docker Hub

1. Log in to https://hub.docker.com
2. Create a repository: `199os/customer-success-mcp`
3. Generate an access token:
   - Account Settings → Security → New Access Token
   - Scope: Read, Write, Delete
4. Add username and token as GitHub secrets

### 6. Install Pre-commit Hooks

For local development:

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

## Running Tests Locally

### Run All Tests

```bash
# Start PostgreSQL and Redis (docker-compose)
docker-compose up -d postgres redis

# Run tests with coverage
pytest tests/ \
  --cov=src \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=80 \
  -v

# View coverage report
open htmlcov/index.html
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_core_system_tools.py -v

# Specific test
pytest tests/unit/test_core_system_tools.py::test_register_client -v
```

### Run Linting Locally

```bash
# Format code
black src/ tests/

# Lint code
ruff check --fix src/ tests/

# Type check
mypy src/ --ignore-missing-imports

# Security scan
bandit -r src/ -ll

# Dependency check
safety check
```

## Docker Build Locally

```bash
# Build image
docker build -t cs-mcp:local .

# Run image
docker run --rm \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e REDIS_URL=redis://host:6379/0 \
  -p 8080:8080 \
  cs-mcp:local

# Scan image
docker scan cs-mcp:local

# Or use Trivy
trivy image cs-mcp:local
```

## Workflow Badges

Add these badges to your README.md:

```markdown
[![Tests](https://github.com/199os/customer-success-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/199os/customer-success-mcp/actions/workflows/test.yml)
[![Lint](https://github.com/199os/customer-success-mcp/actions/workflows/lint.yml/badge.svg)](https://github.com/199os/customer-success-mcp/actions/workflows/lint.yml)
[![Build](https://github.com/199os/customer-success-mcp/actions/workflows/build.yml/badge.svg)](https://github.com/199os/customer-success-mcp/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/199os/customer-success-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/199os/customer-success-mcp)
[![Docker Image](https://img.shields.io/docker/v/199os/customer-success-mcp?label=docker&sort=semver)](https://hub.docker.com/r/199os/customer-success-mcp)
```

## Release Process

### 1. Prepare Release

```bash
# Ensure main branch is up to date
git checkout main
git pull origin main

# Ensure all tests pass
pytest tests/ --cov=src --cov-fail-under=80

# Ensure linting passes
black --check src/ tests/
ruff check src/ tests/
```

### 2. Create Release Tag

```bash
# Create and push tag (semantic versioning)
git tag -a v1.0.0 -m "Release v1.0.0: Initial production release"
git push origin v1.0.0
```

### 3. Automated Release Process

Once the tag is pushed, GitHub Actions will automatically:

1. Run all tests (test.yml)
2. Run all linting checks (lint.yml)
3. Build Docker image (build.yml)
4. Scan image for vulnerabilities (Trivy)
5. Push image to Docker Hub with tags: `v1.0.0`, `v1.0`, `v1`, `latest`
6. Create GitHub Release with auto-generated release notes
7. Deploy to staging (deploy.yml)
8. Wait for manual approval
9. Deploy to production (after approval)

### 4. Monitor Deployment

1. Check GitHub Actions logs
2. Verify Docker image published: https://hub.docker.com/r/199os/customer-success-mcp
3. Check GitHub Release created
4. Monitor staging deployment
5. Approve production deployment
6. Monitor production health checks

## Troubleshooting

### Tests Failing in CI but Passing Locally

1. Check Python version (CI runs 3.10, 3.11, 3.12)
2. Check database connection (CI uses service containers)
3. Check environment variables
4. Check for timing issues in async tests
5. Review CI logs for specific errors

### Docker Build Failing

1. Check Dockerfile syntax
2. Verify all files exist (check .dockerignore)
3. Check build context size
4. Review Docker build logs
5. Test build locally first

### Codecov Upload Failing

1. Verify `CODECOV_TOKEN` secret is set
2. Check coverage.xml file is generated
3. Review Codecov upload logs
4. Verify repository is linked in Codecov

### Deployment Failing

1. Check deployment credentials (secrets)
2. Verify target environment is accessible
3. Check health check endpoints
4. Review deployment logs
5. Verify image was pushed to Docker Hub

## Best Practices

1. **Always run tests locally before pushing**
2. **Use pre-commit hooks to catch issues early**
3. **Keep workflows DRY** - reuse steps via composite actions if needed
4. **Monitor workflow run times** - optimize if builds take >10 minutes
5. **Review security scan results** - don't ignore vulnerabilities
6. **Test deployment process in staging first**
7. **Document custom deployment steps** - update deploy.yml
8. **Use semantic versioning** - v1.0.0, not v1
9. **Write meaningful commit messages** - they appear in releases
10. **Review and approve production deployments promptly**

## Monitoring

### GitHub Actions Dashboard

- View all workflow runs: https://github.com/199os/customer-success-mcp/actions
- Filter by workflow, branch, or status
- Download logs for debugging
- Re-run failed workflows

### Codecov Dashboard

- View coverage reports: https://codecov.io/gh/199os/customer-success-mcp
- Track coverage trends over time
- Identify uncovered code
- Review coverage on pull requests

### Docker Hub Dashboard

- View images: https://hub.docker.com/r/199os/customer-success-mcp
- Check image sizes
- Review pull statistics
- Manage tags

## Support

For issues with CI/CD workflows:

1. Check GitHub Actions logs
2. Review this documentation
3. Open an issue in the repository
4. Contact DevOps team

---

**Last Updated:** October 10, 2025
