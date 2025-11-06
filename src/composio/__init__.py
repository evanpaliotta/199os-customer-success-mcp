"""
Composio MCP Integration

This module provides integration with the Composio MCP server, which manages
300+ third-party integrations with OAuth handling.

In Phase 2-3, all tools will be migrated to use Composio instead of custom integrations.

Usage:
    from src.composio import get_composio_client, composio_action

    # Get singleton client
    composio = get_composio_client()

    # Execute action
    result = await composio.execute_action(
        "salesforce_get_opportunities",
        user_id=client_id,
        params={"limit": 100}
    )

    # Or use context manager
    async with composio_action("salesforce_get_opportunities", client_id, params) as result:
        # Process result
        pass
"""

from .client import get_composio_client, composio_action, ComposioClientStub

__all__ = [
    'get_composio_client',
    'composio_action',
    'ComposioClientStub',
]
