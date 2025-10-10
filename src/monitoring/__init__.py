"""
Monitoring module for Customer Success MCP
Provides performance monitoring, metrics, and health checks
"""

from src.monitoring.performance_monitor import (
    monitor_tool_execution,
    monitor_database_query,
    monitor_api_call,
    record_cache_hit,
    record_cache_miss,
    monitor_health_score_calculation,
    update_memory_usage,
    PerformanceThreshold,
    PerformanceSummary,
    PROMETHEUS_AVAILABLE
)

from src.monitoring.metrics_server import (
    start_metrics_server,
    stop_metrics_server,
    get_metrics_server
)

from src.monitoring.health_monitoring import (
    HealthMonitor,
    get_health_monitor,
    HealthStatus,
    ComponentHealth
)

__all__ = [
    # Performance monitoring decorators
    'monitor_tool_execution',
    'monitor_database_query',
    'monitor_api_call',

    # Cache monitoring
    'record_cache_hit',
    'record_cache_miss',

    # Health score monitoring
    'monitor_health_score_calculation',

    # System monitoring
    'update_memory_usage',

    # Configuration
    'PerformanceThreshold',
    'PerformanceSummary',
    'PROMETHEUS_AVAILABLE',

    # Metrics server
    'start_metrics_server',
    'stop_metrics_server',
    'get_metrics_server',

    # Health monitoring
    'HealthMonitor',
    'get_health_monitor',
    'HealthStatus',
    'ComponentHealth'
]
