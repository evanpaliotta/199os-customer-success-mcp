"""
Core Domain Tools

This domain contains 5 tools for core-related operations.

Tools:
  - register_client
  - get_client_overview
  - update_client_info
  - list_clients
  - get_client_timeline

Usage:
    from src.tools.core import register_client

    result = await register_client(ctx, client_id, ...)
"""

# Import all tools from this domain
from .register_client import register_client
from .get_client_overview import get_client_overview
from .update_client_info import update_client_info
from .list_clients import list_clients
from .get_client_timeline import get_client_timeline

__all__ = [
    "register_client",
    "get_client_overview",
    "update_client_info",
    "list_clients",
    "get_client_timeline",
]
