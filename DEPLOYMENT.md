# Claude Web Connector Deployment Guide

## Quick Setup for Claude Web Integration

### 1. OAuth Client Registration

Your OAuth client is already registered:

```json
{
  "client_id": "mcp_DnQOmdMZ9o-j7hlg43mWyA",
  "client_secret": "R0uc27yTZrIVrcrMeyMsnyJsKzgr7pTye3w5er441bU",
  "redirect_uris": [
    "https://claude.ai/oauth/callback",
    "https://claude.ai/api/mcp/auth_callback"
  ]
}
```

### 2. Public Access Setup

For Claude Web to access your server, you need **public HTTPS access**.

#### Option A: Reverse Proxy (Recommended)

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:2068;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE specific headers
        proxy_buffering off;
        proxy_cache off;
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
    }
}
```

#### Option B: Cloudflare Tunnel

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb

# Create tunnel
cloudflared tunnel create centre-ai-mcp
cloudflared tunnel route dns centre-ai-mcp your-domain.com

# Configure tunnel
cat > config.yml << EOF
tunnel: YOUR_TUNNEL_ID
credentials-file: /path/to/tunnel/credentials.json

ingress:
  - hostname: your-domain.com
    service: http://localhost:2068
  - service: http_status:404
EOF

# Run tunnel
cloudflared tunnel --config config.yml run
```

### 3. Claude Web Setup

1. **Go to Claude Settings** → **Connectors**
2. **Add Custom Connector:**
   - **Server URL:** `https://your-domain.com/sse`
   - **Authorization URL:** `https://your-domain.com/oauth/authorize`
   - **Token URL:** `https://your-domain.com/oauth/token`
   - **Client ID:** `mcp_DnQOmdMZ9o-j7hlg43mWyA`
   - **Client Secret:** `R0uc27yTZrIVrcrMeyMsnyJsKzgr7pTye3w5er441bU`

### 4. Environment Configuration

Update your `.env` for production:

```env
# Production URLs (replace with your domain)
BASE_URL=https://your-domain.com
CORS_ORIGINS=https://claude.ai,https://*.claude.ai

# Enhanced security
LOG_LEVEL=WARNING
OAUTH_REQUIRE_PKCE=true
```

### 5. Available Tools

Once connected, Claude Web will have access to these 10 tools:

- **create_memory** - Store knowledge and facts
- **get_memory** - Retrieve memories with semantic search
- **get_codebase** - Search indexed code repositories
- **capture_codebase** - Index local codebases
- **get_instructions** - Retrieve admin instructions
- **who_am_i_talking_to** - Get admin profile info
- **project_overview** - View managed projects
- **conversation_overview** - Access chat history
- **web_search** - Search web via DuckDuckGo
- **get_knowledge_graph** - Retrieve knowledge graph

### 6. Testing

Test your connector endpoints:

```bash
# Health check
curl https://your-domain.com/health

# Connector metadata
curl https://your-domain.com/connector.json

# OAuth metadata
curl https://your-domain.com/.well-known/oauth-authorization-server
```

### 7. Security Notes

- OAuth 2.1 with PKCE enabled
- CORS restricted to Claude domains
- Bearer token authentication
- Auto-approval for registered Claude clients
- All communication over HTTPS required

Your Centre AI server is now ready for Claude Web integration!