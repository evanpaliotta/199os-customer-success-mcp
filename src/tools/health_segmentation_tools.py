"""
Compatibility Module - Health Segmentation Tools

This module re-exports tools from the new filesystem-based structure
for backwards compatibility with existing tests.

New locations: src/tools/retention/*, src/tools/expansion/*, src/tools/feedback/*
"""

# Re-export retention tools
from .retention.identify_churn_risk import identify_churn_risk
from .retention.manage_escalations import manage_escalations
from .retention.score_risk_factors import score_risk_factors
from .retention.automate_retention_campaigns import automate_retention_campaigns
from .retention.analyze_churn_postmortem import analyze_churn_postmortem
from .retention.execute_retention_campaign import execute_retention_campaign
from .retention.monitor_satisfaction import monitor_satisfaction

# Re-export expansion tools
from .expansion.track_renewals import track_renewals
from .expansion.identify_crosssell_opportunities import identify_crosssell_opportunities
from .expansion.forecast_renewals import forecast_renewals
from .expansion.negotiate_renewals import negotiate_renewals
from .expansion.identify_expansion_opportunities import identify_expansion_opportunities
from .expansion.track_revenue_expansion import track_revenue_expansion
from .expansion.identify_upsell_opportunities import identify_upsell_opportunities
from .expansion.optimize_customer_lifetime_value import optimize_customer_lifetime_value

# Re-export feedback tools
from .feedback.share_product_insights import share_product_insights
from .feedback.track_cs_metrics import track_cs_metrics
from .feedback.analyze_product_usage import analyze_product_usage
from .feedback.analyze_feedback_sentiment import analyze_feedback_sentiment
from .feedback.collect_feedback import collect_feedback
from .feedback.manage_voice_of_customer import manage_voice_of_customer

__all__ = [
    # Retention
    "identify_churn_risk",
    "manage_escalations",
    "score_risk_factors",
    "automate_retention_campaigns",
    "analyze_churn_postmortem",
    "execute_retention_campaign",
    "monitor_satisfaction",
    # Expansion
    "track_renewals",
    "identify_crosssell_opportunities",
    "forecast_renewals",
    "negotiate_renewals",
    "identify_expansion_opportunities",
    "track_revenue_expansion",
    "identify_upsell_opportunities",
    "optimize_customer_lifetime_value",
    # Feedback
    "share_product_insights",
    "track_cs_metrics",
    "analyze_product_usage",
    "analyze_feedback_sentiment",
    "collect_feedback",
    "manage_voice_of_customer",
]
