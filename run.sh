#!/bin/bash
# Centre AI MCP Server Startskript für Python 3.14

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      Centre AI - MCP Server starten (Python 3.14)         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python 3.14 is available
if ! command -v python3.14 &> /dev/null; then
    echo "✗ Python 3.14 ist nicht installiert!"
    exit 1
fi

echo "✓ Python 3.14 gefunden: $(python3.14 --version)"
echo ""
echo "Starte Flask MCP Server..."
echo "Server läuft auf: http://localhost:5000"
echo ""
echo "Drücke Ctrl+C zum Beenden"
echo ""

# Start the server
python3.14 app.py
