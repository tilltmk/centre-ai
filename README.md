# Centre AI - Flask MCP Server

Ein professioneller Flask-basierter MCP (Model Context Protocol) Server mit Apple-Stil Dashboard für Ollama und andere AI-Modelle.

## Features

### Core Features
- **MCP Server**: Vollständige Model Context Protocol Implementation
- **38 Tools**: Text, Data, Web, File & Git Operations
- **Multi-Auth**: API Key, Bearer Token, OAuth 2.0, Basic Auth
- **Apple-Stil Dashboard**: Modernes UI mit Dark Mode
- **Docker Support**: Vollständiges Docker Setup

### Advanced Features
- **Git Repository Management**: Clone, modify, commit & push repositories
- **Code Indexing**: Semantische Code-Suche mit Qdrant Vector DB
- **User Profiles**: Personalisierte Profile mit Präferenzen
- **Conversation Management**: Session-basierte Konversations-Historie
- **Long-term Memory**: Intelligentes Gedächtnis-System mit Tags
- **PostgreSQL & Qdrant**: Duale Datenbankarchitektur

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

## Verfügbare Tools (38)

### 📝 Text Tools (8)
`text_length`, `text_uppercase`, `text_lowercase`, `text_reverse`, `text_word_count`, `text_find_replace`, `text_extract_emails`, `text_extract_urls`

### 📊 Data Tools (8)
`json_format`, `json_validate`, `calculate`, `hash_text`, `base64_encode`, `base64_decode`, `list_sort`, `list_unique`

### 🌐 Web Tools (5)
`url_encode`, `url_decode`, `url_parse`, `html_escape`, `html_unescape`

### 📁 File Tools (5)
`file_extension`, `file_mimetype`, `path_join`, `path_basename`, `path_dirname`

### 🔧 Git Tools (12)
`git_clone`, `git_pull`, `git_status`, `git_log`, `git_diff`, `git_list_repos`, `git_list_files`, `git_read_file`, `git_write_file`, `git_commit`, `git_push`, `git_delete_repo`

## API Endpunkte

### MCP Server
- `POST /mcp/initialize` - MCP Server initialisieren
- `POST /mcp/tools/execute` - Tool ausführen
- `GET /mcp/tools/list` - Verfügbare Tools auflisten

### Profile & Memory
- `GET/POST /api/profile` - Profil abrufen/erstellen
- `POST /api/memories` - Memory speichern
- `GET /api/memories` - Memories abrufen

### Conversations
- `POST /api/conversations` - Neue Konversation
- `POST /api/conversations/{session_id}/messages` - Nachricht hinzufügen
- `GET /api/conversations/{session_id}/history` - Historie abrufen

### Code Search
- `POST /api/code/search` - Semantische Code-Suche

### Dashboard
- `GET /` - Haupt-Dashboard
- `GET /api/status` - Server Status
- `GET /api/stats` - Nutzungsstatistiken
- `GET /health` - Health Check

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
