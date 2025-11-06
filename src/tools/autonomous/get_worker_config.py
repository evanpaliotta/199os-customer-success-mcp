"""
get_worker_config - Get configuration for a specific worker

Args:
    worker_name: Name of worker

Returns:
    Worker configuration

Get configuration for a specific worker

Args:
    worker_name: Name of worker

Returns:
    Worker configuration
"""

from typing import Optional, Dict, List, Any
import structlog
from pathlib import Path
import sys

    from src.decorators import mcp_tool
from src.composio import get_composio_client

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
