# Claude Desktop via SSH - Keine lokale Installation nötig!

Mit diesem Setup läuft der stdio-Server **zentral auf deinem Server** und Claude Desktop verbindet sich via SSH.
**Kein lokaler Wrapper, keine Installation auf jedem Client!**

---

## Vorteile

- ✅ **Zentral**: Server läuft nur auf deinem Server
- ✅ **Keine lokale Installation**: Funktioniert auf jedem Client mit SSH
- ✅ **Secure**: SSH-Verschlüsselung + MCP-Token
- ✅ **Multi-Client**: Mehrere Claude Desktop Instanzen können sich verbinden
- ✅ **Easy Updates**: Update nur auf dem Server, nicht auf Clients

---

## Server-Setup

### 1. stdio-Server installieren

```bash
# Als root/sudo
cp mcp_stdio_server.py /opt/centre-ai/
chmod +x /opt/centre-ai/mcp_stdio_server.py

# Testen
python3 /opt/centre-ai/mcp_stdio_server.py --token YOUR_TOKEN
```

### 2. Systemd Socket Service (Optional - für permanenten Service)

```bash
# Services installieren
sudo cp systemd/centre-ai-mcp-stdio.socket /etc/systemd/system/
sudo cp systemd/centre-ai-mcp-stdio.service /etc/systemd/system/

# Service aktivieren
sudo systemctl daemon-reload
sudo systemctl enable centre-ai-mcp-stdio.socket
sudo systemctl start centre-ai-mcp-stdio.socket

# Status checken
sudo systemctl status centre-ai-mcp-stdio.socket
```

### 3. SSH-User vorbereiten

```bash
# MCP-User erstellen (falls nicht vorhanden)
sudo useradd -r -s /bin/bash -d /opt/centre-ai -m mcp

# SSH-Key für passwordless login
sudo -u mcp ssh-keygen -t ed25519 -f /opt/centre-ai/.ssh/id_ed25519 -N ""
```

---

## Client-Setup (Claude Desktop)

### Option A: Direkt via SSH (Empfohlen)

**claude_desktop_config.json:**
```json
{
  "mcpServers": {
    "centre-ai": {
      "command": "ssh",
      "args": [
        "-i", "/home/YOU/.ssh/centre-ai-key",
        "mcp@your-server.com",
        "python3 /opt/centre-ai/mcp_stdio_server.py"
      ]
    }
  }
}
```

**SSH-Key Setup:**
```bash
# Auf deinem CLIENT
# 1. Key vom Server holen
scp your-server.com:/opt/centre-ai/.ssh/id_ed25519 ~/.ssh/centre-ai-key
chmod 600 ~/.ssh/centre-ai-key

# 2. Authorized keys auf Server
ssh-copy-id -i ~/.ssh/centre-ai-key mcp@your-server.com

# 3. Testen
ssh -i ~/.ssh/centre-ai-key mcp@your-server.com "python3 /opt/centre-ai/mcp_stdio_server.py"
```

### Option B: Via Systemd Socket (Fortgeschritten)

**claude_desktop_config.json:**
```json
{
  "mcpServers": {
    "centre-ai": {
      "command": "ssh",
      "args": [
        "mcp@your-server.com",
        "socat",
        "STDIO",
        "UNIX-CONNECT:/run/centre-ai/mcp.sock"
      ]
    }
  }
}
```

Benötigt `socat` auf dem Server:
```bash
sudo apt install socat  # Debian/Ubuntu
sudo dnf install socat  # Fedora
```

---

## Konfigurationen

### Für macOS
**Config-Pfad:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "centre-ai": {
      "command": "ssh",
      "args": [
        "-i", "/Users/YOURNAME/.ssh/centre-ai-key",
        "-o", "StrictHostKeyChecking=accept-new",
        "mcp@your-server.com",
        "python3", "/opt/centre-ai/mcp_stdio_server.py"
      ]
    }
  }
}
```

### Für Linux
**Config-Pfad:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "centre-ai": {
      "command": "ssh",
      "args": [
        "-i", "/home/YOURNAME/.ssh/centre-ai-key",
        "-o", "StrictHostKeyChecking=accept-new",
        "mcp@your-server.com",
        "python3", "/opt/centre-ai/mcp_stdio_server.py"
      ]
    }
  }
}
```

### Für Windows
**Config-Pfad:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "centre-ai": {
      "command": "ssh.exe",
      "args": [
        "-i", "C:\\Users\\YOURNAME\\.ssh\\centre-ai-key",
        "mcp@your-server.com",
        "python3", "/opt/centre-ai/mcp_stdio_server.py"
      ]
    }
  }
}
```

---

## SSH-Config optimieren

**~/.ssh/config:**
```ssh
Host centre-ai
    HostName your-server.com
    User mcp
    IdentityFile ~/.ssh/centre-ai-key
    StrictHostKeyChecking accept-new
    ServerAliveInterval 60
    ServerAliveCountMax 3
    Compression yes
```

**Dann vereinfacht sich die Claude Desktop Config:**
```json
{
  "mcpServers": {
    "centre-ai": {
      "command": "ssh",
      "args": [
        "centre-ai",
        "python3 /opt/centre-ai/mcp_stdio_server.py"
      ]
    }
  }
}
```

---

## Troubleshooting

### SSH-Verbindung testen
```bash
# Manuell testen
ssh centre-ai "echo 'test'"

# stdio-Server testen
ssh centre-ai "python3 /opt/centre-ai/mcp_stdio_server.py" < /dev/null

# Mit Debug
ssh -vvv centre-ai "python3 /opt/centre-ai/mcp_stdio_server.py"
```

### Logs ansehen

**Server-Side:**
```bash
# Systemd logs
sudo journalctl -u centre-ai-mcp-stdio.socket -f

# stdio-Server direkt
sudo -u mcp python3 /opt/centre-ai/mcp_stdio_server.py --debug
```

**Client-Side:**
- **macOS**: `~/Library/Logs/Claude/mcp*.log`
- **Linux**: `~/.config/Claude/logs/mcp*.log`

### Häufige Fehler

**"Permission denied (publickey)"**
- SSH-Key Permissions prüfen: `chmod 600 ~/.ssh/centre-ai-key`
- Authorized keys: `ssh-copy-id -i ~/.ssh/centre-ai-key mcp@server`

**"Connection refused"**
- Server läuft? `systemctl status centre-ai-mcp-stdio.socket`
- Firewall: Port 22 offen?

**"Command not found: python3"**
- Absoluter Pfad nutzen: `/usr/bin/python3`
- Virtual env: `/opt/centre-ai/venv/bin/python3`

---

## Sicherheit

### SSH Hardening
```bash
# /etc/ssh/sshd_config
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AllowUsers mcp

# Nur für MCP-User command restriction
Match User mcp
    ForceCommand /opt/centre-ai/mcp_stdio_server.py
    PermitTTY no
    X11Forwarding no
```

### Firewall
```bash
# Nur SSH von vertrauenswürdigen IPs
sudo ufw allow from YOUR_CLIENT_IP to any port 22
```

---

## Performance-Tipps

### SSH Multiplexing (Connection Sharing)
```ssh
# ~/.ssh/config
Host centre-ai
    ControlMaster auto
    ControlPath ~/.ssh/control-%r@%h:%p
    ControlPersist 10m
```

Reduziert Verbindungsaufbau-Zeit erheblich!

### Compression
```ssh
Host centre-ai
    Compression yes
    CompressionLevel 6
```

Gut für langsame Verbindungen.

---

## Multi-Server Setup

Mehrere MCP Server gleichzeitig:

```json
{
  "mcpServers": {
    "centre-ai-prod": {
      "command": "ssh",
      "args": ["centre-ai-prod", "python3 /opt/centre-ai/mcp_stdio_server.py"]
    },
    "centre-ai-dev": {
      "command": "ssh",
      "args": ["centre-ai-dev", "python3 /opt/centre-ai/mcp_stdio_server.py"]
    },
    "local-filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "~/Documents"]
    }
  }
}
```

---

## Architektur

```
┌────────────────┐
│ Claude Desktop │
│   (Client)     │
└───────┬────────┘
        │ SSH (Encrypted)
        ▼
┌─────────────────────────┐
│  Your Server            │
│  ┌──────────────────┐   │
│  │ mcp_stdio_server │   │
│  └────────┬─────────┘   │
│           │ Local        │
│           ▼              │
│  ┌──────────────────┐   │
│  │   MCP Backend    │   │
│  │  (Tools, DB)     │   │
│  └──────────────────┘   │
└─────────────────────────┘
```

**Vorteile dieser Architektur:**
- Kein Wrapper auf Client nötig
- SSH übernimmt Verschlüsselung und Auth
- Zentrale Updates und Wartung
- Funktioniert mit jedem SSH-Client (Windows/macOS/Linux)

---

## Production Deployment

### Mit Docker + SSH Jump Host

```yaml
# docker-compose.yml
services:
  centre-ai-mcp:
    image: centre-ai:latest
    ports:
      - "3001:3001"  # HTTP/SSE
    volumes:
      - ./data:/var/lib/centre-ai

  ssh-jump:
    image: linuxserver/openssh-server
    ports:
      - "2222:2222"
    environment:
      - USER_NAME=mcp
      - PUBLIC_KEY_FILE=/config/authorized_keys
    volumes:
      - ./ssh-config:/config
```

**Client Config:**
```json
{
  "mcpServers": {
    "centre-ai": {
      "command": "ssh",
      "args": [
        "-p", "2222",
        "mcp@your-domain.com",
        "docker", "exec", "-i", "centre-ai-mcp",
        "python3", "/app/mcp_stdio_server.py"
      ]
    }
  }
}
```

---

## Zusammenfassung

**3 Integrations-Methoden:**

| Method | Use Case | Installation |
|--------|----------|--------------|
| **SSH stdio** | Claude Desktop/Code | ✅ Nur auf Server |
| **HTTP/SSE + OAuth** | Claude.ai Web | ✅ Nur auf Server |
| **HTTP/SSE + Bearer** | API Clients | ✅ Nur auf Server |

**Keine lokale Installation mehr nötig!** 🎉
