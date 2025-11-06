# Onboarding Domain Tools

## Overview

This domain contains 8 tools for onboarding-related operations.

## Available Tools

### create_onboarding_plan
Process 79: Create Onboarding Plans & Timelines

Creates a customized onboarding plan with clear milestones, timelines,
and success metrics for each customer. This ensures structured activation
and re...

### activate_onboarding_automation
Process 80: Customer Onboarding Automation & Workflows

Activates automated onboarding workflows with progress tracking, milestone
completion notifications, and quality assurance checks. Scales onboar...

### deliver_training_session
Process 81: Teach Customers Effectively (Training Delivery)

Delivers effective training programs with competency verification, engagement
tracking, and outcome achievement. Ensures customers can effe...

### manage_certification_program
Process 82: Customer Education & Certification Programs

Manages comprehensive education programs with certification tracking,
competency verification, and adoption improvement. Develops customer
expe...

### optimize_onboarding_process
Process 83: Get Better at Onboarding (Process Optimization)

Continuously improves onboarding effectiveness based on customer feedback,
success rates, and time-to-value data. Identifies optimization o...

### map_customer_journey
Process 84: Customer Journey Mapping & Milestone Tracking

Visualizes and optimizes the customer experience throughout their lifecycle.
Maps all touchpoints, interactions, milestones, and experience m...

### optimize_time_to_value
Process 85: Time-to-Value Optimization & Measurement

Minimizes the time required for customers to achieve meaningful value from
the product. Provides measurement frameworks, benchmark tracking, and
o...

### track_onboarding_progress
Process 86: Onboarding Success Metrics & Reporting

Tracks onboarding effectiveness and identifies improvement opportunities.
Provides comprehensive progress reports with metrics, risk analysis, and
p...


## Usage

```python
from src.tools.onboarding import create_onboarding_plan

result = await create_onboarding_plan(ctx, client_id, ...)
```

## Progressive Discovery

These tools are organized for filesystem-based discovery. Claude can explore
this directory structure to find relevant tools on-demand, rather than loading
all tools upfront.

This enables 98.7% token savings (150K → 2K tokens on tool loading).
