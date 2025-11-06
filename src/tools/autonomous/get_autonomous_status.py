"""
get_autonomous_status - Get status of all autonomous workers

Returns:
    Status of autonomous system and all workers

Get status of all autonomous workers

Returns:
    Status of autonomous system and all workers
"""

from typing import Optional, Dict, List, Any
import structlog
from pathlib import Path
import sys

    from src.decorators import mcp_tool
from src.composio import get_composio_client

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
