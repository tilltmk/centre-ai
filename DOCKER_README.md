# Centre AI - Docker Deployment

Geschlossenes Ökosystem mit allen Services in Docker Compose.

## Quick Start

```bash
# 1. Setup ausführen (erstellt Verzeichnisse, baut Container)
./docker-setup.sh

# 2. Services sind verfügbar unter:
# - Dashboard: http://localhost:2068
# - API Key: dev-api-key-12345
# - Basic Auth: admin / admin
```

## Services

| Service | Intern | Extern | Beschreibung |
|---------|--------|--------|--------------|
| centre-ai | 5000 | 2068 | Flask MCP Server + Dashboard |
| postgres | 5432 | - | PostgreSQL Datenbank |
| qdrant | 6333 | - | Vector Database |

## Verwaltung

```bash
# Logs anzeigen
docker compose logs -f centre-ai

# Status prüfen
docker compose ps

# Neu starten
docker compose restart centre-ai

# Stoppen
docker compose down

# Stoppen und Daten löschen
docker compose down -v
```

## Konfiguration

Alle Einstellungen in `.env` (wird aus `.env.example` erstellt):

```env
# Wichtigste Einstellungen
API_KEY=dev-api-key-12345           # API-Authentifizierung
SECRET_KEY=change-this-in-prod      # Flask Secret
POSTGRES_PASSWORD=centre_ai_password # DB Password
QDRANT_API_KEY=                      # Optional: Qdrant API Key
```

## Volumes

Persistente Daten:
- `./mcp_data` - SQLite Memory Store
- `./logs` - Application Logs
- `./git_repos` - Geklonte Git Repositories
- `postgres-data` - PostgreSQL Daten
- `qdrant-data` - Vector Database

## Troubleshooting

### Tools werden nicht geladen

```bash
# Logs prüfen
docker compose logs centre-ai | grep -i error

# Container neu starten
docker compose restart centre-ai
```

### Qdrant Connection Error

```bash
# Qdrant Logs prüfen
docker compose logs qdrant

# Qdrant neu starten
docker compose restart qdrant
```

### PostgreSQL Connection Error

```bash
# DB Status prüfen
docker compose exec postgres pg_isready -U centre_ai

# DB neu initialisieren (ACHTUNG: Löscht Daten!)
docker compose down -v
./docker-setup.sh
```

## Entwicklung

Für lokale Entwicklung ohne Docker:

```bash
# Virtuelle Umgebung
python3 -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Server starten (benötigt lokale Postgres + Qdrant)
python app.py
```

## Produktion

Für Production Deployment:

1. `.env` anpassen:
   - `SECRET_KEY` ändern
   - `API_KEY` ändern
   - `POSTGRES_PASSWORD` ändern
   - `QDRANT_API_KEY` setzen (optional)

2. Port-Binding anpassen in `docker-compose.yml`:
   ```yaml
   ports:
     - "80:5000"  # Oder mit Reverse Proxy
   ```

3. Services starten:
   ```bash
   docker compose up -d --build
   ```
