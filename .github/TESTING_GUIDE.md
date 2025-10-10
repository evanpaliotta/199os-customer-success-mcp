# Testing Guide

Quick reference for running tests in the Customer Success MCP Server.

## Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Start service containers (PostgreSQL + Redis)
docker-compose up -d postgres redis

# Or use docker-compose.test.yml if available
docker-compose -f docker-compose.test.yml up -d
```

## Test Commands

### Run All Tests

```bash
pytest tests/
```

### Run Tests with Coverage

```bash
pytest tests/ \
  --cov=src \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=80 \
  -v
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific category
pytest tests/unit/test_core_system_tools.py -v

# Specific test
pytest tests/unit/test_core_system_tools.py::test_register_client -v
```

### Run Tests in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run with 4 workers
pytest tests/ -n 4
```

### Run Tests with Different Output Formats

```bash
# Verbose output
pytest tests/ -v

# Very verbose (show print statements)
pytest tests/ -vv -s

# Quiet output (only summary)
pytest tests/ -q

# Show only failed tests
pytest tests/ --tb=short

# Show failed tests with full traceback
pytest tests/ --tb=long
```

### Coverage Reports

```bash
# HTML report (interactive)
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Terminal report
pytest tests/ --cov=src --cov-report=term-missing

# XML report (for Codecov)
pytest tests/ --cov=src --cov-report=xml

# All formats
pytest tests/ \
  --cov=src \
  --cov-report=html \
  --cov-report=xml \
  --cov-report=term-missing
```

## Test Environment Configuration

### Environment Variables

```bash
# Create test .env file
cp .env.example .env.test

# Set test-specific values
export DATABASE_URL=postgresql://csops_test:test_password@localhost:5432/cs_mcp_test
export REDIS_URL=redis://localhost:6379/0
export ENVIRONMENT=test
export LOG_LEVEL=DEBUG
```

### Database Setup

```bash
# Create test database
createdb cs_mcp_test

# Run migrations
alembic upgrade head

# Or use pytest fixtures that handle this automatically
```

## Test Debugging

### Run Tests in Debug Mode

```bash
# Stop on first failure
pytest tests/ -x

# Stop after N failures
pytest tests/ --maxfail=3

# Enter debugger on failure
pytest tests/ --pdb

# Show local variables on failure
pytest tests/ -l
```

### Test a Specific Scenario

```bash
# Run only tests matching pattern
pytest tests/ -k "test_register"

# Run tests with specific marker
pytest tests/ -m "integration"

# Skip slow tests
pytest tests/ -m "not slow"
```

## Coverage Analysis

### Check Coverage by Module

```bash
pytest tests/ --cov=src --cov-report=term-missing

# Example output:
# Name                                    Stmts   Miss  Cover   Missing
# ---------------------------------------------------------------------
# src/__init__.py                            0      0   100%
# src/tools/core_system_tools.py           123     12    90%   45-48, 89-92
# src/models/customer_models.py            200      5    98%   123, 156-159
# ---------------------------------------------------------------------
# TOTAL                                   1234    123    90%
```

### Find Uncovered Lines

```bash
# Generate HTML report and open
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html

# Navigate to specific file to see uncovered lines highlighted in red
```

### Coverage Threshold

```bash
# Fail if coverage below 80%
pytest tests/ --cov=src --cov-fail-under=80

# Fail if coverage below 90%
pytest tests/ --cov=src --cov-fail-under=90
```

## Performance Testing

### Measure Test Duration

```bash
# Show slowest 10 tests
pytest tests/ --durations=10

# Show all test durations
pytest tests/ --durations=0
```

### Profile Tests

```bash
# Install pytest-profiling
pip install pytest-profiling

# Profile test execution
pytest tests/ --profile

# Generate SVG profile
pytest tests/ --profile-svg
```

## Continuous Testing

### Watch Mode

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file change
ptw tests/ src/
```

### Test Coverage Watch

```bash
# Run tests with coverage on file change
ptw tests/ src/ -- --cov=src --cov-report=term-missing
```

## CI/CD Integration

### Run Tests Like CI

```bash
# Exact command from GitHub Actions
pytest tests/ \
  --cov=src \
  --cov-report=xml \
  --cov-report=html \
  --cov-report=term-missing \
  --cov-fail-under=80 \
  -v \
  --tb=short \
  --maxfail=5
```

### Generate Coverage XML for Codecov

```bash
pytest tests/ --cov=src --cov-report=xml
# Uploads coverage.xml to Codecov in CI
```

## Common Test Patterns

### Testing Async Functions

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await my_async_function()
    assert result == expected
```

### Using Fixtures

```python
import pytest

@pytest.fixture
def sample_customer():
    return {
        "client_id": "test-001",
        "company_name": "Test Corp"
    }

def test_with_fixture(sample_customer):
    assert sample_customer["client_id"] == "test-001"
```

### Mocking External APIs

```python
from unittest.mock import Mock, patch

def test_with_mock():
    with patch('src.integrations.zendesk_client.ZendeskClient') as mock_client:
        mock_client.return_value.create_ticket.return_value = {"id": 123}
        result = create_support_ticket()
        assert result["ticket_id"] == 123
```

### Database Tests

```python
import pytest

@pytest.fixture
def db_session():
    # Setup test database
    session = create_test_session()
    yield session
    # Cleanup
    session.rollback()
    session.close()

def test_database_operation(db_session):
    customer = Customer(client_id="test-001")
    db_session.add(customer)
    db_session.commit()

    retrieved = db_session.query(Customer).filter_by(client_id="test-001").first()
    assert retrieved is not None
```

## Troubleshooting

### Tests Failing with Database Errors

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check database connection
psql -U csops_test -d cs_mcp_test -h localhost

# Reset test database
dropdb cs_mcp_test && createdb cs_mcp_test
alembic upgrade head
```

### Tests Failing with Redis Errors

```bash
# Check if Redis is running
docker ps | grep redis

# Test Redis connection
redis-cli -h localhost -p 6379 ping
```

### Import Errors

```bash
# Ensure src/ is in Python path
export PYTHONPATH="${PYTHONPATH}:${PWD}"

# Or install package in development mode
pip install -e .
```

### Slow Tests

```bash
# Identify slow tests
pytest tests/ --durations=10

# Skip slow tests during development
pytest tests/ -m "not slow"

# Use faster database (SQLite for unit tests)
export DATABASE_URL=sqlite:///test.db
```

## Best Practices

1. **Write Tests First** (TDD)
   ```bash
   # Write test
   # Run test (should fail)
   pytest tests/unit/test_new_feature.py
   # Implement feature
   # Run test (should pass)
   pytest tests/unit/test_new_feature.py
   ```

2. **Test Coverage Goals**
   - Unit tests: >90% coverage
   - Integration tests: >80% coverage
   - Overall: >80% coverage

3. **Test Organization**
   ```
   tests/
   ├── unit/           # Fast, isolated tests
   ├── integration/    # Tests with external dependencies
   └── e2e/           # End-to-end workflow tests
   ```

4. **Naming Conventions**
   - Test files: `test_*.py`
   - Test functions: `test_*`
   - Test classes: `Test*`

5. **Fast Feedback Loop**
   ```bash
   # Run only changed tests
   pytest tests/ --lf  # last failed
   pytest tests/ --ff  # failed first
   ```

## Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Codecov Documentation](https://docs.codecov.io/)

---

**Last Updated:** October 10, 2025
