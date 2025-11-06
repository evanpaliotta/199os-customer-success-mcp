"""
trigger_worker_now - Manually trigger a worker to run immediately

Args:
    worker_name: Name of worker to trigger

Returns:
    Worker execution results

Manually trigger a worker to run immediately

Args:
    worker_name: Name of worker to trigger

Returns:
    Worker execution results
"""

from typing import Optional, Dict, List, Any
import structlog
from pathlib import Path
import sys

    from src.decorators import mcp_tool
from src.composio import get_composio_client

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
