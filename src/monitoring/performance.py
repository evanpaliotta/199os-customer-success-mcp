"""
Performance Monitoring for Sales MCP
Tracks request latency, resource usage, and tool performance metrics
"""

import time
import functools
import psutil
from typing import Any, Callable, Dict, List, Optional, TypeVar
from datetime import datetime
from collections import defaultdict, deque
from dataclasses import dataclass, field
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T')


# ============================================================================
# Performance Thresholds & Configuration
# ============================================================================

THRESHOLDS = {
    'max_latency_ms': 5000,          # 5 second timeout
    'max_memory_mb': 1024,            # 1GB memory per process
    'max_error_rate': 0.05,           # 5% error rate
    'min_cache_hit_rate': 0.70,       # 70% cache hits
    'warning_latency_ms': 2000,       # Warn at 2 seconds
    'critical_latency_ms': 4000,      # Critical at 4 seconds
}


# ============================================================================
# Performance Data Structures
# ============================================================================

@dataclass
class PerformanceMetric:
    """Single performance measurement"""
    tool_name: str
    start_time: float
    end_time: float
    duration_ms: float
    success: bool
    error: Optional[str] = None
    memory_delta_mb: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tool_name": self.tool_name,
            "duration_ms": round(self.duration_ms, 2),
            "success": self.success,
            "error": self.error,
            "memory_delta_mb": round(self.memory_delta_mb, 2) if self.memory_delta_mb else None,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class ToolStats:
    """Aggregated statistics for a tool"""
    tool_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    durations: deque = field(default_factory=lambda: deque(maxlen=1000))  # Keep last 1000

    @property
    def error_rate(self) -> float:
        """Calculate error rate"""
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls

    @property
    def avg_duration_ms(self) -> float:
        """Calculate average duration"""
        if self.total_calls == 0:
            return 0.0
        return self.total_duration_ms / self.total_calls

    @property
    def p50_duration_ms(self) -> float:
        """Calculate 50th percentile (median)"""
        if not self.durations:
            return 0.0
        sorted_durations = sorted(self.durations)
        return sorted_durations[len(sorted_durations) // 2]

    @property
    def p95_duration_ms(self) -> float:
        """Calculate 95th percentile"""
        if not self.durations:
            return 0.0
        sorted_durations = sorted(self.durations)
        index = int(len(sorted_durations) * 0.95)
        return sorted_durations[index]

    @property
    def p99_duration_ms(self) -> float:
        """Calculate 99th percentile"""
        if not self.durations:
            return 0.0
        sorted_durations = sorted(self.durations)
        index = int(len(sorted_durations) * 0.99)
        return sorted_durations[index]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "tool_name": self.tool_name,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "error_rate": round(self.error_rate, 4),
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "min_duration_ms": round(self.min_duration_ms, 2) if self.min_duration_ms != float('inf') else 0,
            "max_duration_ms": round(self.max_duration_ms, 2),
            "p50_duration_ms": round(self.p50_duration_ms, 2),
            "p95_duration_ms": round(self.p95_duration_ms, 2),
            "p99_duration_ms": round(self.p99_duration_ms, 2)
        }


# ============================================================================
# Performance Monitor
# ============================================================================

class PerformanceMonitor:
    """Central performance monitoring system"""

    def __init__(self):
        self.tool_stats: Dict[str, ToolStats] = defaultdict(ToolStats)
        self.recent_metrics: deque = deque(maxlen=10000)  # Keep last 10k metrics
        self.start_time = time.time()
        self.process = psutil.Process()

    def record_metric(self, metric: PerformanceMetric):
        """Record a performance metric"""
        tool_name = metric.tool_name

        # Initialize stats if needed
        if tool_name not in self.tool_stats:
            self.tool_stats[tool_name] = ToolStats(tool_name=tool_name)

        stats = self.tool_stats[tool_name]

        # Update stats
        stats.total_calls += 1
        if metric.success:
            stats.successful_calls += 1
        else:
            stats.failed_calls += 1

        stats.total_duration_ms += metric.duration_ms
        stats.min_duration_ms = min(stats.min_duration_ms, metric.duration_ms)
        stats.max_duration_ms = max(stats.max_duration_ms, metric.duration_ms)
        stats.durations.append(metric.duration_ms)

        # Store recent metric
        self.recent_metrics.append(metric)

        # Check thresholds and log warnings
        self._check_thresholds(metric, stats)

    def _check_thresholds(self, metric: PerformanceMetric, stats: ToolStats):
        """Check if metric exceeds thresholds"""
        # Check latency
        if metric.duration_ms > THRESHOLDS['critical_latency_ms']:
            logger.error(
                f"Critical latency threshold exceeded",
                tool=metric.tool_name,
                duration_ms=metric.duration_ms,
                threshold=THRESHOLDS['critical_latency_ms']
            )
        elif metric.duration_ms > THRESHOLDS['warning_latency_ms']:
            logger.warning(
                f"Warning latency threshold exceeded",
                tool=metric.tool_name,
                duration_ms=metric.duration_ms,
                threshold=THRESHOLDS['warning_latency_ms']
            )

        # Check error rate
        if stats.error_rate > THRESHOLDS['max_error_rate']:
            logger.error(
                f"Error rate threshold exceeded",
                tool=metric.tool_name,
                error_rate=stats.error_rate,
                threshold=THRESHOLDS['max_error_rate']
            )

    def get_tool_stats(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for a tool or all tools"""
        if tool_name:
            if tool_name in self.tool_stats:
                return self.tool_stats[tool_name].to_dict()
            else:
                return {"error": f"No stats for tool: {tool_name}"}

        # Return all stats
        return {
            name: stats.to_dict()
            for name, stats in self.tool_stats.items()
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        total_calls = sum(s.total_calls for s in self.tool_stats.values())
        total_errors = sum(s.failed_calls for s in self.tool_stats.values())
        uptime_seconds = time.time() - self.start_time

        # Calculate overall metrics
        all_durations = []
        for stats in self.tool_stats.values():
            all_durations.extend(stats.durations)

        if all_durations:
            sorted_durations = sorted(all_durations)
            avg_duration = sum(sorted_durations) / len(sorted_durations)
            p50 = sorted_durations[len(sorted_durations) // 2]
            p95 = sorted_durations[int(len(sorted_durations) * 0.95)]
            p99 = sorted_durations[int(len(sorted_durations) * 0.99)]
        else:
            avg_duration = p50 = p95 = p99 = 0

        # Get memory info
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)

        return {
            "uptime_seconds": round(uptime_seconds, 2),
            "uptime_hours": round(uptime_seconds / 3600, 2),
            "total_requests": total_calls,
            "total_errors": total_errors,
            "error_rate": round(total_errors / total_calls, 4) if total_calls > 0 else 0,
            "tools_tracked": len(self.tool_stats),
            "latency": {
                "avg_ms": round(avg_duration, 2),
                "p50_ms": round(p50, 2),
                "p95_ms": round(p95, 2),
                "p99_ms": round(p99, 2)
            },
            "memory": {
                "current_mb": round(memory_mb, 2),
                "threshold_mb": THRESHOLDS['max_memory_mb'],
                "within_threshold": memory_mb < THRESHOLDS['max_memory_mb']
            },
            "thresholds": {
                "max_latency_ms": THRESHOLDS['max_latency_ms'],
                "max_error_rate": THRESHOLDS['max_error_rate'],
                "warning_latency_ms": THRESHOLDS['warning_latency_ms'],
                "critical_latency_ms": THRESHOLDS['critical_latency_ms']
            }
        }

    def get_slowest_tools(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest tools by average duration"""
        sorted_stats = sorted(
            self.tool_stats.values(),
            key=lambda s: s.avg_duration_ms,
            reverse=True
        )
        return [s.to_dict() for s in sorted_stats[:limit]]

    def get_most_called_tools(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently called tools"""
        sorted_stats = sorted(
            self.tool_stats.values(),
            key=lambda s: s.total_calls,
            reverse=True
        )
        return [s.to_dict() for s in sorted_stats[:limit]]

    def get_highest_error_tools(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get tools with highest error rates"""
        sorted_stats = sorted(
            [s for s in self.tool_stats.values() if s.failed_calls > 0],
            key=lambda s: s.error_rate,
            reverse=True
        )
        return [s.to_dict() for s in sorted_stats[:limit]]

    def reset_stats(self):
        """Reset all statistics"""
        self.tool_stats.clear()
        self.recent_metrics.clear()
        self.start_time = time.time()
        logger.info("Performance statistics reset")


# ============================================================================
# Performance Tracking Decorator
# ============================================================================

def track_performance(tool_name: Optional[str] = None):
    """
    Decorator to track performance of MCP tools.

    Usage:
        @track_performance()
        async def my_tool(ctx, ...):
            ...

        @track_performance(tool_name="custom_name")
        async def my_tool(ctx, ...):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Use provided tool_name or function name
        actual_tool_name = tool_name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Get memory before
            try:
                process = psutil.Process()
                memory_before = process.memory_info().rss / (1024 * 1024)  # MB
            except:
                memory_before = None

            start_time = time.time()
            success = False
            error = None

            try:
                result = await func(*args, **kwargs)
                success = True
                return result

            except Exception as e:
                error = str(e)
                raise

            finally:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000

                # Get memory after
                try:
                    memory_after = process.memory_info().rss / (1024 * 1024)  # MB
                    memory_delta = memory_after - memory_before if memory_before else None
                except:
                    memory_delta = None

                # Record metric
                metric = PerformanceMetric(
                    tool_name=actual_tool_name,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    success=success,
                    error=error,
                    memory_delta_mb=memory_delta
                )

                # Get global monitor and record
                monitor = get_performance_monitor()
                monitor.record_metric(metric)

                # Log if slow
                if duration_ms > THRESHOLDS['warning_latency_ms']:
                    logger.warning(
                        f"Slow tool execution",
                        tool=actual_tool_name,
                        duration_ms=round(duration_ms, 2),
                        success=success
                    )

        return wrapper
    return decorator


# ============================================================================
# Global Performance Monitor Instance
# ============================================================================

_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor instance"""
    global _performance_monitor

    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
        logger.info("Performance monitor initialized")

    return _performance_monitor


def reset_performance_monitor():
    """Reset the global performance monitor"""
    global _performance_monitor
    if _performance_monitor:
        _performance_monitor.reset_stats()
