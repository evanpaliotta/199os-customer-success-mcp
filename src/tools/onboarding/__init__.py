"""
Onboarding Domain Tools

This domain contains 8 tools for onboarding-related operations.

Tools:
  - create_onboarding_plan
  - activate_onboarding_automation
  - deliver_training_session
  - manage_certification_program
  - optimize_onboarding_process
  - map_customer_journey
  - optimize_time_to_value
  - track_onboarding_progress

Usage:
    from src.tools.onboarding import create_onboarding_plan

    result = await create_onboarding_plan(ctx, client_id, ...)
"""

# Import all tools from this domain
from .create_onboarding_plan import create_onboarding_plan
from .activate_onboarding_automation import activate_onboarding_automation
from .deliver_training_session import deliver_training_session
from .manage_certification_program import manage_certification_program
from .optimize_onboarding_process import optimize_onboarding_process
from .map_customer_journey import map_customer_journey
from .optimize_time_to_value import optimize_time_to_value
from .track_onboarding_progress import track_onboarding_progress

__all__ = [
    "create_onboarding_plan",
    "activate_onboarding_automation",
    "deliver_training_session",
    "manage_certification_program",
    "optimize_onboarding_process",
    "map_customer_journey",
    "optimize_time_to_value",
    "track_onboarding_progress",
]
