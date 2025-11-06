"""
CLI entry point for Customer Success MCP tools
Allows running tools as modules: python -m src.tools.onboarding_wizard
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # Check which tool is being run
    if "onboarding_wizard" in sys.modules['__main__'].__file__:
        from src.tools.onboarding_wizard import main
        main()
    else:
        print("Unknown tool. Available tools:")
        print("  python -m src.tools.onboarding_wizard")
        sys.exit(1)
