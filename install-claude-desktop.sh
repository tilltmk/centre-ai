#!/bin/bash
# Installation script for Centre AI MCP stdio wrapper for Claude Desktop

set -e

echo "🚀 Centre AI MCP Server - Claude Desktop Setup"
echo "================================================"

# Detect OS and config location
if [[ "$OSTYPE" == "darwin"* ]]; then
    CONFIG_DIR="$HOME/Library/Application Support/Claude"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CONFIG_DIR="$HOME/.config/Claude"
else
    echo "❌ Unsupported OS: $OSTYPE"
    exit 1
fi

CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WRAPPER_PATH="$SCRIPT_DIR/mcp_stdio_wrapper.py"

# Make wrapper executable
chmod +x "$WRAPPER_PATH"

echo ""
echo "📝 Configuration"
echo "---------------"

# Get server URL
read -p "MCP Server URL [http://localhost:3001]: " SERVER_URL
SERVER_URL=${SERVER_URL:-http://localhost:3001}

# Get auth token
read -p "MCP Auth Token: " AUTH_TOKEN

if [ -z "$AUTH_TOKEN" ]; then
    echo "❌ Auth token is required!"
    exit 1
fi

# Create config directory if needed
mkdir -p "$CONFIG_DIR"

# Check if config exists
if [ -f "$CONFIG_FILE" ]; then
    echo ""
    echo "⚠️  Existing configuration found"
    read -p "Backup existing config? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        echo "✅ Backup created"
    fi

    # Read existing config
    EXISTING_CONFIG=$(cat "$CONFIG_FILE")
else
    EXISTING_CONFIG='{}'
fi

# Create new config with centre-ai server
NEW_CONFIG=$(echo "$EXISTING_CONFIG" | python3 -c "
import sys, json

config = json.load(sys.stdin)
if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['centre-ai'] = {
    'command': 'python3',
    'args': ['$WRAPPER_PATH'],
    'env': {
        'MCP_SERVER_URL': '$SERVER_URL',
        'MCP_AUTH_TOKEN': '$AUTH_TOKEN'
    }
}

print(json.dumps(config, indent=2))
")

# Write config
echo "$NEW_CONFIG" > "$CONFIG_FILE"

echo ""
echo "✅ Installation Complete!"
echo ""
echo "📋 Configuration Details:"
echo "  Config file: $CONFIG_FILE"
echo "  Wrapper:     $WRAPPER_PATH"
echo "  Server URL:  $SERVER_URL"
echo ""
echo "🔄 Next Steps:"
echo "  1. Restart Claude Desktop"
echo "  2. The 'centre-ai' MCP server should appear in Claude"
echo "  3. Check logs in Claude Desktop if there are issues"
echo ""
echo "💡 Tips:"
echo "  - View config: cat \"$CONFIG_FILE\""
echo "  - Test wrapper: python3 \"$WRAPPER_PATH\""
echo "  - Check server: curl $SERVER_URL/health"
echo ""
