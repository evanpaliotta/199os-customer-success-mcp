#!/bin/bash
# Quick MCP Inspector launcher for testing
# Usage: ./dev-test.sh

cd "$(dirname "$0")"

echo "🚀 Starting MCP Inspector for Customer Success MCP..."
echo "📝 This will open in your browser at http://localhost:5173"
echo "🔄 Make code changes and refresh the browser - no restarts needed!"
echo ""

npx @modelcontextprotocol/inspector /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 server.py
