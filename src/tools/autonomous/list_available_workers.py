"""
list_available_workers - List all available autonomous workers

Returns:
    List of all workers with descriptions and status

List all available autonomous workers

Returns:
    List of all workers with descriptions and status
"""

from typing import Optional, Dict, List, Any
import structlog
from pathlib import Path
import sys

    from src.decorators import mcp_tool
from src.composio import get_composio_client

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
