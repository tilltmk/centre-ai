# Centre AI Transport Layer Documentation

Centre AI supports **multiple transport methods** for maximum compatibility with different AI platforms and clients.

## 🚀 Available Transport Methods

### **1. HTTP REST API (Port 2070)**
**Compatible with**: OpenWebUI, MCPO, Generic HTTP clients
**Best for**: Standard integrations, web applications, debugging

```bash
# Start HTTP transport
docker-compose up mcp-http -d

# Test endpoints
curl http://localhost:2070/health
curl http://localhost:2070/tools
curl -X POST http://localhost:2070/mcp/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "who_am_i_talking_to", "arguments": {}}'
```

**Features:**
- ✅ OpenAPI/Swagger documentation (`/docs`)
- ✅ MCPO-compatible generic API (`/mcp/call`)
- ✅ Tool-specific REST endpoints
- ✅ OAuth 2.1 authentication support
- ✅ CORS enabled for web clients
- ✅ Fixes `'list' object has no attribute 'split'` errors

### **2. Server-Sent Events (Port 2071)**
**Compatible with**: Claude Desktop, SSE-based clients
**Best for**: Real-time applications, Claude Desktop integration

```bash
# Start SSE transport
docker-compose up mcp-sse -d

# SSE endpoint
curl http://localhost:2071/sse
```

**Features:**
- ✅ Claude Desktop compatible
- ✅ Real-time event streaming
- ✅ WebSocket-like functionality over HTTP
- ✅ Automatic reconnection support

### **3. Streamable HTTP (Port 2072)**
**Compatible with**: Modern web apps, real-time dashboards
**Best for**: Progress tracking, large operations, live updates

```bash
# Start streaming transport
docker-compose up mcp-stream -d

# Streaming execution
curl -X POST http://localhost:2072/stream/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "capture_codebase", "arguments": {"name": "test", "path": "/app"}, "stream": true}'
```

**Features:**
- ✅ Real-time progress tracking
- ✅ Chunked response streaming
- ✅ Event-based progress updates
- ✅ Perfect for long-running operations

### **4. Standard MCP/STDIO (Port 2068)**
**Compatible with**: Cursor AI, Claude Code, native MCP clients
**Best for**: Desktop applications, development tools

```bash
# Start MCP server
docker-compose up mcp-server -d

# MCP protocol endpoint
curl http://localhost:2068/health
```

**Features:**
- ✅ Official MCP protocol implementation
- ✅ STDIO transport support
- ✅ Native tool definitions
- ✅ Optimized for AI development tools

## 🖥️ Standalone Client

Download and use the Centre AI client independently:

### **Quick Install**
```bash
# Download and install
curl -L ${CENTRE_AI_REPO_URL:-https://raw.githubusercontent.com/your-org/centre-ai/main}/client/install.sh | bash

# Or manual download
wget ${CENTRE_AI_REPO_URL:-https://raw.githubusercontent.com/your-org/centre-ai/main}/client/centre_ai_client.py
pip install httpx websockets
```

### **Usage Examples**

```bash
# Interactive mode
centre-ai-client

# List available tools
centre-ai-client --list-tools

# Check server health
centre-ai-client --health --transport http

# Execute specific tool
centre-ai-client --tool get_memory --args '{"query": "test", "limit": 5}'

# Use streaming transport
centre-ai-client --transport stream --tool capture_codebase --stream

# Connect to different hosts
centre-ai-client --host 192.168.1.100 --transport http
```

### **Client Features**
- ✅ **Multi-transport support** (HTTP, SSE, Streaming)
- ✅ **Interactive mode** with guided tool execution
- ✅ **Command-line interface** for automation
- ✅ **Progress tracking** with streaming transport
- ✅ **OAuth authentication** support
- ✅ **Zero-dependency downloads** (only requires Python 3.8+)

## 🐋 Docker Services Overview

| Service | Port | Transport | Compatible With | Use Case |
|---------|------|-----------|----------------|----------|
| `mcp-server` | 2068 | MCP/STDIO | Cursor AI, Claude Code | Development tools |
| `admin-ui` | 2069 | Web UI | Browsers | Administration |
| `mcp-http` | 2070 | HTTP REST | OpenWebUI, MCPO | Web integration |
| `mcp-sse` | 2071 | SSE | Claude Desktop | Real-time apps |
| `mcp-stream` | 2072 | Streaming | Dashboards | Progress tracking |

## 🔧 Configuration

All services support environment variables:

```bash
# Port configuration
export MCP_PORT=2068        # Standard MCP
export ADMIN_PORT=2069      # Admin UI
export HTTP_PORT=2070       # HTTP API
export SSE_PORT=2071        # SSE Transport
export STREAM_PORT=2072     # Streaming API

# Database settings
export POSTGRES_PASSWORD=secure_password
export SECRET_KEY=your_secret_key
export MCP_AUTH_TOKEN=auth_token

# Start all services
docker-compose up -d
```

## 🔗 Integration Guides

### **OpenWebUI Integration**
```yaml
# Option 1: Direct HTTP
base_url: "http://localhost:2070"
openapi_url: "http://localhost:2070/openapi.json"

# Option 2: Via MCPO
mcp_servers:
  centre_ai:
    command: "curl"
    args: ["-X", "POST", "http://localhost:2070/mcp/call"]
```

### **Claude.ai Integration**
```json
{
  "mcpServers": {
    "centre-ai": {
      "transport": "http",
      "url": "http://localhost:2070",
      "auth": {
        "type": "oauth2",
        "tokenUrl": "http://localhost:2070/oauth/token"
      }
    }
  }
}
```

### **Cursor AI Integration**
```json
{
  "mcp": {
    "servers": {
      "centre-ai": {
        "command": "python",
        "args": ["/path/to/centre_ai_client.py", "--transport", "stdio"]
      }
    }
  }
}
```

## 🛟 Troubleshooting

### **Common Issues**

1. **`'list' object has no attribute 'split'`** (OpenWebUI/MCPO)
   - ✅ **Fixed** in HTTP transport with argument sanitization
   - Use `/mcp/call` endpoint or direct HTTP APIs

2. **Connection refused**
   - Check service is running: `docker-compose ps`
   - Verify port not in use: `netstat -ln | grep :2070`
   - Check logs: `docker-compose logs mcp-http`

3. **Authentication errors**
   - Get OAuth token: `curl http://localhost:2070/oauth/register`
   - Include in requests: `Authorization: Bearer <token>`

4. **Streaming not working**
   - Use correct transport: `--transport stream`
   - Check streaming support: `curl http://localhost:2072/stream`
   - Verify client supports Server-Sent Events

### **Health Checks**
```bash
# Check all services
docker-compose ps

# Individual health checks
curl http://localhost:2068/health  # MCP
curl http://localhost:2070/health  # HTTP
curl http://localhost:2071/health  # SSE
curl http://localhost:2072/stream/health  # Streaming
```

## 📚 API Documentation

- **HTTP API**: http://localhost:2070/docs
- **Streaming API**: http://localhost:2072/stream/docs
- **OpenAPI Schema**: http://localhost:2070/openapi.json
- **Tool Definitions**: http://localhost:2070/tools

## 🚀 Performance

| Transport | Latency | Throughput | Use Case |
|-----------|---------|------------|----------|
| HTTP | Low | High | Bulk operations |
| SSE | Medium | Medium | Real-time updates |
| Streaming | Medium | High | Large responses |
| MCP/STDIO | Lowest | Highest | Development tools |

## 📈 Monitoring

All transports expose metrics:

```bash
# Service status
curl http://localhost:2070/health

# Tool usage
curl http://localhost:2070/tools

# Server information
curl http://localhost:2070/
```

---

**Questions?** Check logs with `docker-compose logs <service-name>` or create an issue in the repository.