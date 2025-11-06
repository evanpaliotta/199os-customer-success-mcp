"""
Retention Domain Tools

This domain contains 7 tools for retention-related operations.

Tools:
  - identify_churn_risk
  - execute_retention_campaign
  - monitor_satisfaction
  - manage_escalations
  - analyze_churn_postmortem
  - score_risk_factors
  - automate_retention_campaigns

Usage:
    from src.tools.retention import identify_churn_risk

    result = await identify_churn_risk(ctx, client_id, ...)
"""

# Import all tools from this domain
from .identify_churn_risk import identify_churn_risk
from .execute_retention_campaign import execute_retention_campaign
from .monitor_satisfaction import monitor_satisfaction
from .manage_escalations import manage_escalations
from .analyze_churn_postmortem import analyze_churn_postmortem
from .score_risk_factors import score_risk_factors
from .automate_retention_campaigns import automate_retention_campaigns

__all__ = [
    "identify_churn_risk",
    "execute_retention_campaign",
    "monitor_satisfaction",
    "manage_escalations",
    "analyze_churn_postmortem",
    "score_risk_factors",
    "automate_retention_campaigns",
]
