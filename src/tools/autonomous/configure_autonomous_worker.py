"""
configure_autonomous_worker - Enable/disable a worker or update its parameters

Args:
    worker_name: Name of worker (e

Enable/disable a worker or update its parameters

Args:
    worker_name: Name of worker (e.g., "deal_risk_monitor")
    enabled: True to enable, False to disable
    params: Optional dict of parameter updates

Returns:
    Success message or error
"""

from typing import Optional, Dict, List, Any
import structlog
from pathlib import Path
import sys
from src.decorators import mcp_tool
from src.composio import get_composio_client
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
