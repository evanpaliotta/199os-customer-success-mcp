"""
Communication Domain Tools

This domain contains 6 tools for communication-related operations.

Tools:
  - send_personalized_email
  - automate_communications
  - manage_community
  - manage_advocacy_program
  - conduct_executive_review
  - automate_newsletters

Usage:
    from src.tools.communication import send_personalized_email

    result = await send_personalized_email(ctx, client_id, ...)
"""

# Import all tools from this domain
from .send_personalized_email import send_personalized_email
from .automate_communications import automate_communications
from .manage_community import manage_community
from .manage_advocacy_program import manage_advocacy_program
from .conduct_executive_review import conduct_executive_review
from .automate_newsletters import automate_newsletters

__all__ = [
    "send_personalized_email",
    "automate_communications",
    "manage_community",
    "manage_advocacy_program",
    "conduct_executive_review",
    "automate_newsletters",
]
