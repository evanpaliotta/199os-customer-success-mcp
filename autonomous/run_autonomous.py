#!/usr/bin/env python3
"""
199|OS Sales MCP - Autonomous Mode
Run 24/7 autonomous monitoring

Usage:
    python autonomous/run_autonomous.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from autonomous.config_manager import ConfigManager
from autonomous.scheduler import AutonomousScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(project_root / "logs" / "autonomous.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for autonomous mode"""
    logger.info("=" * 60)
    logger.info("199|OS Sales MCP - Autonomous Mode Starting")
    logger.info("=" * 60)

    try:
        # Load configuration
        config_manager = ConfigManager()

        if not config_manager.is_enabled():
            logger.error("Autonomous mode is disabled in config. Set 'autonomous.enabled' to true.")
            return

        # Initialize tools (import your MCP tools here)
        # For now, we'll pass None - you'll need to connect this to your actual tools
        tools = None  # TODO: Initialize MCP tools access

        # Create scheduler
        scheduler = AutonomousScheduler(config_manager, tools)

        # Show status
        status = scheduler.get_status()
        logger.info(f"Enabled workers: {len(status['workers'])}")
        for worker_name, worker_status in status["workers"].items():
            logger.info(
                f"  - {worker_name}: "
                f"interval={worker_status['interval_hours']}h, "
                f"runs={worker_status['run_count']}"
            )

        # Run scheduler
        logger.info("Starting autonomous scheduler loop...")
        await scheduler.run_forever()

    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        logger.info("Autonomous mode stopped")


if __name__ == "__main__":
    asyncio.run(main())
