# Centre AI - MCP Tools Übersicht

## ✓ System Status

**Alle 38 Tools sind verfügbar und funktionsfähig!**

## Wichtig: Virtuelle Umgebung verwenden

Das System benötigt die virtuelle Umgebung (venv) mit allen installierten Abhängigkeiten.

### Aktivierung

```bash
# Option 1: Mit Aktivierungsskript
source activate_env.sh

# Option 2: Manuell
source venv/bin/activate

# Option 3: Direkt Python aus venv verwenden
./venv/bin/python3.13 app.py
```

## Verfügbare Tools (38 gesamt)

### 📝 TEXT Tools (8)
- `text_length` - Zeichen zählen
- `text_uppercase` - In Großbuchstaben konvertieren
- `text_lowercase` - In Kleinbuchstaben konvertieren
- `text_reverse` - Text umkehren
- `text_word_count` - Wörter zählen
- `text_find_replace` - Text suchen und ersetzen
- `text_extract_emails` - E-Mail-Adressen extrahieren
- `text_extract_urls` - URLs extrahieren

### 📊 DATA Tools (8)
- `json_format` - JSON formatieren und prettifizieren
- `json_validate` - JSON-Syntax validieren
- `calculate` - Mathematische Berechnungen durchführen
- `hash_text` - Hash generieren (MD5, SHA256)
- `base64_encode` - Text zu Base64 kodieren
- `base64_decode` - Base64 zu Text dekodieren
- `list_sort` - Liste sortieren
- `list_unique` - Eindeutige Elemente einer Liste

### 🌐 WEB Tools (5)
- `url_encode` - URL kodieren
- `url_decode` - URL dekodieren
- `url_parse` - URL in Komponenten zerlegen
- `html_escape` - HTML-Sonderzeichen escapen
- `html_unescape` - HTML-Sonderzeichen unescapen

### 📁 FILE Tools (5)
- `file_extension` - Dateierweiterung ermitteln
- `file_mimetype` - MIME-Type ermitteln
- `path_join` - Pfadkomponenten zusammenfügen
- `path_basename` - Basename aus Pfad extrahieren
- `path_dirname` - Verzeichnisname aus Pfad extrahieren

### 🔧 GIT Tools (12)
- `git_clone` - Repository klonen
- `git_pull` - Neueste Änderungen ziehen
- `git_status` - Repository-Status abrufen
- `git_log` - Commit-Historie anzeigen
- `git_diff` - Diff anzeigen
- `git_list_repos` - Alle geklonten Repositories auflisten
- `git_list_files` - Dateien im Repository auflisten
- `git_read_file` - Datei aus Repository lesen
- `git_write_file` - Datei im Repository schreiben/ändern
- `git_commit` - Änderungen committen
- `git_push` - Commits zu Remote pushen
- `git_delete_repo` - Repository löschen

## Testen

```bash
# Alle Tools testen
./venv/bin/python3.13 test_tools.py

# Oder nach Aktivierung der venv:
source activate_env.sh
python3 test_tools.py
```

## Server starten

### Entwicklungsmodus (lokal)

```bash
# Mit venv
source activate_env.sh
python3 app.py
```

Server läuft dann auf: http://localhost:5000

### Produktionsmodus (Docker)

```bash
# Container starten
docker compose up -d

# Status prüfen
docker compose ps

# Logs anzeigen
docker compose logs -f centre-ai

# Container stoppen
docker compose down
```

Server läuft dann auf: http://127.0.0.1:2068

## API Endpoints

### MCP Tools
- `POST /mcp/initialize` - MCP Server initialisieren
- `GET /mcp/tools/list` - Alle verfügbaren Tools auflisten
- `POST /mcp/tools/execute` - Tool ausführen

### Dashboard
- `GET /` - Dashboard
- `GET /health` - Health Check
- `GET /api/status` - Server-Status (Auth erforderlich)

## Authentifizierung

Die API erfordert eine der folgenden Authentifizierungsmethoden:

### API Key
```bash
curl -H "X-API-Key: dein-api-schluessel" http://localhost:5000/mcp/tools/list
```

### Bearer Token
```bash
curl -H "Authorization: Bearer your-token" http://localhost:5000/mcp/tools/list
```

### Basic Auth
```bash
curl -u admin:admin http://localhost:5000/mcp/tools/list
```

## Beispiel: Tool ausführen

```bash
# Text in Großbuchstaben konvertieren
curl -X POST http://localhost:5000/mcp/tools/execute \
  -H "X-API-Key: dein-api-schluessel" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "text_uppercase",
    "parameters": {
      "text": "hello world"
    }
  }'
```

## Abhängigkeiten

Die folgenden Hauptabhängigkeiten sind installiert:
- Flask 3.0.0
- Flask-CORS 4.0.0
- GitPython 3.1.40
- qdrant-client 1.12.1
- sentence-transformers 3.3.1
- psycopg 3.2.3
- PyJWT 2.8.0
- bcrypt 4.1.2

## Fehlerbehebung

### Problem: "ModuleNotFoundError: No module named 'git'"
**Lösung:** Verwende die virtuelle Umgebung (venv):
```bash
source venv/bin/activate
# oder
./venv/bin/python3.13 app.py
```

### Problem: Tools werden nicht gefunden
**Lösung:** Stelle sicher, dass die venv aktiviert ist und alle Dependencies installiert sind:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Problem: Docker-Container starten nicht
**Lösung:** Prüfe die Logs:
```bash
docker compose logs postgres
docker compose logs qdrant
docker compose logs centre-ai
```

## System-Informationen

- Python Version: 3.13
- Entwicklungsumgebung: venv
- Git Repository Path: ~/.centre-ai/git_repos (oder GIT_REPOS_PATH)
- MCP Data Path: ./mcp_data
- Logs Path: ./logs
