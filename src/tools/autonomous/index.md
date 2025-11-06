# Autonomous Domain Tools

## Overview

This domain contains 5 tools for autonomous-related operations.

## Available Tools

### get_autonomous_status
Get status of all autonomous workers

Returns:
    Status of autonomous system and all workers...

### configure_autonomous_worker
Enable/disable a worker or update its parameters

Args:
    worker_name: Name of worker (e.g., "deal_risk_monitor")
    enabled: True to enable, False to disable
    params: Optional dict of parameter...

### trigger_worker_now
Manually trigger a worker to run immediately

Args:
    worker_name: Name of worker to trigger

Returns:
    Worker execution results...

### get_worker_config
Get configuration for a specific worker

Args:
    worker_name: Name of worker

Returns:
    Worker configuration...

### list_available_workers
List all available autonomous workers

Returns:
    List of all workers with descriptions and status...


## Usage

```python
from src.tools.autonomous import get_autonomous_status

result = await get_autonomous_status(ctx, client_id, ...)
```

## Progressive Discovery

These tools are organized for filesystem-based discovery. Claude can explore
this directory structure to find relevant tools on-demand, rather than loading
all tools upfront.

This enables 98.7% token savings (150K → 2K tokens on tool loading).
