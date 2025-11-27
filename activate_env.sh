#!/bin/bash
# Aktivierungsskript für Centre AI MCP Server
# Aktiviert die virtuelle Umgebung für die Entwicklung

echo "Aktiviere Centre AI MCP Server Umgebung..."
source venv/bin/activate
echo "✓ Virtuelle Umgebung aktiviert"
echo "✓ Python: $(which python3)"
echo "✓ Version: $(python3 --version)"
echo ""
echo "Verfügbare Kommandos:"
echo "  python3 test_tools.py          - Teste alle MCP-Tools"
echo "  python3 app.py                 - Starte Flask-Server (Dev)"
echo "  docker compose up -d           - Starte Docker-Container"
echo "  docker compose down            - Stoppe Docker-Container"
echo ""
