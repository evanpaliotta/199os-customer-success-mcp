# Retention Domain Tools

## Overview

This domain contains 7 tools for retention-related operations.

## Available Tools

### identify_churn_risk
Process 95: Identify customers at risk of churn with probability scores.

Args:
    client_id: Specific client to analyze (optional, analyzes all if None)
    health_score_threshold: Health score thre...

### execute_retention_campaign
Process 96: Execute targeted retention interventions.

Args:
    client_id: Target customer
    campaign_type: Type (proactive_outreach, value_reinforcement, success_planning, etc.)
    intervention_l...

### monitor_satisfaction
Process 97: Monitor customer satisfaction with surveys.

Args:
    client_id: Specific client (optional)
    survey_type: Type (nps, csat, ces)
    time_period_days: Analysis period
    
Returns:
    ...

### manage_escalations
Process 98: Manage customer escalations with resolution workflows.

Args:
    action: Action (list, create, update, resolve, close)
    escalation_id: Escalation ID for specific actions
    client_id:...

### analyze_churn_postmortem
Process 99: Analyze churned customers to improve retention.

Args:
    client_id: Churned customer ID
    churn_date: Date of churn (YYYY-MM-DD)
    
Returns:
    Churn analysis with lessons learned...

### score_risk_factors
Process 100: Systematically identify and score risk factors.

Args:
    client_id: Customer to analyze
    
Returns:
    Comprehensive risk scoring with predictive modeling...

### automate_retention_campaigns
Process 101: Automatically trigger retention campaigns based on signals.

Args:
    trigger_type: Trigger (health_score, usage_decline, nps_detractor, renewal_risk)
    threshold: Threshold value for ...


## Usage

```python
from src.tools.retention import identify_churn_risk

result = await identify_churn_risk(ctx, client_id, ...)
```

## Progressive Discovery

These tools are organized for filesystem-based discovery. Claude can explore
this directory structure to find relevant tools on-demand, rather than loading
all tools upfront.

This enables 98.7% token savings (150K → 2K tokens on tool loading).
