#!/bin/bash
# Centre AI MCP Client Installer
# Downloads and sets up the Centre AI client from Git

set -e

CLIENT_NAME="centre-ai-client"
INSTALL_DIR="$HOME/.local/bin"
CLIENT_DIR="$HOME/.local/share/centre-ai-client"

echo "🤖 Centre AI MCP Client Installer"
echo "================================="

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$CLIENT_DIR"

echo "📥 Downloading Centre AI client..."

# Configuration
REPO_BASE_URL="${CENTRE_AI_REPO_URL:-https://raw.githubusercontent.com/your-org/centre-ai/main}"

# Download client files
if command -v curl >/dev/null 2>&1; then
    curl -L -o "$CLIENT_DIR/centre_ai_client.py" \
        "$REPO_BASE_URL/client/centre_ai_client.py"
    curl -L -o "$CLIENT_DIR/requirements.txt" \
        "$REPO_BASE_URL/client/requirements.txt"
elif command -v wget >/dev/null 2>&1; then
    wget -O "$CLIENT_DIR/centre_ai_client.py" \
        "$REPO_BASE_URL/client/centre_ai_client.py"
    wget -O "$CLIENT_DIR/requirements.txt" \
        "$REPO_BASE_URL/client/requirements.txt"
else
    echo "❌ Error: curl or wget required for download"
    exit 1
fi

# Make executable
chmod +x "$CLIENT_DIR/centre_ai_client.py"

# Create wrapper script
cat > "$INSTALL_DIR/$CLIENT_NAME" << 'EOF'
#!/bin/bash
# Centre AI Client Wrapper
CLIENT_DIR="$HOME/.local/share/centre-ai-client"
PYTHON_CMD="python3"

# Check if python3 is available
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Error: Python 3 is required"
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import httpx, websockets" >/dev/null 2>&1; then
    echo "📦 Installing dependencies..."
    if command -v pip3 >/dev/null 2>&1; then
        pip3 install --user -r "$CLIENT_DIR/requirements.txt"
    elif command -v pip >/dev/null 2>&1; then
        pip install --user -r "$CLIENT_DIR/requirements.txt"
    else
        echo "❌ Error: pip required to install dependencies"
        echo "Install manually: pip install httpx websockets"
        exit 1
    fi
fi

# Run client
exec python3 "$CLIENT_DIR/centre_ai_client.py" "$@"
EOF

chmod +x "$INSTALL_DIR/$CLIENT_NAME"

echo "✅ Centre AI client installed successfully!"
echo ""
echo "Usage:"
echo "  $CLIENT_NAME                    # Interactive mode"
echo "  $CLIENT_NAME --help             # Show all options"
echo "  $CLIENT_NAME --list-tools       # List available tools"
echo "  $CLIENT_NAME --health           # Check server health"
echo ""
echo "Examples:"
echo "  $CLIENT_NAME --transport stream"
echo "  $CLIENT_NAME --tool get_memory --args '{\"query\": \"test\", \"limit\": 5}'"
echo ""

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "⚠️  Note: $INSTALL_DIR is not in your PATH"
    echo "   Add this to your shell profile (.bashrc, .zshrc, etc.):"
    echo "   export PATH=\"\$PATH:$INSTALL_DIR\""
    echo ""
fi

echo "🚀 Ready! Run '$CLIENT_NAME' to start."