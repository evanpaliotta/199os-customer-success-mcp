# Communication Domain Tools

## Overview

This domain contains 6 tools for communication-related operations.

## Available Tools

### send_personalized_email
Create and send personalized email campaigns to customers.

Enables targeted, personalized email communications with advanced segmentation,
scheduling, and tracking capabilities. Supports various temp...

### automate_communications
Create and manage automated communication workflows.

Build sophisticated automation workflows that trigger communications based on
customer behaviors, lifecycle events, health changes, or time-based ...

### manage_community
Manage customer communities and networks.

Create and moderate customer communities including forums, user groups, advisory boards,
and champions programs. Track member engagement, facilitate discussi...

### manage_advocacy_program
Manage customer advocacy and reference programs.

Build and operate customer advocacy programs including case studies, testimonials,
references, speaking engagements, and referrals. Track advocate con...

### conduct_executive_review
Schedule and manage Executive Business Reviews (EBRs).

Plan, prepare, conduct, and follow up on executive business reviews with
strategic customers. Track QBRs, EBRs, and success reviews with compreh...

### automate_newsletters
Automate customer newsletter creation and distribution.

Create, schedule, and distribute newsletters to customer segments with rich content
sections, automated scheduling, performance tracking, and s...


## Usage

```python
from src.tools.communication import send_personalized_email

result = await send_personalized_email(ctx, client_id, ...)
```

## Progressive Discovery

These tools are organized for filesystem-based discovery. Claude can explore
this directory structure to find relevant tools on-demand, rather than loading
all tools upfront.

This enables 98.7% token savings (150K → 2K tokens on tool loading).
