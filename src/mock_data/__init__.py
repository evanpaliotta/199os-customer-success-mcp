"""
DEPRECATED: Mock data has been moved to tests/fixtures/mock_data/

This stub module provides backward compatibility for existing tool imports.
In Phase 2-3, all tools will be migrated to use Composio for real data.

For tests, import from: tests.fixtures.mock_data
"""

# Import from test fixtures to maintain backward compatibility temporarily
import sys
from pathlib import Path

# Add tests directory to path
tests_path = Path(__file__).parent.parent.parent / 'tests'
if str(tests_path) not in sys.path:
    sys.path.insert(0, str(tests_path))

# Re-export from test fixtures
from fixtures.mock_data.generators import *  # noqa

__all__ = ['generators']
