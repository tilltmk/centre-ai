# Centre AI - Complete Feature List

## 🚀 Erweiterte Features v2.0.0

### 1. **Git Repository Management**

Vollständige Git-Integration zum Klonen, Modifizieren und Verwalten von Repositories:

#### Verfügbare Tools:
- `git_clone` - Repository klonen
- `git_pull` - Updates holen
- `git_status` - Repository-Status
- `git_log` - Commit-Historie
- `git_diff` - Änderungen anzeigen
- `git_list_repos` - Alle Repositories auflisten
- `git_list_files` - Dateien im Repository
- `git_read_file` - Datei lesen
- `git_write_file` - Datei schreiben/modifizieren
- `git_commit` - Änderungen committen
- `git_push` - Zum Remote pushen
- `git_delete_repo` - Repository löschen

#### Beispiel: Repository klonen und indexieren

```bash
# Repository klonen
curl -X POST http://localhost:5000/mcp/tools/execute \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "git_clone",
    "parameters": {
      "repo_url": "https://github.com/user/repo.git",
      "branch": "main"
    }
  }'

# Dateien auflisten
curl -X POST http://localhost:5000/mcp/tools/execute \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "git_list_files",
    "parameters": {
      "repo_name": "repo",
      "path": "src"
    }
  }'
```

### 2. **Code-Indexierung & Semantische Suche**

Automatische Indexierung von Code-Repositories mit Qdrant Vector Database:

#### Features:
- **Automatische Sprach-Erkennung**: 25+ Programmiersprachen
- **Semantic Code Search**: Finde Code nach Bedeutung, nicht nur Keywords
- **Chunking**: Intelligente Code-Aufteilung für bessere Suche
- **Embeddings**: Verwendet Sentence-Transformers für hochwertige Vektoren

#### Unterstützte Sprachen:
Python, JavaScript, TypeScript, Java, C/C++, C#, Go, Rust, Ruby, PHP, Swift, Kotlin, Scala, R, SQL, Bash, HTML, CSS, SCSS, JSON, YAML, XML, Markdown

#### Beispiel: Code suchen

```bash
curl -X POST http://localhost:5000/api/code/search \
  -H "X-API-Key: dev-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication function with JWT",
    "language": "python",
    "limit": 5
  }'
```

### 3. **Benutzer-Profile**

Persönliche Profile für jeden Nutzer mit Präferenzen und Metadaten:

#### API Endpoints:
- `GET /api/profile` - Profil abrufen
- `POST /api/profile` - Profil erstellen/aktualisieren
- `PUT /api/profile/preferences` - Präferenzen aktualisieren

#### Gespeicherte Informationen:
- Vollständiger Name
- E-Mail
- Bio/Beschreibung
- Benutzerdefinierte Präferenzen (JSON)
- Erweiterte Metadaten (JSON)

#### Beispiel:

```python
import requests

# Profil erstellen
response = requests.post(
    'http://localhost:5000/api/profile',
    headers={'X-API-Key': 'dev-api-key-12345'},
    json={
        'full_name': 'Max Mustermann',
        'email': 'max@example.com',
        'bio': 'Software Developer',
        'preferences': {
            'theme': 'dark',
            'language': 'de',
            'notifications': True
        },
        'metadata': {
            'timezone': 'Europe/Berlin',
            'favorite_languages': ['Python', 'JavaScript']
        }
    }
)
```

### 4. **Konversations-Management**

Vollständiges System für Konversations-Historie und Nachrichten:

#### Features:
- **Persistente Konversationen**: Alle Gespräche werden gespeichert
- **Session-basiert**: Jede Konversation hat eine eindeutige Session-ID
- **Kontextverwaltung**: Zusätzliche Kontext-Daten pro Konversation
- **Nachrichtenverfolgung**: Jede Nachricht mit Rolle, Inhalt und Metadaten

#### API Endpoints:
- `POST /api/conversations` - Neue Konversation
- `POST /api/conversations/{session_id}/messages` - Nachricht hinzufügen
- `GET /api/conversations/{session_id}/history` - Historie abrufen
- `GET /api/conversations` - Alle Konversationen des Nutzers

#### Beispiel:

```python
# Konversation starten
requests.post(
    'http://localhost:5000/api/conversations',
    headers={'X-API-Key': 'dev-api-key-12345'},
    json={
        'session_id': 'unique-session-id',
        'title': 'Code Review Discussion',
        'context': {'project': 'my-app'}
    }
)

# Nachricht hinzufügen
requests.post(
    'http://localhost:5000/api/conversations/unique-session-id/messages',
    headers={'X-API-Key': 'dev-api-key-12345'},
    json={
        'role': 'user',
        'content': 'Can you review this code?',
        'metadata': {'file': 'app.py'}
    }
)

# Historie abrufen
response = requests.get(
    'http://localhost:5000/api/conversations/unique-session-id/history',
    headers={'X-API-Key': 'dev-api-key-12345'}
)
```

### 5. **Langzeit-Gedächtnis (Memories)**

Intelligentes Gedächtnis-System für langfristige Erinnerungen:

#### Features:
- **Kategorisierung**: Memories nach Typ organisieren
- **Wichtigkeit**: 1-10 Skala für Priorität
- **Tags**: Mehrere Tags pro Memory
- **Metadaten**: Erweiterte Informationen

#### Memory-Typen:
- `fact`: Fakten über den Nutzer
- `preference`: Präferenzen
- `reminder`: Wichtige Erinnerungen
- `context`: Kontextuelle Informationen
- `custom`: Benutzerdefiniert

#### API Endpoints:
- `POST /api/memories` - Memory speichern
- `GET /api/memories` - Memories abrufen (mit Filtern)
- `DELETE /api/memories/{id}` - Memory löschen

#### Beispiel:

```python
# Wichtige Erinnerung speichern
requests.post(
    'http://localhost:5000/api/memories',
    headers={'X-API-Key': 'dev-api-key-12345'},
    json={
        'memory_type': 'preference',
        'content': 'User prefers Python over JavaScript for backend',
        'importance': 8,
        'tags': ['programming', 'preferences'],
        'metadata': {
            'source': 'conversation',
            'date': '2024-01-15'
        }
    }
)

# Memories abrufen
response = requests.get(
    'http://localhost:5000/api/memories',
    headers={'X-API-Key': 'dev-api-key-12345'},
    params={
        'memory_type': 'preference',
        'tags': 'programming',
        'limit': 10
    }
)
```

### 6. **Vector Database (Qdrant)**

Leistungsstarke Vektor-Datenbank für semantische Suche:

#### Collections:
- `code_files`: Indexierte Code-Dateien
- `memories`: Semantische Erinnerungen
- `conversations`: Konversations-Embeddings
- Custom Collections möglich

#### Features:
- **Similarity Search**: Finde ähnliche Inhalte
- **Filtering**: Kombiniere Vektor-Suche mit Filtern
- **Scalable**: Millionen von Vektoren
- **Fast**: Sub-Sekunden Antwortzeit

### 7. **PostgreSQL Database**

Relationale Datenbank für strukturierte Daten:

#### Tabellen:
- `user_profiles`: Nutzer-Profile
- `conversations`: Konversationen
- `messages`: Nachrichten
- `memories`: Langzeit-Gedächtnis
- `git_repositories`: Git-Repositories
- `code_files`: Code-Dateien

#### Features:
- **ACID**: Transaktionssicherheit
- **JSON Support**: JSONB für flexible Daten
- **Indexes**: Optimierte Abfragen
- **Auto-Timestamps**: Automatische Zeitstempel

### 8. **n8n Workflow Automation**

Integration mit n8n für Workflow-Automatisierung:

#### Zugriff:
- URL: http://localhost:5678
- Standard-Login: admin / admin

#### Möglichkeiten:
- MCP Server in Workflows integrieren
- Automatische Code-Indexierung
- Benachrichtigungen bei Git-Änderungen
- Scheduled Tasks

### 9. **Ollama Integration**

Lokale AI-Modelle mit Ollama:

#### Zugriff:
- URL: http://localhost:11434
- API: http://localhost:11434/api

#### Beispiel: Modell verwenden

```bash
# Modell herunterladen
docker-compose exec ollama ollama pull llama2

# Chat mit Modell
curl http://localhost:11434/api/chat -d '{
  "model": "llama2",
  "messages": [
    {
      "role": "user",
      "content": "Explain what MCP is"
    }
  ]
}'
```

## 📊 Service-Übersicht

### Laufende Services:

| Service | Port | URL | Beschreibung |
|---------|------|-----|-------------|
| **MCP Server** | 5000 | http://localhost:5000 | Haupt-API & Dashboard |
| **n8n** | 5678 | http://localhost:5678 | Workflow Automation |
| **Qdrant** | 6333 | http://localhost:6333 | Vector Database |
| **Postgres** | 5432 | localhost:5432 | Relationale DB |
| **Redis** | 6379 | localhost:6379 | Cache & Sessions |
| **Ollama** | 11434 | http://localhost:11434 | AI Models |

### Gesamtstatistik:

- **50+ MCP Tools** (Text, Data, Web, File, Git)
- **6 Services** in einem Docker Compose
- **2 Datenbanken** (PostgreSQL + Qdrant)
- **4 Authentifizierungs-Methoden**
- **3 Memory-Systeme** (SQLite, PostgreSQL, Qdrant)

## 🎯 Use Cases

### 1. Code Assistant
```
1. Repository klonen mit git_clone
2. Automatisch indexieren lassen
3. Code semantic suchen
4. Code lesen und modifizieren
5. Änderungen committen & pushen
```

### 2. Personal AI Assistant
```
1. Profil erstellen mit Präferenzen
2. Konversationen führen mit Context
3. Wichtige Erinnerungen speichern
4. Preferences learning über Zeit
```

### 3. Knowledge Base
```
1. Multiple Repositories indexieren
2. Cross-repo Code-Suche
3. Dokumentation durchsuchen
4. Best Practices finden
```

### 4. Workflow Automation
```
1. n8n Workflows erstellen
2. Git-Webhooks einrichten
3. Automatische Code-Reviews
4. Benachrichtigungen senden
```

## 🔐 Sicherheit

### Authentifizierung:
- API Key (empfohlen)
- JWT Bearer Token
- Basic Auth
- Query Parameter (nur für Tests)

### Datenbank:
- Encrypted connections
- User-isolation
- Row-level security möglich

### Environment Variables:
Alle sensiblen Daten in `.env` Datei

## 📚 Weitere Dokumentation

- `README.md` - Allgemeine Übersicht
- `QUICKSTART.md` - Schneller Einstieg
- `INTEGRATION.md` - Integration mit AI-Modellen
- `FEATURES.md` - Diese Datei
