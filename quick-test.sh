#!/bin/bash
# Quick MCP Testing Script
# Automatically sets up clean testing environment

set -e

PROJECT_DIR="/Users/evanpaliotta/199os-customer-success-mcp"
cd "$PROJECT_DIR"

echo "🧹 Cleaning up old processes and cache..."

# Kill any orphaned server processes
pkill -f "199os-customer-success-mcp" 2>/dev/null || true
sleep 1

# Clear Python cache
echo "   → Clearing Python cache..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo "✅ Cleanup complete!"
echo ""
echo "🚀 Starting MCP Inspector..."
echo "   📝 Browser will open at http://localhost:5173"
echo "   🔄 Make code changes and click 'Reconnect' - no restarts needed!"
echo "   ⚡ Test individual tools instantly"
echo "   📖 See TESTING.md for full workflow guide"
echo ""
echo "Press Ctrl+C to stop testing"
echo ""

# Start the inspector
npx @modelcontextprotocol/inspector /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 server.py
