# Quick Start: CI/CD Setup

**5-minute guide to activate GitHub Actions CI/CD workflows**

## Prerequisites

- GitHub account
- Docker Hub account
- Codecov account (optional, for coverage badges)

## Steps

### 1. Initialize Git Repository (1 minute)

```bash
cd /Users/evanpaliotta/199os-customer-success-mcp

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit with CI/CD workflows"
```

### 2. Create GitHub Repository (2 minutes)

**Option A: Via GitHub Web UI**
1. Go to https://github.com/new
2. Organization: `199os`
3. Repository name: `customer-success-mcp`
4. Visibility: Public or Private
5. Click "Create repository"

**Option B: Via GitHub CLI**
```bash
gh repo create 199os/customer-success-mcp --public --source=. --remote=origin --push
```

### 3. Push Code (30 seconds)

```bash
git remote add origin git@github.com:199os/customer-success-mcp.git
git branch -M main
git push -u origin main
```

### 4. Configure GitHub Secrets (2 minutes)

Go to: https://github.com/199os/customer-success-mcp/settings/secrets/actions

**Required Secrets:**

1. **CODECOV_TOKEN** (optional for coverage badge):
   - Go to https://codecov.io
   - Sign in with GitHub
   - Add repository
   - Copy token from Settings → Repository Upload Token
   - Add as secret in GitHub

2. **DOCKER_USERNAME**:
   - Your Docker Hub username (e.g., `199os`)

3. **DOCKER_PASSWORD**:
   - Go to https://hub.docker.com/settings/security
   - Click "New Access Token"
   - Name: `github-actions`
   - Permissions: Read, Write, Delete
   - Copy token
   - Add as secret in GitHub

### 5. Create Docker Hub Repository (1 minute)

1. Go to https://hub.docker.com/repositories
2. Click "Create Repository"
3. Name: `customer-success-mcp`
4. Namespace: `199os`
5. Visibility: Public
6. Click "Create"

### 6. Verify Workflows Run (2 minutes)

1. Go to https://github.com/199os/customer-success-mcp/actions
2. You should see workflows running from your push
3. Wait for all checks to complete (2-5 minutes)

### 7. Set Up Pre-commit Hooks (1 minute)

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Done!

Your CI/CD is now active. Every push will trigger:
- ✅ Automated tests (Python 3.10, 3.11, 3.12)
- ✅ Code quality checks (Black, Ruff, mypy)
- ✅ Security scans (Bandit, Safety)
- ✅ Docker image builds
- ✅ Coverage reporting (if Codecov configured)

## Quick Test

Make a change and create a pull request:

```bash
git checkout -b test/verify-ci
echo "# Test CI/CD" >> TEST.md
git add TEST.md
git commit -m "test: Verify CI/CD workflows"
git push -u origin test/verify-ci
```

Then create a PR on GitHub and watch the workflows run!

## Test Commands

### Run Tests Locally

```bash
# Start services
docker-compose up -d postgres redis

# Run tests with coverage
pytest tests/ --cov=src --cov-report=html --cov-fail-under=80 -v

# View coverage
open htmlcov/index.html
```

### Run Linting Locally

```bash
# Format code
black src/ tests/

# Lint
ruff check --fix src/ tests/

# Type check
mypy src/ --ignore-missing-imports
```

### Build Docker Image Locally

```bash
docker build -t cs-mcp:local .
docker run --rm cs-mcp:local python --version
```

## Create First Release

When ready to release v1.0.0:

```bash
git checkout main
git pull origin main
git tag -a v1.0.0 -m "Release v1.0.0: Initial production release"
git push origin v1.0.0
```

This will automatically:
1. Run all tests
2. Build Docker image
3. Push to Docker Hub with tags: `v1.0.0`, `v1.0`, `v1`, `latest`
4. Create GitHub Release
5. Deploy to staging (if configured)

## Need Help?

- **Full Documentation:** `.github/CI_CD_SETUP.md`
- **Testing Guide:** `.github/TESTING_GUIDE.md`
- **Implementation Summary:** `CI_CD_IMPLEMENTATION_SUMMARY.md`

## Badge URLs (for README)

```markdown
[![Tests](https://github.com/199os/customer-success-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/199os/customer-success-mcp/actions/workflows/test.yml)
[![Lint](https://github.com/199os/customer-success-mcp/actions/workflows/lint.yml/badge.svg)](https://github.com/199os/customer-success-mcp/actions/workflows/lint.yml)
[![Build](https://github.com/199os/customer-success-mcp/actions/workflows/build.yml/badge.svg)](https://github.com/199os/customer-success-mcp/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/199os/customer-success-mcp/branch/main/graph/badge.svg)](https://codecov.io/gh/199os/customer-success-mcp)
[![Docker](https://img.shields.io/docker/v/199os/customer-success-mcp?label=docker&sort=semver)](https://hub.docker.com/r/199os/customer-success-mcp)
```

---

**Setup Time:** ~10 minutes
**Status:** Ready to use ✅
