"""
Support Domain Tools

This domain contains 6 tools for support-related operations.

Tools:
  - handle_support_ticket
  - route_tickets
  - manage_knowledge_base
  - update_knowledge_base
  - manage_customer_portal
  - analyze_support_performance

Usage:
    from src.tools.support import handle_support_ticket

    result = await handle_support_ticket(ctx, client_id, ...)
"""

# Import all tools from this domain
from .handle_support_ticket import handle_support_ticket
from .route_tickets import route_tickets
from .manage_knowledge_base import manage_knowledge_base
from .update_knowledge_base import update_knowledge_base
from .manage_customer_portal import manage_customer_portal
from .analyze_support_performance import analyze_support_performance

__all__ = [
    "handle_support_ticket",
    "route_tickets",
    "manage_knowledge_base",
    "update_knowledge_base",
    "manage_customer_portal",
    "analyze_support_performance",
]
