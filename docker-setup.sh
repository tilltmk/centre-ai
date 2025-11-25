#!/bin/bash
# Centre AI Docker Setup Script
# Bereitet das geschlossene Ökosystem vor

set -e

echo "🚀 Centre AI - Docker Setup"
echo "=============================="
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker läuft nicht. Bitte Docker starten."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ docker-compose nicht gefunden. Bitte installieren."
    exit 1
fi

# Create necessary directories
echo "📁 Erstelle Verzeichnisse..."
mkdir -p mcp_data logs git_repos

# Check if .env exists, if not copy from .env.example
if [ ! -f .env ]; then
    echo "📝 Erstelle .env aus .env.example..."
    cp .env.example .env
    echo "⚠️  Bitte .env anpassen und dann erneut ausführen!"
    exit 0
fi

# Stop and remove existing containers
echo "🧹 Räume alte Container auf..."
docker compose down -v 2>/dev/null || true

# Build and start services
echo "🏗️  Baue und starte Services..."
docker compose up -d --build

# Wait for services to be healthy
echo "⏳ Warte auf Service-Start..."
sleep 10

# Check health
echo "🏥 Prüfe Service-Status..."
docker compose ps

echo ""
echo "✅ Centre AI ist bereit!"
echo ""
echo "📊 Dashboard: http://localhost:2068"
echo "🔑 API Key: dev-api-key-12345"
echo "👤 Basic Auth: admin / admin"
echo ""
echo "Befehle:"
echo "  docker compose logs -f centre-ai    # Logs anzeigen"
echo "  docker compose ps                    # Status prüfen"
echo "  docker compose down                  # Stoppen"
echo ""
