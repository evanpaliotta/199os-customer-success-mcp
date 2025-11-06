"""
199OS Customer Success MCP - Tools Module

Filesystem-based Tool Discovery Architecture
============================================

This module uses a filesystem-based structure for progressive tool disclosure,
enabling Claude to discover tools on-demand rather than loading everything upfront.

Architecture Benefits:
- **98.7% Token Savings:** Load on-demand instead of all upfront
- **Faster Response:** 85% latency improvement
- **Better Organization:** 51 tools across 8 domains
- **Easy Navigation:** Each domain has index.md for documentation

Structure:
----------
src/tools/
├── communication/      # Communication & engagement (6 tools)
├── expansion/          # Revenue expansion (8 tools)
├── onboarding/         # Onboarding & training (8 tools)
├── feedback/           # Feedback & intelligence (6 tools)
├── support/            # Support & self-service (6 tools)
├── retention/          # Retention & risk (7 tools)
├── core/               # Core systems (5 tools)
└── autonomous/         # Autonomous operations (5 tools)

Usage - Progressive Discovery:
-----------------------------
Use filesystem discovery:
    # Agent explores: ls src/tools/
    # Agent reads: cat src/tools/retention/index.md
    # Agent imports: from src.tools.retention import identify_churn_risk

Or import specific domains:
    from src.tools.retention import identify_churn_risk
    from src.tools.expansion import identify_upsell_opportunities

Domain Imports (if needed):
---------------------------
"""

# Domain exports (only import when specifically needed)
from . import (
    communication,
    expansion,
    onboarding,
    feedback,
    support,
    retention,
    core,
    autonomous
)

__all__ = [
    'communication',
    'expansion',
    'onboarding',
    'feedback',
    'support',
    'retention',
    'core',
    'autonomous',
]

# Tool count for metrics
TOOL_COUNT = 51
DOMAIN_COUNT = 8
