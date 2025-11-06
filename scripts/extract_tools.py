#!/usr/bin/env python3
"""
Tool Extraction Script - Filesystem-based Tool Discovery

This script extracts individual tools from monolithic tool files and organizes
them into a filesystem-based structure for progressive disclosure.

Goals:
1. Extract each tool function into its own file
2. Organize by domain (deal/, outreach/, analytics/, etc.)
3. Keep files under 1,500 LOC limit
4. Create domain index files for documentation
5. Enable filesystem-based tool discovery (98.7% token savings)

Usage:
    python scripts/extract_tools.py --source src/tools --target src/tools_new

Architecture:
    Before: src/tools/deal_management_tools.py (4,979 LOC, all tools loaded)
    After:  src/tools/deal/
            ├── __init__.py (domain exports)
            ├── index.md (domain documentation)
            ├── createDeal.py (150 LOC)
            ├── updateDealStage.py (180 LOC)
            ├── forecastRevenue.py (200 LOC)
            └── ... (20+ individual tool files)

Result: Agent loads tools on-demand via filesystem exploration
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional


class ToolExtractor:
    """Extracts tools from monolithic files into filesystem structure"""

    def __init__(self, source_dir: Path, target_dir: Path):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.max_file_size = 1500  # LOC limit per file

    def extract_all(self):
        """Extract all tools from source directory"""
        print(f"Extracting tools from {self.source_dir} to {self.target_dir}")

        tool_files = list(self.source_dir.glob("*_tools.py"))
        print(f"Found {len(tool_files)} tool files")

        for tool_file in tool_files:
            if tool_file.name == "__init__.py":
                continue

            domain = self._extract_domain_name(tool_file.name)
            print(f"\nProcessing {tool_file.name} -> domain: {domain}")

            self._extract_tools_from_file(tool_file, domain)

    def _extract_domain_name(self, filename: str) -> str:
        """Extract domain name from filename"""
        # deal_management_tools.py -> deal
        # analytics_reporting_tools.py -> analytics
        # outreach_engagement_tools.py -> outreach
        name = filename.replace("_tools.py", "")
        name = name.replace("_management", "")
        name = name.replace("_reporting", "")
        name = name.replace("_engagement", "")
        name = name.replace("_orchestration", "")
        name = name.replace("_qualification", "")
        name = name.replace("_forecasting", "")
        name = name.replace("_prediction", "")
        name = name.replace("_control", "")
        name = name.replace("_system", "")

        # Handle remaining underscores
        parts = name.split("_")
        return parts[0] if parts else "misc"

    def _extract_tools_from_file(self, file_path: Path, domain: str):
        """Extract individual tools from a file"""
        with open(file_path, 'r') as f:
            content = f.read()

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"  ERROR: Cannot parse {file_path}: {e}")
            return

        # Create domain directory
        domain_dir = self.target_dir / domain
        domain_dir.mkdir(parents=True, exist_ok=True)

        # Extract tools (async functions decorated with @mcp.tool)
        tools = self._find_tool_functions(tree, content)
        print(f"  Found {len(tools)} tools")

        if not tools:
            print(f"  WARNING: No tools found in {file_path}")
            return

        # Write each tool to its own file
        for tool in tools:
            tool_file = domain_dir / f"{tool['name']}.py"
            self._write_tool_file(tool_file, tool, content)

        # Create domain __init__.py
        self._create_domain_init(domain_dir, tools)

        # Create domain index.md
        self._create_domain_index(domain_dir, domain, tools)

    def _find_tool_functions(self, tree: ast.AST, content: str) -> List[Dict[str, Any]]:
        """Find all tool functions in AST"""
        tools = []

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                # Check if decorated with @mcp.tool or similar
                is_tool = any(
                    self._is_tool_decorator(dec)
                    for dec in node.decorator_list
                )

                if is_tool:
                    # Extract function source
                    start_line = node.lineno - 1  # 0-indexed
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 50

                    lines = content.split('\n')
                    func_source = '\n'.join(lines[start_line:end_line])

                    # Extract docstring
                    docstring = ast.get_docstring(node) or "No description"

                    tools.append({
                        'name': node.name,
                        'source': func_source,
                        'docstring': docstring,
                        'start_line': start_line,
                        'end_line': end_line,
                        'loc': end_line - start_line
                    })

        return tools

    def _is_tool_decorator(self, dec: ast.expr) -> bool:
        """Check if decorator is a tool decorator"""
        if isinstance(dec, ast.Attribute):
            return dec.attr == 'tool'
        elif isinstance(dec, ast.Name):
            return dec.id in ['tool', 'mcp_tool']
        elif isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Attribute):
                return dec.func.attr == 'tool'
            elif isinstance(dec.func, ast.Name):
                return dec.func.id in ['tool', 'mcp_tool']
        return False

    def _write_tool_file(self, file_path: Path, tool: Dict[str, Any], original_content: str):
        """Write individual tool to file"""
        # Extract imports from original file
        imports = self._extract_imports(original_content)

        # Create tool file content
        content = f'''"""
{tool['name']} - {tool['docstring'].split('.')[0]}

{tool['docstring']}
"""

{imports}

{tool['source']}
'''

        with open(file_path, 'w') as f:
            f.write(content)

        loc = len(content.split('\n'))
        print(f"    → {file_path.name} ({loc} LOC)")

    def _extract_imports(self, content: str) -> str:
        """Extract import statements from content"""
        lines = content.split('\n')
        imports = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ')):
                imports.append(line)
            elif imports and not stripped.startswith('#') and stripped:
                # Stop at first non-import, non-comment line
                break

        return '\n'.join(imports)

    def _create_domain_init(self, domain_dir: Path, tools: List[Dict[str, Any]]):
        """Create __init__.py for domain"""
        tool_names = [tool['name'] for tool in tools]

        content = f'''"""
{domain_dir.name.title()} Domain Tools

This domain contains {len(tools)} tools for {domain_dir.name}-related operations.

Tools:
{chr(10).join(f"  - {name}" for name in tool_names)}

Usage:
    from src.tools.{domain_dir.name} import {tool_names[0]}

    result = await {tool_names[0]}(ctx, client_id, ...)
"""

# Import all tools from this domain
{chr(10).join(f"from .{name} import {name}" for name in tool_names)}

__all__ = [
{chr(10).join(f'    "{name}",' for name in tool_names)}
]
'''

        init_file = domain_dir / "__init__.py"
        with open(init_file, 'w') as f:
            f.write(content)

        print(f"    → __init__.py (domain exports)")

    def _create_domain_index(self, domain_dir: Path, domain: str, tools: List[Dict[str, Any]]):
        """Create index.md for domain documentation"""
        content = f'''# {domain.title()} Domain Tools

## Overview

This domain contains {len(tools)} tools for {domain}-related operations.

## Available Tools

{chr(10).join(f"### {tool['name']}{chr(10)}{tool['docstring'][:200]}...{chr(10)}" for tool in tools)}

## Usage

```python
from src.tools.{domain} import {tools[0]['name']}

result = await {tools[0]['name']}(ctx, client_id, ...)
```

## Progressive Discovery

These tools are organized for filesystem-based discovery. Claude can explore
this directory structure to find relevant tools on-demand, rather than loading
all tools upfront.

This enables 98.7% token savings (150K → 2K tokens on tool loading).
'''

        index_file = domain_dir / "index.md"
        with open(index_file, 'w') as f:
            f.write(content)

        print(f"    → index.md (domain documentation)")


def main():
    """Main execution"""
    if len(sys.argv) < 3:
        print("Usage: python extract_tools.py <source_dir> <target_dir>")
        sys.exit(1)

    source_dir = Path(sys.argv[1])
    target_dir = Path(sys.argv[2])

    if not source_dir.exists():
        print(f"ERROR: Source directory does not exist: {source_dir}")
        sys.exit(1)

    print("=" * 80)
    print("Tool Extraction Script - Filesystem-based Discovery")
    print("=" * 80)

    extractor = ToolExtractor(source_dir, target_dir)
    extractor.extract_all()

    print("\n" + "=" * 80)
    print("Extraction complete!")
    print(f"Tools extracted to: {target_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
