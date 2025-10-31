"""
Performance Monitoring Module for Customer Success MCP
Provides Prometheus metrics, performance decorators, and monitoring capabilities
"""

import time
import functools
import asyncio
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from datetime import datetime
from collections import defaultdict
from enum import Enum
import structlog

# Prometheus metrics imports
try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Summary,
        generate_latest,
        CONTENT_TYPE_LATEST,
        CollectorRegistry,
        start_http_server
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Provide mock classes for when prometheus_client is not installed
    class Counter:
        def __init__(self, *args, **kwargs) -> Any: pass
        def inc(self, *args, **kwargs) -> Any: pass
        def labels(self, **kwargs) -> Any: return self

    class Histogram:
        def __init__(self, *args, **kwargs) -> Any: pass
        def observe(self, *args, **kwargs) -> Any: pass
        def labels(self, **kwargs) -> Any: return self
        def time(self) -> Any: return self
        def __enter__(self) -> Any: return self
        def __exit__(self, *args) -> Any: pass

    class Gauge:
        def __init__(self, *args, **kwargs) -> Any: pass
        def set(self, *args, **kwargs) -> Any: pass
        def inc(self, *args, **kwargs) -> Any: pass
        def dec(self, *args, **kwargs) -> Any: pass
        def labels(self, **kwargs) -> Any: return self

    class Summary:
        def __init__(self, *args, **kwargs) -> Any: pass
        def observe(self, *args, **kwargs) -> Any: pass
        def labels(self, **kwargs) -> Any: return self

logger = structlog.get_logger(__name__)

T = TypeVar('T')

# ============================================================================
# Performance Thresholds & Configuration
# ============================================================================

class PerformanceThreshold:
    """Performance threshold configuration"""
    SLOW_OPERATION_WARNING_MS = 1000    # 1 second warning
    SLOW_OPERATION_ERROR_MS = 5000      # 5 second error
    DB_QUERY_WARNING_MS = 50            # 50ms for DB queries
    DB_QUERY_ERROR_MS = 200             # 200ms for DB queries
    API_CALL_WARNING_MS = 2000          # 2 seconds for API calls
    API_CALL_ERROR_MS = 10000           # 10 seconds for API calls
    HEALTH_SCORE_TARGET_MS = 100        # 100ms for health score calculation
    CACHE_TTL_SECONDS = 3600             # 1 hour default cache TTL

# ============================================================================
# Prometheus Metrics Definition
# ============================================================================

# Tool execution metrics
tool_execution_counter = Counter(
    'cs_mcp_tool_execution_total',
    'Total number of tool executions',
    ['tool_name', 'status']
)

tool_execution_duration = Histogram(
    'cs_mcp_tool_execution_duration_seconds',
    'Tool execution duration in seconds',
    ['tool_name'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
)

# Database query metrics
database_query_counter = Counter(
    'cs_mcp_database_query_total',
    'Total number of database queries',
    ['query_type']
)

database_query_duration = Histogram(
    'cs_mcp_database_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1)
)

# Platform API call metrics
platform_api_counter = Counter(
    'cs_mcp_platform_api_calls_total',
    'Total number of platform API calls',
    ['integration', 'endpoint', 'status']
)

platform_api_duration = Histogram(
    'cs_mcp_platform_api_duration_seconds',
    'Platform API call duration in seconds',
    ['integration', 'endpoint'],
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10, 15, 30)
)

# Health score calculation metrics
health_score_calculation_duration = Histogram(
    'cs_mcp_health_score_calculation_seconds',
    'Health score calculation duration in seconds',
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1)
)

# Cache metrics
cache_hit_counter = Counter(
    'cs_mcp_cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

cache_miss_counter = Counter(
    'cs_mcp_cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

# Error metrics
error_counter = Counter(
    'cs_mcp_errors_total',
    'Total number of errors',
    ['error_type']
)

# Active connections/processes gauge
active_connections = Gauge(
    'cs_mcp_active_connections',
    'Number of active connections'
)

# Memory usage gauge
memory_usage_bytes = Gauge(
    'cs_mcp_memory_usage_bytes',
    'Current memory usage in bytes'
)

# ============================================================================
# Performance Monitoring Decorators
# ============================================================================

def monitor_tool_execution(tool_name: Optional[str] = None) -> Any:
    """
    Decorator to monitor tool execution performance.

    Usage:
        @monitor_tool_execution()
        async def my_tool(ctx, ...) -> Any:
            ...

        @monitor_tool_execution(tool_name="custom_name")
        async def my_tool(ctx, ...) -> Any:
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        actual_tool_name = tool_name or func.__name__

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            status = "success"

            try:
                # Start monitoring
                active_connections.inc()

                # Execute function
                result = await func(*args, **kwargs)

                return result

            except Exception as e:
                status = "error"
                error_counter.labels(error_type=type(e).__name__).inc()
                logger.error(
                    "Tool execution failed",
                    tool=actual_tool_name,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise

            finally:
                # Calculate duration
                duration = time.time() - start_time
                duration_ms = duration * 1000

                # Record metrics
                tool_execution_counter.labels(
                    tool_name=actual_tool_name,
                    status=status
                ).inc()

                tool_execution_duration.labels(
                    tool_name=actual_tool_name
                ).observe(duration)

                # Log slow operations
                if duration_ms > PerformanceThreshold.SLOW_OPERATION_ERROR_MS:
                    logger.error(
                        "Slow tool execution detected",
                        tool=actual_tool_name,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=PerformanceThreshold.SLOW_OPERATION_ERROR_MS
                    )
                elif duration_ms > PerformanceThreshold.SLOW_OPERATION_WARNING_MS:
                    logger.warning(
                        "Tool execution slower than expected",
                        tool=actual_tool_name,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=PerformanceThreshold.SLOW_OPERATION_WARNING_MS
                    )
                else:
                    logger.debug(
                        "Tool execution completed",
                        tool=actual_tool_name,
                        duration_ms=round(duration_ms, 2),
                        status=status
                    )

                # Cleanup
                active_connections.dec()

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            status = "success"

            try:
                # Start monitoring
                active_connections.inc()

                # Execute function
                result = func(*args, **kwargs)

                return result

            except Exception as e:
                status = "error"
                error_counter.labels(error_type=type(e).__name__).inc()
                logger.error(
                    "Tool execution failed",
                    tool=actual_tool_name,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise

            finally:
                # Calculate duration
                duration = time.time() - start_time
                duration_ms = duration * 1000

                # Record metrics
                tool_execution_counter.labels(
                    tool_name=actual_tool_name,
                    status=status
                ).inc()

                tool_execution_duration.labels(
                    tool_name=actual_tool_name
                ).observe(duration)

                # Log slow operations
                if duration_ms > PerformanceThreshold.SLOW_OPERATION_ERROR_MS:
                    logger.error(
                        "Slow tool execution detected",
                        tool=actual_tool_name,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=PerformanceThreshold.SLOW_OPERATION_ERROR_MS
                    )
                elif duration_ms > PerformanceThreshold.SLOW_OPERATION_WARNING_MS:
                    logger.warning(
                        "Tool execution slower than expected",
                        tool=actual_tool_name,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=PerformanceThreshold.SLOW_OPERATION_WARNING_MS
                    )

                # Cleanup
                active_connections.dec()

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def monitor_database_query(query_type: str = "select") -> Any:
    """
    Decorator to monitor database query performance.

    Usage:
        @monitor_database_query("insert")
        async def insert_customer(data) -> Any:
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                error_counter.labels(error_type=f"db_{type(e).__name__}").inc()
                logger.error(
                    "Database query failed",
                    query_type=query_type,
                    error=str(e)
                )
                raise

            finally:
                # Calculate duration
                duration = time.time() - start_time
                duration_ms = duration * 1000

                # Record metrics
                database_query_counter.labels(query_type=query_type).inc()
                database_query_duration.labels(query_type=query_type).observe(duration)

                # Log slow queries
                if duration_ms > PerformanceThreshold.DB_QUERY_ERROR_MS:
                    logger.error(
                        "Slow database query detected",
                        query_type=query_type,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=PerformanceThreshold.DB_QUERY_ERROR_MS
                    )
                elif duration_ms > PerformanceThreshold.DB_QUERY_WARNING_MS:
                    logger.warning(
                        "Database query slower than expected",
                        query_type=query_type,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=PerformanceThreshold.DB_QUERY_WARNING_MS
                    )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result

            except Exception as e:
                error_counter.labels(error_type=f"db_{type(e).__name__}").inc()
                logger.error(
                    "Database query failed",
                    query_type=query_type,
                    error=str(e)
                )
                raise

            finally:
                # Calculate duration
                duration = time.time() - start_time
                duration_ms = duration * 1000

                # Record metrics
                database_query_counter.labels(query_type=query_type).inc()
                database_query_duration.labels(query_type=query_type).observe(duration)

                # Log slow queries
                if duration_ms > PerformanceThreshold.DB_QUERY_ERROR_MS:
                    logger.error(
                        "Slow database query detected",
                        query_type=query_type,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=PerformanceThreshold.DB_QUERY_ERROR_MS
                    )
                elif duration_ms > PerformanceThreshold.DB_QUERY_WARNING_MS:
                    logger.warning(
                        "Database query slower than expected",
                        query_type=query_type,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=PerformanceThreshold.DB_QUERY_WARNING_MS
                    )

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def monitor_api_call(integration: str, endpoint: str) -> Any:
    """
    Decorator to monitor platform API call performance.

    Usage:
        @monitor_api_call("zendesk", "create_ticket")
        async def create_zendesk_ticket(data) -> Any:
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                status = "error"
                error_counter.labels(error_type=f"api_{integration}_{type(e).__name__}").inc()
                logger.error(
                    "API call failed",
                    integration=integration,
                    endpoint=endpoint,
                    error=str(e)
                )
                raise

            finally:
                # Calculate duration
                duration = time.time() - start_time
                duration_ms = duration * 1000

                # Record metrics
                platform_api_counter.labels(
                    integration=integration,
                    endpoint=endpoint,
                    status=status
                ).inc()

                platform_api_duration.labels(
                    integration=integration,
                    endpoint=endpoint
                ).observe(duration)

                # Log slow API calls
                if duration_ms > PerformanceThreshold.API_CALL_ERROR_MS:
                    logger.error(
                        "Slow API call detected",
                        integration=integration,
                        endpoint=endpoint,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=PerformanceThreshold.API_CALL_ERROR_MS
                    )
                elif duration_ms > PerformanceThreshold.API_CALL_WARNING_MS:
                    logger.warning(
                        "API call slower than expected",
                        integration=integration,
                        endpoint=endpoint,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=PerformanceThreshold.API_CALL_WARNING_MS
                    )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result

            except Exception as e:
                status = "error"
                error_counter.labels(error_type=f"api_{integration}_{type(e).__name__}").inc()
                logger.error(
                    "API call failed",
                    integration=integration,
                    endpoint=endpoint,
                    error=str(e)
                )
                raise

            finally:
                # Calculate duration
                duration = time.time() - start_time
                duration_ms = duration * 1000

                # Record metrics
                platform_api_counter.labels(
                    integration=integration,
                    endpoint=endpoint,
                    status=status
                ).inc()

                platform_api_duration.labels(
                    integration=integration,
                    endpoint=endpoint
                ).observe(duration)

                # Log slow API calls
                if duration_ms > PerformanceThreshold.API_CALL_ERROR_MS:
                    logger.error(
                        "Slow API call detected",
                        integration=integration,
                        endpoint=endpoint,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=PerformanceThreshold.API_CALL_ERROR_MS
                    )
                elif duration_ms > PerformanceThreshold.API_CALL_WARNING_MS:
                    logger.warning(
                        "API call slower than expected",
                        integration=integration,
                        endpoint=endpoint,
                        duration_ms=round(duration_ms, 2),
                        threshold_ms=PerformanceThreshold.API_CALL_WARNING_MS
                    )

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================================================
# Cache Monitoring Functions
# ============================================================================

def record_cache_hit(cache_type: str = "redis") -> Any:
    """Record a cache hit"""
    cache_hit_counter.labels(cache_type=cache_type).inc()
    logger.debug("Cache hit", cache_type=cache_type)


def record_cache_miss(cache_type: str = "redis") -> Any:
    """Record a cache miss"""
    cache_miss_counter.labels(cache_type=cache_type).inc()
    logger.debug("Cache miss", cache_type=cache_type)


# ============================================================================
# Health Score Monitoring
# ============================================================================

def monitor_health_score_calculation() -> Any:
    """Context manager for monitoring health score calculation"""
    return health_score_calculation_duration.time()


# ============================================================================
# Memory Monitoring
# ============================================================================

def update_memory_usage() -> Any:
    """Update memory usage metrics"""
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_usage_bytes.set(memory_info.rss)
    except ImportError:
        logger.warning("psutil not installed, memory monitoring unavailable")
    except Exception as e:
        logger.error("Failed to update memory usage", error=str(e))


# ============================================================================
# Prometheus Metrics Endpoint
# ============================================================================

class PrometheusMetricsHandler:
    """Handler for Prometheus metrics endpoint"""

    def __init__(self, registry=None) -> Any:
        self.registry = registry

    async def handle_metrics(self) -> tuple[bytes, str]:
        """
        Generate Prometheus metrics in text format.
        Returns: (metrics_bytes, content_type)
        """
        if not PROMETHEUS_AVAILABLE:
            return b"# Prometheus client not installed\n", "text/plain"

        try:
            # Update dynamic metrics
            update_memory_usage()

            # Generate metrics
            metrics = generate_latest(self.registry)
            return metrics, CONTENT_TYPE_LATEST

        except Exception as e:
            logger.error("Failed to generate metrics", error=str(e))
            return b"# Error generating metrics\n", "text/plain"


def start_metrics_server(port: int = 9090) -> Any:
    """
    Start a standalone HTTP server for Prometheus metrics.

    Args:
        port: Port to serve metrics on (default: 9090)
    """
    if not PROMETHEUS_AVAILABLE:
        logger.warning("Prometheus client not installed, metrics server not started")
        return

    try:
        start_http_server(port)
        logger.info(event=f"Prometheus metrics server started on port {port}")
    except Exception as e:
        logger.error(event=f"Failed to start metrics server", error=str(e))


# ============================================================================
# Performance Summary Generator
# ============================================================================

class PerformanceSummary:
    """Generate performance summary reports"""

    @staticmethod
    def get_summary() -> Dict[str, Any]:
        """Get current performance summary"""
        summary = {
            "timestamp": datetime.now().isoformat(),
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "thresholds": {
                "slow_operation_warning_ms": PerformanceThreshold.SLOW_OPERATION_WARNING_MS,
                "slow_operation_error_ms": PerformanceThreshold.SLOW_OPERATION_ERROR_MS,
                "db_query_warning_ms": PerformanceThreshold.DB_QUERY_WARNING_MS,
                "db_query_error_ms": PerformanceThreshold.DB_QUERY_ERROR_MS,
                "api_call_warning_ms": PerformanceThreshold.API_CALL_WARNING_MS,
                "api_call_error_ms": PerformanceThreshold.API_CALL_ERROR_MS,
                "health_score_target_ms": PerformanceThreshold.HEALTH_SCORE_TARGET_MS
            }
        }

        if PROMETHEUS_AVAILABLE:
            # Add current metric values if available
            # Note: This would require accessing the registry directly
            summary["metrics_endpoint"] = "/metrics"
            summary["metrics_port"] = 9090

        return summary


# ============================================================================
# Initialization
# ============================================================================

def initialize_performance_monitoring() -> Any:
    """Initialize performance monitoring system"""
    logger.info("Initializing performance monitoring",
                prometheus_available=PROMETHEUS_AVAILABLE)

    if not PROMETHEUS_AVAILABLE:
        logger.warning(
            "Prometheus client not installed. Install with: pip install prometheus-client"
        )

    # Update initial memory usage
    update_memory_usage()

    return PrometheusMetricsHandler()


# Create global metrics handler instance
metrics_handler = initialize_performance_monitoring()