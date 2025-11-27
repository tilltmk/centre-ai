# Centre AI - MCP Server Quickstart

## 🚀 Schnellstart

### Option 1: Mit Docker (Empfohlen)

```bash
# Setup-Skript ausführen (macht alles automatisch)
./setup.sh

# Oder manuell:
docker-compose up -d
```

Der Server läuft dann auf: http://localhost:5000

### Option 2: Lokale Entwicklung

```bash
# Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# .env Datei erstellen
cp .env.example .env

# Server starten
python app.py
```

## 📋 Features

- ✅ **MCP Server**: Vollständige Model Context Protocol Implementation
- ✅ **Multi-Auth**: API Key, Bearer Token, Basic Auth
- ✅ **Tools**: 30+ integrierte Tools (Text, Data, Web, File)
- ✅ **Memory**: Persistentes Gedächtnis mit SQLite
- ✅ **Dashboard**: Apple-Style UI mit Dark Mode
- ✅ **Docker**: Production-ready Setup

## 🔐 Authentifizierung

### 1. API Key (empfohlen)

```bash
curl -H "X-API-Key: dev-api-key-12345" \
  http://localhost:5000/mcp/tools/list
```

### 2. Bearer Token (JWT)

```bash
curl -H "Authorization: Bearer your-token" \
  http://localhost:5000/mcp/tools/list
```

### 3. Basic Auth

```bash
curl -u admin:admin \
  http://localhost:5000/mcp/tools/list
```

## 🛠️ Tools Beispiele

### Text verarbeiten

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{"tool_name": "text_uppercase", "parameters": {"text": "hello"}}' \
  http://localhost:5000/mcp/tools/execute
```

### JSON formatieren

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{"tool_name": "json_format", "parameters": {"json_string": "{\"a\":1}"}}' \
  http://localhost:5000/mcp/tools/execute
```

### Hash berechnen

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{"tool_name": "hash_text", "parameters": {"text": "hello", "algorithm": "sha256"}}' \
  http://localhost:5000/mcp/tools/execute
```

## 💾 Memory (Gedächtnis)

### Speichern

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{"key": "my_key", "value": "my_value", "tags": ["important"]}' \
  http://localhost:5000/mcp/memory/store
```

### Abrufen

```bash
curl -H "X-API-Key: dev-api-key-12345" \
  "http://localhost:5000/mcp/memory/retrieve?key=my_key"
```

### Nach Tags suchen

```bash
curl -H "X-API-Key: dev-api-key-12345" \
  "http://localhost:5000/mcp/memory/retrieve?tags=important"
```

## 🔧 Verwaltung

### Mit Make

```bash
make help      # Hilfe anzeigen
make build     # Docker Images bauen
make up        # Services starten
make down      # Services stoppen
make logs      # Logs anzeigen
make restart   # Services neustarten
make clean     # Alles aufräumen
```

### Mit Docker Compose

```bash
docker-compose up -d           # Starten
docker-compose down            # Stoppen
docker-compose logs -f         # Logs folgen
docker-compose ps              # Status anzeigen
docker-compose restart         # Neustarten
```

## 🧪 Testen

### API Tests ausführen

```bash
./test_api.sh
```

### Manueller Test

```bash
# Health Check
curl http://localhost:5000/health

# Status prüfen
curl -H "X-API-Key: dev-api-key-12345" \
  http://localhost:5000/api/status
```

## 🎨 Dashboard

Öffne http://localhost:5000 im Browser:

- **Dark Mode**: Klicke auf 🌙 oben rechts
- **API Tester**: Teste Tools direkt im Browser
- **Live Stats**: Echtzeit-Statistiken
- **Tools Browser**: Alle verfügbaren Tools durchsuchen

## 🐛 Troubleshooting

### Port bereits belegt

```bash
# Ändere den Port in docker-compose.yml
ports:
  - "5001:5000"  # Verwende Port 5001 statt 5000
```

### Logs anzeigen

```bash
docker-compose logs mcp-server
```

### Services neustarten

```bash
docker-compose restart
```

### Alles zurücksetzen

```bash
make clean
./setup.sh
```

## 📚 Verfügbare Tools

### Text Tools (8 Tools)
- `text_length` - Zeichenanzahl
- `text_uppercase` - Großbuchstaben
- `text_lowercase` - Kleinbuchstaben
- `text_reverse` - Text umkehren
- `text_word_count` - Wörter zählen
- `text_find_replace` - Suchen & Ersetzen
- `text_extract_emails` - E-Mails extrahieren
- `text_extract_urls` - URLs extrahieren

### Data Tools (8 Tools)
- `json_format` - JSON formatieren
- `json_validate` - JSON validieren
- `calculate` - Berechnungen
- `hash_text` - Hash generieren
- `base64_encode` - Base64 kodieren
- `base64_decode` - Base64 dekodieren
- `list_sort` - Liste sortieren
- `list_unique` - Duplikate entfernen

### Web Tools (5 Tools)
- `url_encode` - URL kodieren
- `url_decode` - URL dekodieren
- `url_parse` - URL parsen
- `html_escape` - HTML escapen
- `html_unescape` - HTML unescapen

### File Tools (5 Tools)
- `file_extension` - Dateiendung
- `file_mimetype` - MIME-Type
- `path_join` - Pfade verbinden
- `path_basename` - Basisname
- `path_dirname` - Verzeichnisname

## 🔗 Integration mit Ollama

Der Server ist bereits für Ollama konfiguriert:

```bash
# Ollama ist im docker-compose.yml enthalten
# Zugriff auf: http://localhost:11434

# Modell herunterladen
docker-compose exec ollama ollama pull llama2

# Modell verwenden
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Why is the sky blue?"
}'
```

## 🌐 API Endpoints

- `GET /` - Dashboard
- `GET /health` - Health Check
- `GET /api/status` - Server Status
- `GET /api/stats` - Statistiken
- `POST /mcp/initialize` - MCP initialisieren
- `GET /mcp/tools/list` - Tools auflisten
- `POST /mcp/tools/execute` - Tool ausführen
- `POST /mcp/memory/store` - Memory speichern
- `GET /mcp/memory/retrieve` - Memory abrufen
- `DELETE /mcp/memory/delete` - Memory löschen

## 💡 Tipps

1. **Sicherheit**: Ändere API Keys und Passwörter in der `.env` Datei
2. **Performance**: Passe die Anzahl der Gunicorn Worker in `Dockerfile` an
3. **Memory**: Größere Datenmengen? Verwende Redis statt SQLite
4. **Monitoring**: Logs sind in `./logs/` verfügbar
5. **Backup**: Sichere das `./mcp_data/` Verzeichnis

## 📖 Weitere Dokumentation

Siehe `README.md` für detaillierte Informationen.
