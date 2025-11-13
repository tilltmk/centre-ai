# Centre AI - Flask MCP Server

Ein professioneller Flask-basierter MCP (Model Context Protocol) Server mit Apple-Stil Dashboard für Ollama und andere AI-Modelle.

## Features

- **MCP Server**: Vollständige Model Context Protocol Implementation
- **Mehrere Authentifizierungsmethoden**:
  - API Key
  - Bearer Token
  - OAuth 2.0
  - Basic Auth
- **Tools & Memory**: Integrierte Tools und persistentes Gedächtnis
- **Apple-Stil Dashboard**: Modernes UI mit Dark Mode
- **Docker Support**: Vollständiges Docker Setup

## Schnellstart

### Mit Docker (empfohlen)

```bash
docker-compose up -d
```

Der Server läuft dann auf `http://localhost:5000`

### Manuell

```bash
# Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# Server starten
python app.py
```

## Konfiguration

Erstelle eine `.env` Datei:

```env
FLASK_ENV=development
SECRET_KEY=dein-geheimer-schluessel
API_KEY=dein-api-schluessel
OLLAMA_HOST=http://localhost:11434
REDIS_HOST=localhost
REDIS_PORT=6379
```

## API Endpunkte

### MCP Server
- `POST /mcp/initialize` - MCP Server initialisieren
- `POST /mcp/tools/execute` - Tool ausführen
- `GET /mcp/tools/list` - Verfügbare Tools auflisten
- `POST /mcp/memory/store` - Im Gedächtnis speichern
- `GET /mcp/memory/retrieve` - Aus Gedächtnis abrufen

### Dashboard
- `GET /` - Haupt-Dashboard
- `GET /api/status` - Server Status
- `GET /api/stats` - Nutzungsstatistiken

## Authentifizierung

### API Key
```bash
curl -H "X-API-Key: your-api-key" http://localhost:5000/mcp/tools/list
```

### Bearer Token
```bash
curl -H "Authorization: Bearer your-token" http://localhost:5000/mcp/tools/list
```

## Lizenz

MIT
