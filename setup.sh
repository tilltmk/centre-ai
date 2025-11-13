#!/bin/bash
# Centre AI - MCP Server Setup Script

set -e

echo "======================================"
echo "Centre AI - MCP Server Setup"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker ist nicht installiert. Bitte installiere Docker zuerst."
    exit 1
fi

echo "✅ Docker gefunden"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose ist nicht installiert. Bitte installiere Docker Compose zuerst."
    exit 1
fi

echo "✅ Docker Compose gefunden"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Erstelle .env Datei..."
    cp .env.example .env

    # Generate random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i.bak "s/change-this-to-a-random-secret-key/$SECRET_KEY/" .env
    rm .env.bak 2>/dev/null || true

    echo "✅ .env Datei erstellt"
else
    echo "✅ .env Datei existiert bereits"
fi

# Create data directories
echo "📁 Erstelle Datenverzeichnisse..."
mkdir -p mcp_data logs
echo "✅ Verzeichnisse erstellt"

# Build Docker images
echo "🔨 Baue Docker Images..."
docker-compose build

# Start services
echo "🚀 Starte Services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Warte auf Services..."
sleep 5

# Check health
echo "🏥 Prüfe Service-Status..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Services laufen"
    echo ""
    echo "======================================"
    echo "Setup erfolgreich abgeschlossen!"
    echo "======================================"
    echo ""
    echo "Dashboard: http://localhost:5000"
    echo "API: http://localhost:5000/api/status"
    echo ""
    echo "Standard API Key: dev-api-key-12345"
    echo "Standard Login: admin / admin"
    echo ""
    echo "Verwende 'docker-compose logs -f' um Logs zu sehen"
    echo "Verwende 'docker-compose down' um Services zu stoppen"
else
    echo "❌ Services konnten nicht gestartet werden"
    echo "Verwende 'docker-compose logs' um Details zu sehen"
    exit 1
fi
