"""
Autonomous Scheduler
Main loop that runs enabled workers on their schedules
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from .config_manager import ConfigManager
from .workers import WORKER_REGISTRY

logger = logging.getLogger(__name__)


class AutonomousScheduler:
    """Scheduler for autonomous workers"""

    def __init__(self, config_manager: ConfigManager, tools: Any):
        """
        Initialize scheduler

        Args:
            config_manager: Configuration manager instance
            tools: Access to MCP tools for workers
        """
        self.config_manager = config_manager
        self.tools = tools
        self.workers: Dict[str, Any] = {}
        self.running = False
        self._initialize_workers()

    def _initialize_workers(self) -> None:
        """Initialize all worker instances"""
        enabled_workers = self.config_manager.get_enabled_workers()

        for worker_name, worker_config in enabled_workers.items():
            if worker_name in WORKER_REGISTRY:
                worker_class = WORKER_REGISTRY[worker_name]
                self.workers[worker_name] = worker_class(
                    name=worker_name, config=worker_config, tools=self.tools
                )
                logger.info(f"Initialized worker: {worker_name}")
            else:
                logger.warning(f"Worker class not found for: {worker_name}")

    async def run_once(self) -> Dict[str, Any]:
        """
        Run all workers that are due (for testing/manual execution)

        Returns:
            Dict with results from all workers
        """
        results = {}

        for worker_name, worker in self.workers.items():
            if worker.should_run():
                logger.info(f"Triggering worker: {worker_name}")
                result = await worker.run()
                results[worker_name] = result
            else:
                logger.debug(f"Worker {worker_name} not due yet")

        return results

    async def run_worker_now(self, worker_name: str) -> Dict[str, Any]:
        """
        Manually trigger a specific worker

        Args:
            worker_name: Name of worker to run

        Returns:
            Worker execution result
        """
        if worker_name not in self.workers:
            return {
                "status": "error",
                "error": f"Worker {worker_name} not found or not enabled",
            }

        logger.info(f"Manual trigger of worker: {worker_name}")
        return await self.workers[worker_name].run()

    async def run_forever(self) -> None:
        """
        Run scheduler loop indefinitely
        Checks all workers and runs those that are due
        """
        self.running = True
        check_interval_seconds = self.config_manager.get_global_interval() * 60

        logger.info(
            f"Starting autonomous scheduler. "
            f"Check interval: {check_interval_seconds}s. "
            f"Workers enabled: {len(self.workers)}"
        )

        while self.running:
            try:
                # Check each worker
                for worker_name, worker in self.workers.items():
                    if worker.should_run():
                        # Run worker in background (don't block other workers)
                        asyncio.create_task(worker.run())

                # Wait until next check
                await asyncio.sleep(check_interval_seconds)

            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)
                # Continue running even if there's an error
                await asyncio.sleep(60)

    def stop(self) -> None:
        """Stop the scheduler"""
        logger.info("Stopping autonomous scheduler")
        self.running = False

    def get_status(self) -> Dict[str, Any]:
        """
        Get scheduler status and worker stats

        Returns:
            Dict with scheduler and worker status
        """
        return {
            "running": self.running,
            "timestamp": datetime.now().isoformat(),
            "global_interval_minutes": self.config_manager.get_global_interval(),
            "workers": {
                worker_name: worker.get_stats()
                for worker_name, worker in self.workers.items()
            },
        }

    def reload_config(self) -> None:
        """Reload configuration and reinitialize workers"""
        logger.info("Reloading autonomous configuration")
        self.config_manager.load_config()
        self.workers.clear()
        self._initialize_workers()
