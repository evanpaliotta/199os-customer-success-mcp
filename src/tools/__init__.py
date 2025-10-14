"""
Customer Success Tools Package
Registers all MCP tools organized by category
"""

def register_all_tools(mcp):
    """
    Register all Customer Success tools with the MCP server instance.

    Args:
        mcp: FastMCP server instance
    """
    # Import and register each tool category
    from src.tools import autonomous_control_tools
    from src.tools import core_system_tools
    from src.tools import onboarding_training_tools
    from src.tools import health_segmentation_tools
    from src.tools import retention_risk_tools
    from src.tools import communication_engagement_tools
    from src.tools import support_selfservice_tools
    from src.tools import expansion_revenue_tools
    from src.tools import feedback_intelligence_tools

    # Register each category
    autonomous_control_tools.register_tools(mcp)
    core_system_tools.register_tools(mcp)
    onboarding_training_tools.register_tools(mcp)
    health_segmentation_tools.register_tools(mcp)
    retention_risk_tools.register_tools(mcp)
    communication_engagement_tools.register_tools(mcp)
    support_selfservice_tools.register_tools(mcp)
    expansion_revenue_tools.register_tools(mcp)
    feedback_intelligence_tools.register_tools(mcp)
