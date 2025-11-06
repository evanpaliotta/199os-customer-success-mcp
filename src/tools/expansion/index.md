# Expansion Domain Tools

## Overview

This domain contains 8 tools for expansion-related operations.

## Available Tools

### identify_upsell_opportunities
Process 114: Identify upsell opportunities based on usage and health.

Args:
    client_id: Specific client (optional, analyzes all if None)
    min_health_score: Minimum health for upsell considerati...

### identify_crosssell_opportunities
Process 115: Identify cross-sell opportunities for additional products.

Args:
    client_id: Specific client (optional)
    product_family: Product category to analyze
    
Returns:
    Cross-sell op...

### identify_expansion_opportunities
Process 116: Systematically identify all expansion opportunities.

Args:
    client_id: Specific client (optional)
    opportunity_types: Types to analyze (user_expansion, usage_expansion, etc.)
    
...

### track_renewals
Process 117: Track renewal dates with automated reminders.

Args:
    client_id: Specific client (optional)
    days_until_renewal: Include renewals within this many days
    
Returns:
    Renewal tra...

### forecast_renewals
Process 118: Forecast renewal likelihood and prepare strategies.

Args:
    forecast_period_days: Forecast window
    include_risk_analysis: Include detailed risk assessment
    
Returns:
    Renewal ...

### negotiate_renewals
Process 119: Support renewal negotiations with strategies and pricing.

Args:
    client_id: Customer negotiating renewal
    negotiation_strategy: Strategy (value_reinforcement, competitive_defense, ...

### track_revenue_expansion
Process 120: Track and report revenue expansion from existing customers.

Args:
    time_period: Period (monthly, quarterly, annual)
    include_pipeline: Include future pipeline
    
Returns:
    Rev...

### optimize_customer_lifetime_value
Process 121: Optimize customer lifetime value through targeted strategies.

Args:
    client_id: Specific client (optional)
    optimization_focus: Focus (retention, expansion, efficiency, balanced)
 ...


## Usage

```python
from src.tools.expansion import identify_upsell_opportunities

result = await identify_upsell_opportunities(ctx, client_id, ...)
```

## Progressive Discovery

These tools are organized for filesystem-based discovery. Claude can explore
this directory structure to find relevant tools on-demand, rather than loading
all tools upfront.

This enables 98.7% token savings (150K → 2K tokens on tool loading).
