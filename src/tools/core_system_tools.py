"""
Compatibility Module - Core System Tools

This module re-exports tools from the new filesystem-based structure
for backwards compatibility with existing tests.

New location: src/tools/core/*
"""

# Re-export all core tools
from .core.get_client_overview import get_client_overview
from .core.get_client_timeline import get_client_timeline
from .core.list_clients import list_clients
from .core.register_client import register_client
from .core.update_client_info import update_client_info

__all__ = [
    "get_client_overview",
    "get_client_timeline",
    "list_clients",
    "register_client",
    "update_client_info",
]
