#!/bin/bash
# Centre-AI MCP Configuration Generator
# Automatically generates MCP server configuration

# Configuration
MCP_SERVER_NAME="${1:-centre-ai}"
SERVER_HOST="${2:-cnull.net}"
SERVER_PORT="${3:-22068}"
OUTPUT_FILE="${4:-mcp-config.json}"

# Detect local IP if needed
if [[ "$SERVER_HOST" == "auto" ]]; then
    SERVER_HOST=$(hostname -I | awk '{print $1}')
fi

# Generate MCP configuration
cat > "$OUTPUT_FILE" << EOF
{
  "mcpServers": {
    "$MCP_SERVER_NAME": {
      "transport": {
        "type": "sse",
        "url": "http://$SERVER_HOST:$SERVER_PORT/sse"
      },
      "capabilities": {
        "resources": true,
        "tools": true,
        "prompts": true
      }
    }
  }
}
EOF

echo "✅ MCP Configuration generated:"
echo "   File: $OUTPUT_FILE"
echo "   Server: $MCP_SERVER_NAME"
echo "   URL: http://$SERVER_HOST:$SERVER_PORT/sse"
echo ""
echo "Usage in Claude Desktop:"
echo "   Copy content to ~/.config/claude-desktop/config.json"
echo ""
cat "$OUTPUT_FILE"