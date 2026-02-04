#!/bin/bash
# Quick Start Script for Memory Engine MCP Server

set -e

echo "🚀 Memory Engine MCP Server - Quick Start"
echo "=========================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed"
    echo "   Install from: https://github.com/astral-sh/uv"
    exit 1
fi

echo "✅ uv found: $(uv --version)"
echo ""

# Check if dependencies are installed
if [ ! -d "/Users/noor/Builds/.venv" ]; then
    echo "📦 Installing dependencies..."
    uv sync
    echo ""
else
    echo "✅ Dependencies already installed"
    echo ""
fi

# Run test
echo "🧪 Running tests..."
uv run python tests/test_server.py
echo ""

# Show available commands
echo "📝 Available Commands:"
echo "   • Start MCP server:     uv run agent-memory"
echo "   • Test with inspector:  npx @modelcontextprotocol/inspector uv run agent-memory"
echo "   • Run tests:            uv run python tests/test_server.py"
echo ""

echo "📖 Documentation:"
echo "   • Setup guide:  cat SETUP.md"
echo "   • Full README:  cat README.md"
echo "   • MCP config:   cat mcp.json"
echo ""

# Offer to start the server
read -p "🤔 Start the MCP server now? (y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🎯 Starting MCP server..."
    echo "   (Press Ctrl+C to stop)"
    echo ""
    uv run agent-memory
fi
