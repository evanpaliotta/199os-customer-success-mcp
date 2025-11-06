# Core Domain Tools

## Overview

This domain contains 5 tools for core-related operations.

## Available Tools

### register_client
Register a new customer client in the CS system.

Creates a new customer account with initial configuration, health score,
and lifecycle tracking. This is the entry point for all new customers.

Args:...

### get_client_overview
Get comprehensive overview of a client account.

Retrieves complete client status including health score, engagement metrics,
onboarding progress, support status, and revenue opportunities. This is th...

### update_client_info
Update client information and metadata.

Allows updating any client field including contact info, tier, contract details,
or custom metadata. Changes are logged for audit trail.

Args:
    client_id: ...

### list_clients
List all clients with optional filtering.

Retrieve a list of clients filtered by tier, lifecycle stage, health score range,
or other criteria. Supports pagination for large client bases.

Args:
    t...

### get_client_timeline
Get chronological timeline of client activity and events.

Retrieves all significant events in a client's lifecycle including onboarding
milestones, support tickets, product usage changes, health scor...


## Usage

```python
from src.tools.core import register_client

result = await register_client(ctx, client_id, ...)
```

## Progressive Discovery

These tools are organized for filesystem-based discovery. Claude can explore
this directory structure to find relevant tools on-demand, rather than loading
all tools upfront.

This enables 98.7% token savings (150K → 2K tokens on tool loading).
