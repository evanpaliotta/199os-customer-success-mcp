# ==============================================================================
# Stage 1: Builder - Install dependencies and build packages
# ==============================================================================
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
# gcc: Required for compiling Python packages with C extensions
# postgresql-client: PostgreSQL development headers for psycopg2
# libpq-dev: PostgreSQL client library
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python packages in a virtual environment
# Virtual environment makes it easier to copy only what we need to runtime stage
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ==============================================================================
# Stage 2: Runtime - Minimal production image
# ==============================================================================
FROM python:3.11-slim AS runtime

# Metadata
LABEL maintainer="199|OS Customer Success Team" \
      version="1.0.0" \
      description="199|OS Customer Success MCP Server - Production Ready" \
      security.non-root="true"

# Install only runtime dependencies (no build tools)
# postgresql-client: Needed for health checks and database operations
# tini: Proper init system for signal handling
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    redis-tools \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user (SECURITY: Never run as root in production)
# UID 1000 is standard for non-root users
RUN groupadd -r csops --gid=1000 && \
    useradd -r -g csops --uid=1000 --home-dir=/app --shell=/bin/bash csops

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code with proper ownership
# Use --chown to set ownership during copy (more efficient than separate chown)
COPY --chown=csops:csops . .

# Create necessary directories with proper permissions
RUN mkdir -p logs data credentials config/preferences config/audit_logs && \
    chown -R csops:csops logs data credentials config

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO \
    PORT=8080

# Switch to non-root user (CRITICAL SECURITY REQUIREMENT)
USER csops

# Expose port
EXPOSE 8080

# Health check - Test real server responsiveness
# This health check:
# 1. Tests that the server is listening on port 8080
# 2. Tests database connectivity (PostgreSQL)
# 3. Tests Redis connectivity
# Intervals: check every 30s, timeout after 10s, start after 5s, retry 3 times
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; \
        import sys; \
        import os; \
        # Test 1: Check server is listening \
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); \
        server_ok = sock.connect_ex(('localhost', 8080)) == 0; \
        sock.close(); \
        # Test 2: Check database connectivity \
        import subprocess; \
        db_url = os.getenv('DATABASE_URL', ''); \
        db_ok = True; \
        if db_url: \
            db_ok = subprocess.call(['pg_isready', '-q']) == 0; \
        # Test 3: Check Redis connectivity \
        redis_url = os.getenv('REDIS_URL', ''); \
        redis_ok = True; \
        if redis_url: \
            redis_ok = subprocess.call(['redis-cli', '-u', redis_url, 'ping'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0; \
        # Return 0 if all checks pass, 1 otherwise \
        sys.exit(0 if (server_ok and db_ok and redis_ok) else 1)"

# Use tini as init system for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Run server
CMD ["python", "server.py"]
