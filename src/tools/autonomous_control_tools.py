"""
Autonomous Control Tools
MCP tools to control and monitor autonomous workers
"""

import structlog
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from autonomous.config_manager import ConfigManager
from autonomous.scheduler import AutonomousScheduler

logger = structlog.get_logger(__name__)

# Global instances (initialized when server starts)
_config_manager = None
_scheduler = None


def initialize_autonomous_system(tools):
    """Initialize autonomous system (called on server startup)"""
    global _config_manager, _scheduler
    try:
        _config_manager = ConfigManager()
        if _config_manager.is_enabled():
            _scheduler = AutonomousScheduler(_config_manager, tools)
            logger.info("Autonomous system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize autonomous system: {e}")


def register_tools(mcp_instance):
    """Register autonomous control tools with MCP"""

    @mcp_instance.tool()
    async def get_autonomous_status() -> dict:
        """
        Get status of all autonomous workers

        Returns:
            Status of autonomous system and all workers
        """
        try:
            if not _config_manager:
                return {"error": "Autonomous system not initialized"}

            if not _config_manager.is_enabled():
                return {
                    "enabled": False,
                    "message": "Autonomous mode is disabled. Enable it in autonomous_config.json",
                }

            if _scheduler:
                return _scheduler.get_status()
            else:
                return {
                    "enabled": True,
                    "running": False,
                    "workers": {
                        name: {"enabled": config.get("enabled", False)}
                        for name, config in _config_manager.get_enabled_workers().items()
                    },
                }

        except Exception as e:
            logger.error(f"Error getting autonomous status: {e}")
            return {"error": str(e)}

    @mcp_instance.tool()
    async def configure_autonomous_worker(
        worker_name: str, enabled: bool, params: dict = None
    ) -> dict:
        """
        Enable/disable a worker or update its parameters

        Args:
            worker_name: Name of worker (e.g., "deal_risk_monitor")
            enabled: True to enable, False to disable
            params: Optional dict of parameter updates

        Returns:
            Success message or error
        """
        try:
            if not _config_manager:
                return {"error": "Autonomous system not initialized"}

            # Update enabled status
            _config_manager.set_worker_enabled(worker_name, enabled)

            # Update params if provided
            if params:
                _config_manager.update_worker_params(worker_name, params)

            # Reload scheduler if running
            if _scheduler:
                _scheduler.reload_config()

            return {
                "success": True,
                "message": f"Worker {worker_name} {'enabled' if enabled else 'disabled'}",
                "params_updated": bool(params),
            }

        except Exception as e:
            logger.error(f"Error configuring worker: {e}")
            return {"error": str(e)}

    @mcp_instance.tool()
    async def trigger_worker_now(worker_name: str) -> dict:
        """
        Manually trigger a worker to run immediately

        Args:
            worker_name: Name of worker to trigger

        Returns:
            Worker execution results
        """
        try:
            if not _scheduler:
                return {"error": "Autonomous scheduler not running"}

            result = await _scheduler.run_worker_now(worker_name)
            return result

        except Exception as e:
            logger.error(f"Error triggering worker: {e}")
            return {"error": str(e)}

    @mcp_instance.tool()
    async def get_worker_config(worker_name: str) -> dict:
        """
        Get configuration for a specific worker

        Args:
            worker_name: Name of worker

        Returns:
            Worker configuration
        """
        try:
            if not _config_manager:
                return {"error": "Autonomous system not initialized"}

            config = _config_manager.get_worker_config(worker_name)
            if not config:
                return {"error": f"Worker {worker_name} not found"}

            return {
                "worker_name": worker_name,
                "config": config,
            }

        except Exception as e:
            logger.error(f"Error getting worker config: {e}")
            return {"error": str(e)}

    @mcp_instance.tool()
    async def list_available_workers() -> dict:
        """
        List all available autonomous workers

        Returns:
            List of all workers with descriptions and status
        """
        try:
            if not _config_manager:
                return {"error": "Autonomous system not initialized"}

            workers = _config_manager.config.get("workers", {})
            worker_list = []

            for name, config in workers.items():
                worker_list.append(
                    {
                        "name": name,
                        "enabled": config.get("enabled", False),
                        "interval_hours": config.get("interval_hours"),
                        "description": config.get("description", ""),
                    }
                )

            return {
                "autonomous_enabled": _config_manager.is_enabled(),
                "workers": worker_list,
                "total_workers": len(worker_list),
                "enabled_workers": sum(1 for w in worker_list if w["enabled"]),
            }

        except Exception as e:
            logger.error(f"Error listing workers: {e}")
            return {"error": str(e)}

    logger.info("✅ Autonomous control tools registered (5 tools)")
