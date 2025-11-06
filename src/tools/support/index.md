# Support Domain Tools

## Overview

This domain contains 6 tools for support-related operations.

## Available Tools

### handle_support_ticket
Process 108: Comprehensive support ticket handling and resolution.

Handles the complete ticket lifecycle from creation to resolution,
including updates, escalations, and customer satisfaction trackin...

### route_tickets
Process 109: Intelligent ticket routing and prioritization.

Routes tickets to appropriate teams/agents based on priority, category,
agent workload, expertise, and SLA requirements. Supports manual ro...

### manage_knowledge_base
Process 110: Knowledge base management for self-service support.

Manages the complete knowledge base lifecycle including article creation,
search, categorization, and analytics. Enables customers to ...

### update_knowledge_base
Process 111: Knowledge base updates and maintenance.

Updates existing KB articles including content, metadata, status,
and versioning. Tracks article effectiveness through voting and
manages publicat...

### manage_customer_portal
Process 112: Customer portal and self-service resource management.

Manages the customer self-service portal including access to knowledge
base, ticket submission, resource downloads, feature customiz...

### analyze_support_performance
Process 113: Support performance analytics and optimization.

Comprehensive support analytics including SLA compliance, ticket metrics,
agent performance, customer satisfaction, knowledge base effecti...


## Usage

```python
from src.tools.support import handle_support_ticket

result = await handle_support_ticket(ctx, client_id, ...)
```

## Progressive Discovery

These tools are organized for filesystem-based discovery. Claude can explore
this directory structure to find relevant tools on-demand, rather than loading
all tools upfront.

This enables 98.7% token savings (150K → 2K tokens on tool loading).
