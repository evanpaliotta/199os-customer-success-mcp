"""
Expansion Domain Tools

This domain contains 8 tools for expansion-related operations.

Tools:
  - identify_upsell_opportunities
  - identify_crosssell_opportunities
  - identify_expansion_opportunities
  - track_renewals
  - forecast_renewals
  - negotiate_renewals
  - track_revenue_expansion
  - optimize_customer_lifetime_value

Usage:
    from src.tools.expansion import identify_upsell_opportunities

    result = await identify_upsell_opportunities(ctx, client_id, ...)
"""

# Import all tools from this domain
from .identify_upsell_opportunities import identify_upsell_opportunities
from .identify_crosssell_opportunities import identify_crosssell_opportunities
from .identify_expansion_opportunities import identify_expansion_opportunities
from .track_renewals import track_renewals
from .forecast_renewals import forecast_renewals
from .negotiate_renewals import negotiate_renewals
from .track_revenue_expansion import track_revenue_expansion
from .optimize_customer_lifetime_value import optimize_customer_lifetime_value

__all__ = [
    "identify_upsell_opportunities",
    "identify_crosssell_opportunities",
    "identify_expansion_opportunities",
    "track_renewals",
    "forecast_renewals",
    "negotiate_renewals",
    "track_revenue_expansion",
    "optimize_customer_lifetime_value",
]
