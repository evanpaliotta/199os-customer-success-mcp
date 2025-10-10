"""
Health Monitoring System for Sales MCP
Provides comprehensive health checks for all system components
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentHealth:
    """Health status for a single component"""

    def __init__(
        self,
        name: str,
        status: HealthStatus,
        message: str = "",
        metrics: Optional[Dict[str, Any]] = None,
        last_check: Optional[datetime] = None
    ):
        self.name = name
        self.status = status
        self.message = message
        self.metrics = metrics or {}
        self.last_check = last_check or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "metrics": self.metrics,
            "last_check": self.last_check.isoformat()
        }


class HealthMonitor:
    """Comprehensive health monitoring system"""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.last_full_check: Optional[datetime] = None
        self.component_statuses: Dict[str, ComponentHealth] = {}

    def check_all_components(self) -> Dict[str, Any]:
        """Run health checks on all system components"""
        start_time = time.time()

        components = []

        # Check each component
        components.append(self._check_filesystem())
        components.append(self._check_database())
        components.append(self._check_cache())
        components.append(self._check_credentials())
        components.append(self._check_models())
        components.append(self._check_memory())
        components.append(self._check_configuration())

        # Calculate overall status
        statuses = [c.status for c in components]
        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        # Store results
        self.last_full_check = datetime.now()
        for component in components:
            self.component_statuses[component.name] = component

        check_duration = time.time() - start_time

        return {
            "overall_status": overall_status.value,
            "checked_at": self.last_full_check.isoformat(),
            "check_duration_ms": round(check_duration * 1000, 2),
            "components": [c.to_dict() for c in components],
            "summary": {
                "total_components": len(components),
                "healthy": sum(1 for c in components if c.status == HealthStatus.HEALTHY),
                "degraded": sum(1 for c in components if c.status == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for c in components if c.status == HealthStatus.UNHEALTHY)
            }
        }

    def _check_filesystem(self) -> ComponentHealth:
        """Check filesystem access and disk space"""
        try:
            # Check critical directories exist and are writable
            critical_dirs = [
                self.config_path,
                self.config_path / "data",
                self.config_path / "logs",
                self.config_path / "cache"
            ]

            missing_dirs = []
            unwritable_dirs = []

            for dir_path in critical_dirs:
                if not dir_path.exists():
                    missing_dirs.append(str(dir_path))
                elif not os.access(dir_path, os.W_OK):
                    unwritable_dirs.append(str(dir_path))

            # Check disk space
            import shutil
            disk_stats = shutil.disk_usage(self.config_path)
            disk_usage_percent = (disk_stats.used / disk_stats.total) * 100

            metrics = {
                "disk_total_gb": round(disk_stats.total / (1024**3), 2),
                "disk_used_gb": round(disk_stats.used / (1024**3), 2),
                "disk_free_gb": round(disk_stats.free / (1024**3), 2),
                "disk_usage_percent": round(disk_usage_percent, 2)
            }

            if missing_dirs or unwritable_dirs:
                return ComponentHealth(
                    name="filesystem",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Missing dirs: {missing_dirs}, Unwritable: {unwritable_dirs}",
                    metrics=metrics
                )
            elif disk_usage_percent > 90:
                return ComponentHealth(
                    name="filesystem",
                    status=HealthStatus.DEGRADED,
                    message=f"Disk usage high: {disk_usage_percent:.1f}%",
                    metrics=metrics
                )
            else:
                return ComponentHealth(
                    name="filesystem",
                    status=HealthStatus.HEALTHY,
                    message="All directories accessible",
                    metrics=metrics
                )
        except Exception as e:
            logger.error("filesystem_check_failed", error=str(e))
            return ComponentHealth(
                name="filesystem",
                status=HealthStatus.UNHEALTHY,
                message=f"Error: {str(e)}"
            )

    def _check_database(self) -> ComponentHealth:
        """Check database connectivity and status"""
        try:
            # Check if database file exists
            db_path = self.config_path / "data" / "sales.db"

            if not db_path.exists():
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    message="Database file not found (will be created on first use)"
                )

            # Check database is readable
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get database size
            db_size_bytes = db_path.stat().st_size

            # Count tables
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]

            conn.close()

            metrics = {
                "db_size_mb": round(db_size_bytes / (1024**2), 2),
                "table_count": table_count,
                "db_path": str(db_path)
            }

            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                message=f"Database operational with {table_count} tables",
                metrics=metrics
            )
        except Exception as e:
            logger.error("database_check_failed", error=str(e))
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Error: {str(e)}"
            )

    def _check_cache(self) -> ComponentHealth:
        """Check cache system status"""
        try:
            cache_dir = self.config_path / "cache"

            if not cache_dir.exists():
                return ComponentHealth(
                    name="cache",
                    status=HealthStatus.DEGRADED,
                    message="Cache directory not found"
                )

            # Count cache files
            cache_files = list(cache_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in cache_files)

            metrics = {
                "cache_files": len(cache_files),
                "cache_size_mb": round(total_size / (1024**2), 2),
                "cache_path": str(cache_dir)
            }

            return ComponentHealth(
                name="cache",
                status=HealthStatus.HEALTHY,
                message=f"Cache operational with {len(cache_files)} entries",
                metrics=metrics
            )
        except Exception as e:
            logger.error("cache_check_failed", error=str(e))
            return ComponentHealth(
                name="cache",
                status=HealthStatus.DEGRADED,
                message=f"Error: {str(e)}"
            )

    def _check_credentials(self) -> ComponentHealth:
        """Check credential manager status"""
        try:
            creds_dir = self.config_path / "credentials"

            if not creds_dir.exists():
                return ComponentHealth(
                    name="credentials",
                    status=HealthStatus.DEGRADED,
                    message="Credentials directory not found"
                )

            # Check master password is set
            master_password = os.getenv('CREDENTIAL_MASTER_PASSWORD')
            if not master_password:
                return ComponentHealth(
                    name="credentials",
                    status=HealthStatus.DEGRADED,
                    message="CREDENTIAL_MASTER_PASSWORD not set"
                )

            # Count credential files
            cred_files = list(creds_dir.glob("*.enc"))

            metrics = {
                "credential_files": len(cred_files),
                "master_password_set": bool(master_password)
            }

            return ComponentHealth(
                name="credentials",
                status=HealthStatus.HEALTHY,
                message=f"Credential manager operational with {len(cred_files)} clients",
                metrics=metrics
            )
        except Exception as e:
            logger.error("credentials_check_failed", error=str(e))
            return ComponentHealth(
                name="credentials",
                status=HealthStatus.DEGRADED,
                message=f"Error: {str(e)}"
            )

    def _check_models(self) -> ComponentHealth:
        """Check ML model availability"""
        try:
            # Check if models can be imported
            from src.intelligence.sales_predictive_intelligence import sales_forecaster

            metrics = {
                "forecaster_available": True
            }

            return ComponentHealth(
                name="models",
                status=HealthStatus.HEALTHY,
                message="ML models loaded successfully",
                metrics=metrics
            )
        except Exception as e:
            logger.error("models_check_failed", error=str(e))
            return ComponentHealth(
                name="models",
                status=HealthStatus.DEGRADED,
                message=f"Model loading error: {str(e)}"
            )

    def _check_memory(self) -> ComponentHealth:
        """Check system memory usage"""
        try:
            import psutil

            memory = psutil.virtual_memory()
            process = psutil.Process()
            process_memory = process.memory_info()

            metrics = {
                "system_memory_total_gb": round(memory.total / (1024**3), 2),
                "system_memory_used_percent": memory.percent,
                "process_memory_mb": round(process_memory.rss / (1024**2), 2),
                "process_memory_percent": round(process.memory_percent(), 2)
            }

            if memory.percent > 90:
                return ComponentHealth(
                    name="memory",
                    status=HealthStatus.DEGRADED,
                    message=f"System memory high: {memory.percent}%",
                    metrics=metrics
                )
            elif process.memory_percent() > 10:
                return ComponentHealth(
                    name="memory",
                    status=HealthStatus.DEGRADED,
                    message=f"Process memory high: {process.memory_percent():.1f}%",
                    metrics=metrics
                )
            else:
                return ComponentHealth(
                    name="memory",
                    status=HealthStatus.HEALTHY,
                    message="Memory usage normal",
                    metrics=metrics
                )
        except ImportError:
            # psutil not available
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNKNOWN,
                message="psutil not installed, memory monitoring unavailable"
            )
        except Exception as e:
            logger.error("memory_check_failed", error=str(e))
            return ComponentHealth(
                name="memory",
                status=HealthStatus.UNKNOWN,
                message=f"Error: {str(e)}"
            )

    def _check_configuration(self) -> ComponentHealth:
        """Check configuration validity"""
        try:
            # Check critical environment variables
            critical_vars = {
                "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
                "CREDENTIAL_MASTER_PASSWORD": os.getenv("CREDENTIAL_MASTER_PASSWORD")
            }

            missing_vars = [k for k, v in critical_vars.items() if not v]

            metrics = {
                "env_vars_set": len([v for v in critical_vars.values() if v]),
                "env_vars_total": len(critical_vars),
                "missing_vars": missing_vars
            }

            if missing_vars:
                return ComponentHealth(
                    name="configuration",
                    status=HealthStatus.DEGRADED,
                    message=f"Missing environment variables: {missing_vars}",
                    metrics=metrics
                )
            else:
                return ComponentHealth(
                    name="configuration",
                    status=HealthStatus.HEALTHY,
                    message="All critical configuration present",
                    metrics=metrics
                )
        except Exception as e:
            logger.error("configuration_check_failed", error=str(e))
            return ComponentHealth(
                name="configuration",
                status=HealthStatus.DEGRADED,
                message=f"Error: {str(e)}"
            )

    def get_component_status(self, component_name: str) -> Optional[ComponentHealth]:
        """Get status of a specific component"""
        return self.component_statuses.get(component_name)

    def is_healthy(self) -> bool:
        """Check if system is overall healthy"""
        if not self.component_statuses:
            return False
        return all(
            c.status == HealthStatus.HEALTHY
            for c in self.component_statuses.values()
        )


# Global health monitor instance
_health_monitor: Optional[HealthMonitor] = None


def get_health_monitor(config_path: Optional[Path] = None) -> HealthMonitor:
    """Get or create global health monitor instance"""
    global _health_monitor

    if _health_monitor is None:
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent
        _health_monitor = HealthMonitor(config_path)

    return _health_monitor
