# Feedback Domain Tools

## Overview

This domain contains 6 tools for feedback-related operations.

## Available Tools

### collect_feedback
Collect and process customer feedback from any source.

PROCESS 122: Systematic feedback collection across all channels
(surveys, in-app, email, calls, support tickets, social media).

This tool captu...

### analyze_feedback_sentiment
Analyze sentiment across customer feedback for insights and trends.

PROCESS 123: Comprehensive sentiment analysis across all feedback sources
with theme extraction, trend identification, and actionab...

### share_product_insights
Share curated product insights with product team based on customer feedback.

PROCESS 124: Aggregate and synthesize feedback into actionable product insights
for product team consumption. Includes con...

### track_cs_metrics
Track and analyze key Customer Success metrics and KPIs.

PROCESS 125: Comprehensive CS metrics tracking with trends, benchmarks,
and segmentation. Monitors health of customer success operations.

Tra...

### analyze_product_usage
Analyze product usage patterns and feature adoption for a customer.

PROCESS 126: Comprehensive usage analytics including feature adoption,
user engagement, integration usage, and behavioral patterns....

### manage_voice_of_customer
Manage comprehensive Voice of Customer (VoC) program.

PROCESS 127: End-to-end VoC program management including report generation,
feedback loop tracking, program effectiveness measurement, and roadma...


## Usage

```python
from src.tools.feedback import collect_feedback

result = await collect_feedback(ctx, client_id, ...)
```

## Progressive Discovery

These tools are organized for filesystem-based discovery. Claude can explore
this directory structure to find relevant tools on-demand, rather than loading
all tools upfront.

This enables 98.7% token savings (150K → 2K tokens on tool loading).
