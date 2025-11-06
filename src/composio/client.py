"""
Composio MCP Client - Stub Implementation

This is a stub for the Composio MCP server client. The actual Composio MCP
server will be configured separately and accessed via MCP protocol.

In Phase 2-3, tools will use this client to execute actions through Composio,
which provides 300+ managed integrations with OAuth handling.

Usage:
    from src.composio.client import get_composio_client

    composio = get_composio_client()
    result = await composio.execute_action(
        "salesforce_get_opportunities",
        user_id=client_id,
        params={"limit": 100}
    )

Note: This stub will be replaced with actual MCP client once Composio MCP
server is installed and configured.
"""

import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class ComposioClientStub:
    """
    Stub implementation of Composio MCP client.

    This class provides the interface that tools will use. The actual
    implementation will communicate with the Composio MCP server via
    the Model Context Protocol.
    """

    def __init__(self):
        self._initialized = False
        logger.warning(
            "Using Composio client stub. Install Composio MCP server for production use. "
            "See: https://docs.composio.dev/framework/mcp"
        )

    async def initialize(self) -> None:
        """Initialize connection to Composio MCP server"""
        if self._initialized:
            return

        # TODO: Replace with actual MCP connection
        logger.info("Composio MCP client stub initialized (no real connection)")
        self._initialized = True

    async def execute_action(
        self,
        action: str,
        user_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute an action via Composio MCP server.

        Args:
            action: The Composio action to execute (e.g., "salesforce_get_opportunities")
            user_id: Client ID for OAuth context
            params: Action-specific parameters

        Returns:
            Action execution result

        Raises:
            NotImplementedError: Stub implementation - requires real Composio MCP server
        """
        if not self._initialized:
            await self.initialize()

        logger.warning(
            f"Composio action stub called: {action} for user {user_id}. "
            "Install Composio MCP server to execute real actions."
        )

        raise NotImplementedError(
            f"Composio MCP server not configured. Cannot execute action: {action}\n"
            "To enable:\n"
            "1. Install Composio MCP server: npx @composio/mcp init\n"
            "2. Configure OAuth for integrations\n"
            "3. Update this client to use MCP protocol"
        )

    async def list_actions(self, app_name: Optional[str] = None) -> list[str]:
        """
        List available Composio actions.

        Args:
            app_name: Optional app filter (e.g., "salesforce", "gmail")

        Returns:
            List of available action names
        """
        # Stub: Return example actions
        return [
            "salesforce_get_opportunities",
            "salesforce_create_opportunity",
            "gmail_send_email",
            "slack_send_message",
            "hubspot_get_contacts",
        ]

    async def get_app_connection_status(
        self,
        app_name: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Check if user has connected an app via OAuth.

        Args:
            app_name: App to check (e.g., "salesforce")
            user_id: Client ID

        Returns:
            Connection status dict with 'connected' boolean
        """
        return {
            "app": app_name,
            "user_id": user_id,
            "connected": False,
            "message": "Composio MCP server stub - no real connections"
        }


# Singleton instance
_composio_client: Optional[ComposioClientStub] = None


def get_composio_client() -> ComposioClientStub:
    """
    Get singleton Composio client instance.

    Returns:
        ComposioClientStub: The Composio MCP client

    Example:
        >>> composio = get_composio_client()
        >>> result = await composio.execute_action("salesforce_get_opportunities", ...)
    """
    global _composio_client
    if _composio_client is None:
        _composio_client = ComposioClientStub()
    return _composio_client


@asynccontextmanager
async def composio_action(action: str, user_id: str, params: Optional[Dict[str, Any]] = None):
    """
    Async context manager for executing Composio actions with automatic resource cleanup.

    Usage:
        async with composio_action("salesforce_get_opportunities", client_id, params) as result:
            # Process result
            pass
    """
    client = get_composio_client()
    await client.initialize()

    try:
        result = await client.execute_action(action, user_id, params)
        yield result
    finally:
        # Cleanup if needed
        pass
