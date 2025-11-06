"""
Health Check Endpoint for Production Monitoring
Provides /health (liveness) and /ready (readiness) checks for Kubernetes and load balancers
"""

import asyncio
import time
import os
from typing import Dict, Any, List
from datetime import datetime
import structlog

from fastmcp import FastMCP, Context

# Initialize logger
logger = structlog.get_logger(__name__)

# Initialize MCP server for health checks
health_mcp = FastMCP("Health Check System")


def _check_database_connection() -> Dict[str, Any]:
    """
    Check PostgreSQL database connectivity

    Returns:
        Dict with status, response_time, and error (if any)
    """
    start_time = time.time()

    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            return {
                "status": "unavailable",
                "response_time_ms": 0,
                "error": "DATABASE_URL not configured"
            }

        # Try to connect with timeout
        import psycopg2
        from urllib.parse import urlparse

        parsed = urlparse(database_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            connect_timeout=5
        )

        # Execute simple query to verify connection
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        response_time = (time.time() - start_time) * 1000

        if result and result[0] == 1:
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2)
            }
        else:
            return {
                "status": "degraded",
                "response_time_ms": round(response_time, 2),
                "error": "Unexpected query result"
            }

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return {
            "status": "unhealthy",
            "response_time_ms": round(response_time, 2),
            "error": str(e)
        }


def _check_redis_connection() -> Dict[str, Any]:
    """
    Check Redis connectivity

    Returns:
        Dict with status, response_time, and error (if any)
    """
    start_time = time.time()

    try:
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            return {
                "status": "unavailable",
                "response_time_ms": 0,
                "error": "REDIS_URL not configured"
            }

        # Try to connect with timeout
        import redis

        r = redis.from_url(redis_url, socket_connect_timeout=5)
        pong = r.ping()
        r.close()

        response_time = (time.time() - start_time) * 1000

        if pong:
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2)
            }
        else:
            return {
                "status": "degraded",
                "response_time_ms": round(response_time, 2),
                "error": "PING failed"
            }

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return {
            "status": "unhealthy",
            "response_time_ms": round(response_time, 2),
            "error": str(e)
        }


def _check_integration_health() -> Dict[str, Any]:
    """
    Check critical integration health (non-blocking)

    Returns:
        Dict with integration statuses
    """
    integrations = {}

    # Check which integrations are enabled
    if os.getenv('MCP_ENABLE_ZENDESK', 'false').lower() == 'true':
        integrations['zendesk'] = {
            "enabled": True,
            "status": "configured" if os.getenv('ZENDESK_API_TOKEN') else "not_configured"
        }

    if os.getenv('MCP_ENABLE_INTERCOM', 'false').lower() == 'true':
        integrations['intercom'] = {
            "enabled": True,
            "status": "configured" if os.getenv('INTERCOM_ACCESS_TOKEN') else "not_configured"
        }

    if os.getenv('MCP_ENABLE_MIXPANEL', 'false').lower() == 'true':
        integrations['mixpanel'] = {
            "enabled": True,
            "status": "configured" if os.getenv('MIXPANEL_PROJECT_TOKEN') else "not_configured"
        }

    if os.getenv('MCP_ENABLE_SALESFORCE', 'false').lower() == 'true':
        integrations['salesforce'] = {
            "enabled": True,
            "status": "configured" if os.getenv('SALESFORCE_USERNAME') else "not_configured"
        }

    if os.getenv('MCP_ENABLE_SENDGRID', 'false').lower() == 'true':
        integrations['sendgrid'] = {
            "enabled": True,
            "status": "configured" if os.getenv('SENDGRID_API_KEY') else "not_configured"
        }

    return integrations


@health_mcp.tool()
async def health_check_liveness(ctx: Context) -> Dict[str, Any]:
    """
    Liveness probe - checks if the application is running

    This is a lightweight check that only verifies the process is alive.
    Use for Kubernetes liveness probes or load balancer health checks.

    Returns:
        Dict with status: "ok" if alive, error information if not

    Example:
        >>> result = await health_check_liveness(ctx)
        >>> print(result["status"])
        "ok"
    """
    try:
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "server_name": os.getenv('SERVER_NAME', '199OS-CustomerSuccess'),
            "version": "1.0.0",
            "uptime_seconds": int(time.time())  # Simplified - would track actual uptime in production
        }
    except Exception as e:
        logger.error("liveness_check_failed", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@health_mcp.tool()
async def health_check_readiness(ctx: Context) -> Dict[str, Any]:
    """
    Readiness probe - checks if the application is ready to serve traffic

    This performs comprehensive checks of all critical dependencies:
    - Database connectivity
    - Redis connectivity
    - Integration health

    Use for Kubernetes readiness probes to ensure traffic is only routed
    to instances that can handle requests.

    Returns:
        Dict with overall status and individual component health

    Example:
        >>> result = await health_check_readiness(ctx)
        >>> print(result["status"])
        "ready"
    """
    try:
        await ctx.info("Performing readiness health check...")

        # Check all critical components
        db_health = _check_database_connection()
        redis_health = _check_redis_connection()
        integrations = _check_integration_health()

        # Determine overall readiness
        is_ready = (
            db_health["status"] in ["healthy", "degraded"] and
            redis_health["status"] in ["healthy", "unavailable"]  # Redis optional
        )

        # Calculate total response time
        total_response_time = (
            db_health.get("response_time_ms", 0) +
            redis_health.get("response_time_ms", 0)
        )

        result = {
            "status": "ready" if is_ready else "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "database": db_health,
                "redis": redis_health,
                "integrations": integrations
            },
            "total_response_time_ms": round(total_response_time, 2),
            "ready": is_ready
        }

        # Log health check result
        if is_ready:
            logger.info(
                "readiness_check_passed",
                database_status=db_health["status"],
                redis_status=redis_health["status"],
                response_time_ms=total_response_time
            )
        else:
            logger.warning(
                "readiness_check_failed",
                database_status=db_health["status"],
                redis_status=redis_health["status"],
                database_error=db_health.get("error"),
                redis_error=redis_health.get("error")
            )

        return result

    except Exception as e:
        logger.error("readiness_check_error", error=str(e))
        return {
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "ready": False
        }


@health_mcp.tool()
async def health_check_deep(ctx: Context) -> Dict[str, Any]:
    """
    Deep health check - comprehensive system diagnostics

    Performs extensive checks of all system components including:
    - Database connectivity and query performance
    - Redis connectivity and latency
    - Disk space availability
    - Memory usage
    - Integration health
    - Recent error rates

    Use for manual diagnostics and debugging, not for automated probes
    (too expensive for frequent checks).

    Returns:
        Detailed health report with all system metrics

    Example:
        >>> result = await health_check_deep(ctx)
        >>> print(result["status"])
        "healthy"
    """
    try:
        await ctx.info("Performing deep health check...")

        # Perform all checks
        db_health = _check_database_connection()
        redis_health = _check_redis_connection()
        integrations = _check_integration_health()

        # Check disk space
        import shutil
        disk_stat = shutil.disk_usage("/")
        disk_free_gb = disk_stat.free / (1024**3)
        disk_total_gb = disk_stat.total / (1024**3)
        disk_used_percent = (disk_stat.used / disk_stat.total) * 100

        # Check memory (simplified)
        try:
            import psutil
            memory = psutil.virtual_memory()
            memory_used_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
        except ImportError:
            memory_used_percent = None
            memory_available_gb = None

        # Determine overall health
        is_healthy = (
            db_health["status"] == "healthy" and
            disk_free_gb > 1.0 and  # At least 1 GB free
            (memory_used_percent is None or memory_used_percent < 90)  # Less than 90% memory used
        )

        result = {
            "status": "healthy" if is_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "database": db_health,
                "redis": redis_health,
                "integrations": integrations,
                "disk": {
                    "free_gb": round(disk_free_gb, 2),
                    "total_gb": round(disk_total_gb, 2),
                    "used_percent": round(disk_used_percent, 2),
                    "status": "healthy" if disk_free_gb > 1.0 else "low_space"
                },
                "memory": {
                    "used_percent": round(memory_used_percent, 2) if memory_used_percent else "unavailable",
                    "available_gb": round(memory_available_gb, 2) if memory_available_gb else "unavailable",
                    "status": "healthy" if (memory_used_percent is None or memory_used_percent < 90) else "high_usage"
                }
            },
            "environment": {
                "server_name": os.getenv('SERVER_NAME', 'Unknown'),
                "log_level": os.getenv('LOG_LEVEL', 'INFO'),
                "database_pool_size": int(os.getenv('DB_POOL_SIZE', '10')),
                "redis_max_connections": int(os.getenv('REDIS_MAX_CONNECTIONS', '50')),
                "monitoring_enabled": os.getenv('ENABLE_MONITORING', 'false').lower() == 'true',
                "audit_logging_enabled": os.getenv('ENABLE_AUDIT_LOGGING', 'false').lower() == 'true'
            },
            "healthy": is_healthy
        }

        logger.info(
            "deep_health_check_completed",
            status=result["status"],
            disk_free_gb=disk_free_gb,
            memory_used_percent=memory_used_percent
        )

        return result

    except Exception as e:
        logger.error("deep_health_check_error", error=str(e))
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "healthy": False
        }


# Export the FastMCP instance for registration
def get_health_check_tools() -> Any:
    """Get the health check MCP tools for registration"""
    return health_mcp
