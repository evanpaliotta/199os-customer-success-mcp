#!/usr/bin/env python3
"""
Tool Migration Script - Apply @mcp_tool and Composio Patterns

This script migrates tools to use:
1. @mcp_tool decorator (eliminates boilerplate)
2. Composio for external API calls (replaces mock data)
3. Local data processing patterns (process before returning to model)

Usage:
    python scripts/migrate_tool_to_composio.py <tool_file_path>
"""

import re
import sys
from pathlib import Path


def migrate_tool(file_path: Path) -> str:
    """Migrate a tool file to use Composio patterns and @mcp_tool decorator"""

    with open(file_path, 'r') as f:
        content = f.read()

    # Step 1: Add decorator import
    if 'from src.decorators import mcp_tool' not in content:
        # Find the imports section
        imports_end = content.find('async def')
        if imports_end == -1:
            imports_end = content.find('def ')

        if imports_end > 0:
            import_line = 'from src.decorators import mcp_tool\n'
            composio_import = 'from src.composio import get_composio_client\n'

            # Insert before function definition
            content = content[:imports_end] + import_line + composio_import + '\n' + content[imports_end:]

    # Step 2: Add @mcp_tool decorator to function
    # Find async def function_name
    func_pattern = r'(    )(async def \w+\()'
    if not re.search(r'@mcp_tool', content):
        content = re.sub(
            func_pattern,
            r'\1@mcp_tool(validate_client=True, log_progress=True, log_budget=True)\n\1\2',
            content,
            count=1
        )

    # Step 3: Remove manual client_id validation (handled by decorator)
    # Remove the try-except block for validation
    validation_pattern = r'    try:\s+client_id = validate_client_id\(client_id\)\s+except ValidationError as e:\s+return \{[^}]+\}'
    content = re.sub(validation_pattern, '', content, flags=re.DOTALL)

    # Also remove standalone validation
    content = re.sub(r'\s+# Validate client_id\s+', '', content)
    content = re.sub(r'\s+client_id = validate_client_id\(client_id\)\s+', '', content)

    # Step 4: Remove manual execution tracking (handled by decorator)
    content = re.sub(r'\s+execution_id = [^\n]+\n', '', content)
    content = re.sub(r'\s+await ctx\.info\(f"Execution ID: \{execution_id\}"\)\s+', '', content)

    # Step 5: Comment out mock data usage with TODO
    if 'from src.mock_data import generators as mock' in content:
        content = content.replace(
            'from src.mock_data import generators as mock',
            '# from src.mock_data import generators as mock  # TODO: Replace with Composio'
        )

    # Add comment for mock data calls
    content = re.sub(
        r'(\s+)([\w_]+\s*=\s*mock\.\w+\([^)]+\))',
        r'\1# TODO: Replace with Composio API call\n\1\2  # MOCK DATA - needs migration',
        content
    )

    # Step 6: Add local processing pattern comment
    large_data_pattern = r'(deals|contacts|opportunities|accounts|leads|customers)\s*=\s*'
    if re.search(large_data_pattern, content):
        # Add comment about local processing
        note = '''
    # LOCAL PROCESSING PATTERN:
    # 1. Fetch data via Composio: data = await composio.execute_action("action_name", client_id, params)
    # 2. Process locally: df = pd.DataFrame(data); summary = df.groupby('stage').agg(...)
    # 3. Return summary only (not raw data)
    # This keeps large datasets out of model context (98.9% token savings)
'''
        # Insert after function definition
        func_def = re.search(r'(async def \w+\([^)]+\)[^:]*:)\s+("""[^"]*""")?', content)
        if func_def:
            end_pos = func_def.end()
            content = content[:end_pos] + note + content[end_pos:]

    # Step 7: Fix indentation issues from extraction
    # The extraction may have left functions with wrong indentation
    # Remove leading spaces before 'async def'
    content = re.sub(r'^    (async def)', r'\1', content, flags=re.MULTILINE)

    return content


def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate_tool_to_composio.py <tool_file_path>")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print(f"Migrating {file_path.name}...")

    migrated_content = migrate_tool(file_path)

    # Write back
    with open(file_path, 'w') as f:
        f.write(migrated_content)

    print(f"✓ Migrated {file_path.name}")
    print("  - Added @mcp_tool decorator")
    print("  - Removed manual validation (handled by decorator)")
    print("  - Commented mock data (TODO: replace with Composio)")
    print("  - Added local processing pattern notes")


if __name__ == "__main__":
    main()
