# Claude Desktop / Claude Code Integration

Centre AI MCP Server kann auf **3 Arten** verwendet werden:

## 1. 🌐 HTTP/SSE mit Bearer Token (Direct)
Für direkte API-Integration und Testing.

**Claude Desktop Config:**
```json
{
  "mcpServers": {
    "centre-ai-direct": {
      "url": "http://localhost:3001/sse",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_HERE"
      }
    }
  }
}
```

⚠️ **Hinweis**: Claude Desktop unterstützt Remote-MCP nur in bestimmten Versionen. Nutze stdio-Wrapper falls es nicht funktioniert.

---

## 2. 🔐 HTTP/SSE mit OAuth 2.1 (Claude.ai Connectors)
Für Claude.ai Web-Interface mit vollständigem OAuth-Flow.

**Setup:**
1. Gehe zur Admin UI: `http://localhost:8080/oauth-clients`
2. Registriere neuen OAuth Client:
   - **Client Name**: Claude Connector
   - **Redirect URI**: `https://claude.ai/api/mcp/auth_callback`
   - **Type**: Public (PKCE)
3. Notiere die `client_id`
4. Gehe zu [claude.ai](https://claude.ai) → Settings → Connectors
5. Add Custom Connector:
   - **Server URL**: `http://YOUR_SERVER:3001/sse`
   - **Advanced Settings**: Trage `client_id` ein
6. Authorize im OAuth-Flow

**Features:**
- ✅ Dynamic Client Registration
- ✅ PKCE (OAuth 2.1)
- ✅ Token Refresh
- ✅ Secure Authorization

---

## 3. 📟 stdio-Wrapper (Claude Desktop/Code - **Empfohlen**)
Für lokale Claude Desktop und Claude Code Integration.

### Automatische Installation

```bash
./install-claude-desktop.sh
```

Das Skript:
- Erkennt dein OS (macOS/Linux)
- Findet die Claude Desktop Config
- Konfiguriert den stdio-Wrapper
- Erstellt Backup der bestehenden Config

### Manuelle Installation

**1. Config-Datei finden:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**2. Config erstellen/erweitern:**
```json
{
  "mcpServers": {
    "centre-ai": {
      "command": "python3",
      "args": [
        "/absoluter/pfad/zu/centre-ai/mcp_stdio_wrapper.py"
      ],
      "env": {
        "MCP_SERVER_URL": "http://localhost:3001",
        "MCP_AUTH_TOKEN": "dein-token-hier"
      }
    }
  }
}
```

**3. Token aus Admin UI holen:**
```bash
# Server Info aufrufen
curl http://localhost:8080/settings

# Oder in Admin UI nachsehen: Settings → MCP Authentication Token
```

**4. Claude Desktop neu starten**

---

## Verifikation

### stdio-Wrapper testen
```bash
# Direkt ausführen (sollte im Vordergrund laufen)
python3 mcp_stdio_wrapper.py

# In separatem Terminal
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python3 mcp_stdio_wrapper.py
```

### Server-Verbindung testen
```bash
# Health Check
curl http://localhost:3001/health

# Mit Auth
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:3001/info

# OAuth Metadata
curl http://localhost:3001/.well-known/oauth-authorization-server
```

### Claude Desktop Logs
- **macOS**: `~/Library/Logs/Claude/mcp*.log`
- **Linux**: `~/.config/Claude/logs/mcp*.log`

---

## Troubleshooting

### Problem: "MCP server not found"
**Lösung:**
1. Überprüfe Config-Datei-Pfad
2. Stelle sicher dass `python3` im PATH ist
3. Teste Wrapper manuell: `python3 mcp_stdio_wrapper.py`

### Problem: "Connection refused"
**Lösung:**
1. Stelle sicher dass MCP Server läuft: `curl http://localhost:3001/health`
2. Überprüfe SERVER_URL in env
3. Firewall-Einstellungen prüfen

### Problem: "Authentication failed"
**Lösung:**
1. Überprüfe AUTH_TOKEN in env
2. Token aus Admin UI kopieren
3. Keine Leerzeichen/Zeilenumbrüche im Token

### Problem: "Tools not showing"
**Lösung:**
1. Logs checken (siehe oben)
2. Server-Response testen: `curl -H "Authorization: Bearer TOKEN" http://localhost:3001/info`
3. Wrapper-Logs in stderr ansehen

---

## Multi-Server Setup

Du kannst mehrere MCP Server kombinieren:

```json
{
  "mcpServers": {
    "centre-ai": {
      "command": "python3",
      "args": ["/path/to/centre-ai/mcp_stdio_wrapper.py"],
      "env": {
        "MCP_SERVER_URL": "http://localhost:3001",
        "MCP_AUTH_TOKEN": "token1"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/username/Documents"]
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "your-key"
      }
    }
  }
}
```

---

## Architektur

```
┌─────────────────┐
│ Claude Desktop  │
│   or Claude     │
│      Code       │
└────────┬────────┘
         │ stdio (JSON-RPC)
         ▼
┌─────────────────────┐
│ mcp_stdio_wrapper.py│ (Local Proxy)
└────────┬────────────┘
         │ HTTP/SSE + Bearer Token
         ▼
┌──────────────────────┐
│  MCP Server (Port    │
│  3001) mit OAuth &   │
│  Bearer Auth         │
└──────────────────────┘
         │
         ▼
┌──────────────────────┐
│ PostgreSQL + Qdrant  │
│ (Knowledge Base)     │
└──────────────────────┘
```

**Vorteile:**
- ✅ Claude Desktop/Code funktioniert out-of-the-box (stdio)
- ✅ Remote Server bleibt HTTP/SSE (flexibel)
- ✅ Beide Auth-Systeme parallel nutzbar
- ✅ Keine Server-Änderungen nötig

---

## Erweiterte Konfiguration

### Custom Server URL (Production)
```json
{
  "env": {
    "MCP_SERVER_URL": "https://your-domain.com",
    "MCP_AUTH_TOKEN": "production-token"
  }
}
```

### Debug Mode
```json
{
  "env": {
    "MCP_SERVER_URL": "http://localhost:3001",
    "MCP_AUTH_TOKEN": "token",
    "MCP_DEBUG": "true"
  }
}
```

### Separate Log File
```bash
# Redirect stderr to log file
python3 mcp_stdio_wrapper.py 2>> /tmp/mcp-wrapper.log
```

---

## Support

Bei Problemen:
1. Check [GitHub Issues](https://github.com/tilltmk/centre-ai/issues)
2. Server Logs: `journalctl -u centre-ai-mcp -f`
3. Wrapper Logs: stderr output
4. Admin UI: `http://localhost:8080`
