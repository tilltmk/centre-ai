# Centre AI - Verwendung

## 🚀 System starten

```bash
# Docker-System starten (empfohlen)
./docker-setup.sh

# Dashboard öffnen
# http://localhost:2068
```

**Credentials:**
- API Key: `dev-api-key-12345`
- Basic Auth: `admin` / `admin`

---

## 📊 Dashboard (Web UI)

### 1. Überblick
- Server Status & Statistiken
- Verfügbare Tools anzeigen
- API Tester

### 2. API Tester verwenden

```
1. API Key eingeben (bereits vorausgefüllt)
2. Tool aus Dropdown wählen (z.B. "text_uppercase")
3. Parameter als JSON eingeben:
   {"text": "hello world"}
4. "Tool ausführen" klicken
```

**Beispiel-Requests:**
```json
// Text zu Großbuchstaben
{"text": "hello"}

// JSON formatieren
{"json_string": "{\"name\":\"test\"}"}

// Hash generieren
{"text": "password123", "algorithm": "sha256"}

// Git Repository klonen
{"repo_url": "https://github.com/user/repo.git", "branch": "main"}
```

---

## 🔌 Als MCP Server verwenden

### Claude Desktop Integration

Füge in `~/Library/Application Support/Claude/claude_desktop_config.json` hinzu:

```json
{
  "mcpServers": {
    "centre-ai": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "http://localhost:2068/mcp/tools/execute",
        "-H", "X-API-Key: dev-api-key-12345",
        "-H", "Content-Type: application/json",
        "-d", "{\"tool_name\": \"TOOL\", \"parameters\": PARAMS}"
      ]
    }
  }
}
```

### Andere AI-Clients

Beliebiger HTTP-Client mit MCP-Support kann Centre AI verwenden:

```
URL: http://localhost:2068
API Key: dev-api-key-12345
```

---

## 🛠️ API direkt verwenden

### 1. Tools auflisten

```bash
curl -H "X-API-Key: dev-api-key-12345" \
  http://localhost:2068/mcp/tools/list
```

### 2. Tool ausführen

```bash
curl -X POST http://localhost:2068/mcp/tools/execute \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "text_uppercase",
    "parameters": {"text": "hello"}
  }'
```

### 3. Profil erstellen

```bash
curl -X POST http://localhost:2068/api/profile \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Max Mustermann",
    "email": "max@example.com",
    "preferences": {
      "theme": "dark",
      "language": "de"
    }
  }'
```

### 4. Memory speichern

```bash
curl -X POST http://localhost:2068/api/memories \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "memory_type": "fact",
    "content": "User bevorzugt Python",
    "importance": 8,
    "tags": ["programming"]
  }'
```

### 5. Code-Suche

```bash
curl -X POST http://localhost:2068/api/code/search \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication function",
    "language": "python",
    "limit": 5
  }'
```

---

## 📚 Verfügbare Tools (38)

### Text Tools (8)
- `text_length` - Zeichenzählung
- `text_uppercase` - Großbuchstaben
- `text_lowercase` - Kleinbuchstaben
- `text_reverse` - Text umkehren
- `text_word_count` - Wörter zählen
- `text_find_replace` - Suchen & Ersetzen
- `text_extract_emails` - E-Mails extrahieren
- `text_extract_urls` - URLs extrahieren

### Data Tools (8)
- `json_format` - JSON formatieren
- `json_validate` - JSON validieren
- `calculate` - Berechnungen
- `hash_text` - Hash generieren (MD5, SHA256)
- `base64_encode` - Base64 kodieren
- `base64_decode` - Base64 dekodieren
- `list_sort` - Liste sortieren
- `list_unique` - Duplikate entfernen

### Web Tools (5)
- `url_encode` - URL kodieren
- `url_decode` - URL dekodieren
- `url_parse` - URL parsen
- `html_escape` - HTML escapen
- `html_unescape` - HTML unescapen

### File Tools (5)
- `file_extension` - Dateierweiterung
- `file_mimetype` - MIME-Type
- `path_join` - Pfad zusammenfügen
- `path_basename` - Basename
- `path_dirname` - Directory-Name

### Git Tools (12)
- `git_clone` - Repository klonen
- `git_pull` - Updates holen
- `git_status` - Status anzeigen
- `git_log` - Commit-Historie
- `git_diff` - Änderungen anzeigen
- `git_list_repos` - Repositories auflisten
- `git_list_files` - Dateien auflisten
- `git_read_file` - Datei lesen
- `git_write_file` - Datei schreiben
- `git_commit` - Änderungen committen
- `git_push` - Zum Remote pushen
- `git_delete_repo` - Repository löschen

---

## 🎯 Use Cases

### 1. AI-Assistant mit Tools
```python
# Claude/ChatGPT kann auf 38 Tools zugreifen
# und automatisch Git-Repos klonen, Code analysieren,
# Daten transformieren, etc.
```

### 2. Code-Analyse & Suche
```bash
# 1. Repository klonen
git_clone("https://github.com/user/repo.git")

# 2. Semantisch suchen
POST /api/code/search
{"query": "authentication logic", "language": "python"}
```

### 3. Workflow-Automatisierung
```bash
# Tools in Skripten verwenden
./run-analysis.sh | text_extract_urls | json_format
```

### 4. Entwickler-Produktivität
```bash
# Dashboard als Daily-Tool
# - JSON formatieren
# - Hash generieren
# - URLs en/dekodieren
# - Git-Ops ohne CLI
```

---

## 🔧 Konfiguration

### Umgebungsvariablen (.env)

```env
# API Zugang
API_KEY=dev-api-key-12345

# Qdrant (lokal mit API Key)
QDRANT_HOST=http://localhost:6333
QDRANT_API_KEY=dein-qdrant-key

# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PASSWORD=secure-password
```

### Qdrant mit lokalem API Key

```yaml
# docker-compose.yml anpassen
qdrant:
  image: qdrant/qdrant:latest
  environment:
    - QDRANT__SERVICE__API_KEY=${QDRANT_API_KEY}
  ports:
    - "6333:6333"  # Extern verfügbar machen
```

Dann in `.env`:
```env
QDRANT_HOST=http://localhost:6333
QDRANT_API_KEY=your-local-key
```

---

## 📖 Weitere Dokumentation

- `README.md` - Übersicht & Setup
- `DOCKER_README.md` - Docker-Deployment
- `FEATURES.md` - Alle Features im Detail

---

## 🆘 Support

Bei Problemen:
1. Logs prüfen: `docker compose logs centre-ai`
2. Health Check: `curl http://localhost:2068/health`
3. API Status: `curl http://localhost:2068/api/status`
