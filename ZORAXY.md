# Zoraxy Reverse Proxy Configuration

This guide explains how to configure Zoraxy reverse proxy to expose your Centre AI MCP Server securely over the internet.

## Overview

Centre AI exposes two services on localhost:
- **MCP Server** (Port 2068): SSE endpoint for AI clients
- **Admin UI** (Port 2069): Web administration interface

## Prerequisites

- Zoraxy installed and running
- A domain name pointing to your server
- SSL certificates (Let's Encrypt recommended)

## Configuration Steps

### 1. Access Zoraxy Dashboard

Navigate to your Zoraxy admin panel (default: `http://your-server:8000`)

### 2. Add Proxy Rules

#### Admin UI (Web Interface)

Create a new proxy rule for the Admin UI:

```
Domain: admin.yourdomain.com
Target: http://127.0.0.1:2069
```

Settings:
- **Enable HTTPS**: Yes
- **Force HTTPS**: Yes
- **Websocket Support**: No
- **Basic Auth**: Optional (adds extra security layer)

#### MCP Server (SSE Endpoint)

Create a new proxy rule for the MCP server:

```
Domain: mcp.yourdomain.com
Target: http://127.0.0.1:2068
```

Settings:
- **Enable HTTPS**: Yes
- **Force HTTPS**: Yes
- **Websocket Support**: Yes (required for SSE)
- **Basic Auth**: No (uses Bearer token)

**Important Headers for SSE:**
Add these custom headers in Zoraxy:

```
X-Accel-Buffering: no
Cache-Control: no-cache
Connection: keep-alive
```

### 3. SSL Configuration

For each domain, configure SSL:

1. Go to **SSL/TLS** settings in Zoraxy
2. Enable **Let's Encrypt** automatic certificates
3. Add your domains:
   - `admin.yourdomain.com`
   - `mcp.yourdomain.com`
4. Request certificates

### 4. Security Headers

Add these security headers in Zoraxy's global settings or per-rule:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

## Example Zoraxy Configuration (JSON)

If configuring via Zoraxy's config file:

```json
{
  "proxy_rules": [
    {
      "domain": "admin.yourdomain.com",
      "target": "http://127.0.0.1:2069",
      "https": true,
      "force_https": true,
      "websocket": false,
      "headers": {
        "X-Forwarded-Proto": "https"
      }
    },
    {
      "domain": "mcp.yourdomain.com",
      "target": "http://127.0.0.1:2068",
      "https": true,
      "force_https": true,
      "websocket": true,
      "headers": {
        "X-Forwarded-Proto": "https",
        "X-Accel-Buffering": "no",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive"
      }
    }
  ]
}
```

## Firewall Configuration

Ensure your firewall allows:
- **Port 443**: HTTPS traffic
- **Port 80**: HTTP (for Let's Encrypt validation, redirects to 443)

Block direct access to internal ports:
```bash
# Allow only localhost access to Centre AI ports
sudo ufw deny 2068
sudo ufw deny 2069
```

## Testing the Setup

### Test Admin UI

```bash
curl -I https://admin.yourdomain.com/health
```

Expected: `HTTP/2 200`

### Test MCP SSE Endpoint

```bash
curl -I https://mcp.yourdomain.com/health
```

Expected: `HTTP/2 200`

### Test SSE Connection

```bash
curl -N -H "Authorization: Bearer YOUR_MCP_TOKEN" \
  https://mcp.yourdomain.com/sse
```

## MCP Client Configuration (Remote)

After setting up Zoraxy, configure your MCP clients:

```json
{
  "mcpServers": {
    "centre-ai": {
      "url": "https://mcp.yourdomain.com/sse",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_AUTH_TOKEN"
      }
    }
  }
}
```

## Troubleshooting

### SSE Connection Drops

If SSE connections drop unexpectedly:

1. Increase Zoraxy timeout settings:
   - **Proxy Timeout**: 300s
   - **Read Timeout**: 300s
   - **Write Timeout**: 300s

2. Ensure these headers are set:
   ```
   X-Accel-Buffering: no
   ```

### 502 Bad Gateway

1. Check if Centre AI containers are running:
   ```bash
   docker compose ps
   ```

2. Check container logs:
   ```bash
   docker compose logs mcp-server
   docker compose logs admin-ui
   ```

### Certificate Issues

1. Verify DNS is properly configured
2. Check Let's Encrypt rate limits
3. Try manual certificate generation:
   ```bash
   certbot certonly --webroot -w /var/www/html -d mcp.yourdomain.com
   ```

## Security Recommendations

1. **Use Strong Passwords**: Change default admin password
2. **Rotate Tokens**: Periodically rotate MCP_AUTH_TOKEN
3. **IP Whitelist**: Consider restricting MCP access to known IPs
4. **Monitor Logs**: Set up log monitoring for suspicious activity
5. **Keep Updated**: Regularly update Zoraxy and Centre AI

## Alternative: Nginx Configuration

If using Nginx instead of Zoraxy:

```nginx
# Admin UI
server {
    listen 443 ssl http2;
    server_name admin.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/admin.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:2069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# MCP Server (SSE)
server {
    listen 443 ssl http2;
    server_name mcp.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/mcp.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mcp.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:2068;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE specific settings
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
        proxy_set_header Connection '';
        chunked_transfer_encoding off;
    }
}
```

## Support

For issues related to:
- **Centre AI**: Check container logs and GitHub issues
- **Zoraxy**: Visit [Zoraxy Documentation](https://zoraxy.arozos.com/)
