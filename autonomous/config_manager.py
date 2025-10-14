"""
Configuration Manager for Autonomous Workers
Loads and validates autonomous_config.json
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages autonomous worker configuration"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config manager

        Args:
            config_path: Path to config file (default: autonomous_config.json in project root)
        """
        if config_path is None:
            # Default to project root
            project_root = Path(__file__).parent.parent
            config_path = project_root / "autonomous_config.json"

        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            logger.info(f"Loaded autonomous config from {self.config_path}")
            return self.config
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise

    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved autonomous config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def is_enabled(self) -> bool:
        """Check if autonomous mode is globally enabled"""
        return self.config.get("autonomous", {}).get("enabled", False)

    def get_worker_config(self, worker_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific worker

        Args:
            worker_name: Name of the worker (e.g., "deal_risk_monitor")

        Returns:
            Worker configuration dict or None if not found
        """
        return self.config.get("workers", {}).get(worker_name)

    def is_worker_enabled(self, worker_name: str) -> bool:
        """Check if a specific worker is enabled"""
        worker_config = self.get_worker_config(worker_name)
        if not worker_config:
            return False
        return worker_config.get("enabled", False)

    def get_enabled_workers(self) -> Dict[str, Dict[str, Any]]:
        """Get all enabled workers and their configurations"""
        if not self.is_enabled():
            return {}

        workers = self.config.get("workers", {})
        return {
            name: config
            for name, config in workers.items()
            if config.get("enabled", False)
        }

    def set_worker_enabled(self, worker_name: str, enabled: bool) -> None:
        """
        Enable or disable a worker

        Args:
            worker_name: Name of the worker
            enabled: True to enable, False to disable
        """
        if "workers" not in self.config:
            self.config["workers"] = {}

        if worker_name not in self.config["workers"]:
            logger.warning(f"Worker {worker_name} not found in config")
            return

        self.config["workers"][worker_name]["enabled"] = enabled
        self.save_config()
        logger.info(f"Worker {worker_name} {'enabled' if enabled else 'disabled'}")

    def update_worker_params(self, worker_name: str, params: Dict[str, Any]) -> None:
        """
        Update worker parameters

        Args:
            worker_name: Name of the worker
            params: Parameter updates
        """
        if "workers" not in self.config:
            self.config["workers"] = {}

        if worker_name not in self.config["workers"]:
            logger.warning(f"Worker {worker_name} not found in config")
            return

        if "params" not in self.config["workers"][worker_name]:
            self.config["workers"][worker_name]["params"] = {}

        self.config["workers"][worker_name]["params"].update(params)
        self.save_config()
        logger.info(f"Updated params for worker {worker_name}: {params}")

    def get_notification_config(self) -> Dict[str, Any]:
        """Get notification configuration"""
        return self.config.get("autonomous", {}).get("notifications", {})

    def get_global_interval(self) -> int:
        """Get global check interval in minutes"""
        return self.config.get("autonomous", {}).get("global_interval_minutes", 30)
