# Centre AI - MCP Server Quick Start

## ✓ System Status mit Python 3.14

**Alle 38 Tools sind verfügbar und funktionsfähig!**

- Python Version: **3.14.0**
- Keine venv benötigt
- Alle Dependencies installiert

## 🚀 Schnellstart

### Tools testen
```bash
python3.14 test_tools.py
```

### Server starten (Entwicklung)
```bash
python3.14 app.py
```

Server läuft auf: http://localhost:5000

### Server starten (Produktion - Docker)
```bash
docker compose up -d
```

Server läuft auf: http://127.0.0.1:2068

## 📊 Verfügbare Tools (38)

| Kategorie | Anzahl | Beispiele |
|-----------|--------|-----------|
| TEXT | 8 | text_uppercase, text_word_count, text_extract_emails |
| DATA | 8 | json_format, calculate, hash_text, base64_encode |
| WEB | 5 | url_encode, html_escape, url_parse |
| FILE | 5 | file_extension, path_join, file_mimetype |
| GIT | 12 | git_clone, git_commit, git_status, git_push |

## 🔧 API Beispiele

### Tool ausführen

```bash
# Mit curl
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

### Tools auflisten

```bash
curl -H "X-API-Key: dein-api-schluessel" \
  http://localhost:5000/mcp/tools/list
```

## 📦 Python 3.14 Dependencies

Alle wichtigen Pakete sind installiert:
- Flask 3.0.0
- GitPython 3.1.40
- psycopg 3.2.13
- qdrant-client 1.12.1
- sentence-transformers 3.3.1
- bcrypt 4.1.2
- PyJWT 2.8.0
- Flask-CORS 4.0.0
- gunicorn 21.2.0

## 📖 Weitere Dokumentation

Siehe **TOOLS_INFO.md** für:
- Detaillierte Tool-Beschreibungen
- API-Authentifizierung
- Docker-Konfiguration
- Fehlerbehebung

## 💡 Tipp

Alle Befehle verwenden direkt `python3.14` - keine venv nötig!
