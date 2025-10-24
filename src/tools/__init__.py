"""
Customer Success Tools Package
Registers all MCP tools organized by category
"""
import structlog

logger = structlog.get_logger(__name__)


def register_all_tools(mcp):
    """
    Register all Customer Success tools with the MCP server instance with comprehensive error handling.

    Args:
        mcp: FastMCP server instance
    """
    registered_count = 0
    failed_modules = []

    # Define all tool modules with error handling
    tool_modules = [
        ('autonomous_control_tools', 'Autonomous Control'),
        ('core_system_tools', 'Core System'),
        ('onboarding_training_tools', 'Onboarding & Training'),
        ('health_segmentation_tools', 'Health & Segmentation'),
        ('retention_risk_tools', 'Retention & Risk'),
        ('communication_engagement_tools', 'Communication & Engagement'),
        ('support_selfservice_tools', 'Support & Self-Service'),
        ('expansion_revenue_tools', 'Expansion & Revenue'),
        ('feedback_intelligence_tools', 'Feedback & Intelligence'),
    ]

    for module_name, display_name in tool_modules:
        try:
            # Dynamically import the module
            module = __import__(f'src.tools.{module_name}', fromlist=[module_name])

            # Register tools from this module
            if hasattr(module, 'register_tools'):
                module.register_tools(mcp)
                registered_count += 1
                logger.debug(f"✓ Registered {display_name} tools")
            else:
                logger.warning(f"⚠ Module {module_name} has no register_tools function")
                failed_modules.append((module_name, "No register_tools function"))

        except ImportError as e:
            logger.error(f"✗ Failed to import {module_name}: {e}")
            failed_modules.append((module_name, f"Import error: {e}"))
        except Exception as e:
            logger.error(f"✗ Failed to register {module_name}: {e}")
            failed_modules.append((module_name, f"Registration error: {e}"))

    # Log summary
    if failed_modules:
        logger.warning(
            f"Tool registration completed with errors: "
            f"{registered_count}/{len(tool_modules)} modules registered"
        )
        for module_name, error in failed_modules:
            logger.warning(f"  - {module_name}: {error}")
    else:
        logger.info(
            f"✓ All {registered_count} tool modules registered successfully"
        )
        print(f"✅ All {registered_count} tool modules registered with MCP")
