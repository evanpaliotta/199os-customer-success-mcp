"""
Base Worker Class
All autonomous workers inherit from this class
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class AutonomousWorker(ABC):
    """Base class for all autonomous workers"""

    def __init__(self, name: str, config: Dict[str, Any], tools: Any):
        """
        Initialize worker

        Args:
            name: Worker name (e.g., "deal_risk_monitor")
            config: Worker configuration from autonomous_config.json
            tools: Access to MCP tools
        """
        self.name = name
        self.config = config
        self.tools = tools
        self.last_run: Optional[datetime] = None
        self.run_count = 0
        self.alert_count = 0
        self.error_count = 0

    def should_run(self) -> bool:
        """
        Check if worker should run based on interval

        Returns:
            True if worker should run
        """
        if not self.config.get("enabled", False):
            return False

        interval_hours = self.config.get("interval_hours", 24)

        # First run
        if self.last_run is None:
            return True

        # Check if interval has elapsed
        next_run = self.last_run + timedelta(hours=interval_hours)
        return datetime.now() >= next_run

    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """
        Execute worker logic
        Must be implemented by each worker

        Returns:
            Dict with execution results
        """
        pass

    async def run(self) -> Dict[str, Any]:
        """
        Run the worker (wrapper around execute)

        Returns:
            Dict with run results including status and data
        """
        try:
            logger.info(f"Running worker: {self.name}")
            start_time = datetime.now()

            # Execute worker logic
            result = await self.execute()

            # Update run stats
            self.last_run = datetime.now()
            self.run_count += 1
            duration = (datetime.now() - start_time).total_seconds()

            # Send notifications if needed
            if result.get("alerts"):
                await self.notify(result["alerts"])
                self.alert_count += len(result["alerts"])

            logger.info(
                f"Worker {self.name} completed in {duration:.2f}s. "
                f"Results: {result.get('summary', 'no summary')}"
            )

            return {
                "status": "success",
                "worker": self.name,
                "timestamp": self.last_run.isoformat(),
                "duration_seconds": duration,
                "data": result,
            }

        except Exception as e:
            self.error_count += 1
            logger.error(f"Worker {self.name} failed: {e}", exc_info=True)
            return {
                "status": "error",
                "worker": self.name,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }

    async def notify(self, alerts: list) -> None:
        """
        Send notifications for alerts

        Args:
            alerts: List of alert dicts
        """
        notification_config = self.config.get("notifications", {})

        # Slack notifications
        if notification_config.get("slack_enabled"):
            webhook_url = notification_config.get("slack_webhook")
            if webhook_url:
                await self._send_slack_notification(webhook_url, alerts)

        # Email notifications (placeholder - implement with your email service)
        if notification_config.get("email_enabled"):
            email_to = notification_config.get("email_to")
            if email_to:
                logger.info(f"Email notification would be sent to {email_to}")
                # TODO: Implement email sending

    async def _send_slack_notification(self, webhook_url: str, alerts: list) -> None:
        """Send Slack notification"""
        try:
            message = self._format_slack_message(alerts)
            response = requests.post(webhook_url, json=message, timeout=10)
            response.raise_for_status()
            logger.info(f"Sent Slack notification for {len(alerts)} alerts")
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")

    def _format_slack_message(self, alerts: list) -> Dict[str, Any]:
        """Format alerts as Slack message"""
        alert_text = "\n".join([f"• {alert}" for alert in alerts])
        return {
            "text": f"*{self.name.replace('_', ' ').title()} Alert*",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 {self.name.replace('_', ' ').title()}",
                    },
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": alert_text},
                },
            ],
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        return {
            "name": self.name,
            "enabled": self.config.get("enabled", False),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
            "alert_count": self.alert_count,
            "error_count": self.error_count,
            "interval_hours": self.config.get("interval_hours"),
        }
