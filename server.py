"""
199|OS Customer Success Operations MCP Server
Comprehensive Customer Success Platform

Process Categories:
- Onboarding & Training (Processes 79-86)
- Health Monitoring & Segmentation (Processes 87-94)
- Retention & Risk Management (Processes 95-101)
- Communication & Engagement (Processes 102-107)
- Support & Self-Service (Processes 108-113)
- Growth & Revenue Expansion (Processes 114-121)
- Feedback & Product Intelligence (Processes 122-127)
"""

from dotenv import load_dotenv
from src.initialization import initialize_all

# Load environment variables
load_dotenv()

# Initialize entire system (logging, MCP server, agents, tools)
# Skip validation for MCP testing (no database required)
mcp, adaptive_agent, enhanced_agent, logger = initialize_all(skip_validation=True)

# Main entry point
if __name__ == "__main__":
    mcp.run()
