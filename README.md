# Centre AI - MCP Knowledge Server

A secure Model Context Protocol (MCP) server with an elegant admin web interface for AI knowledge management.

## Features

### MCP Server
- **True MCP Protocol**: Native MCP implementation with SSE transport
- **Secure Authentication**: Bearer token authentication for all MCP clients
- **10 Knowledge Tools**: Comprehensive toolset for AI assistants

### Admin Web UI
- **Apple-Style Design**: Elegant black & white interface with serif typography
- **Knowledge Graph**: Interactive D3.js visualization
- **Full Management**: Memories, codebases, projects, instructions

### Infrastructure
- **Docker Compose**: Complete containerized setup
- **Isolated Network**: Only necessary ports exposed
- **Vector Search**: Qdrant for semantic search
- **PostgreSQL**: Structured data storage

## Quick Start

### Setup Wizard

```bash
chmod +x setup.sh
./setup.sh
```

The interactive setup will guide you through:
1. Admin credentials
2. Security token generation
3. Database configuration
4. Port assignment

### Manual Start

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env

# Start services
docker compose up -d
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL ACCESS                          │
│           (via Zoraxy/Nginx Reverse Proxy)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    ┌─────────────────┐         ┌─────────────────┐         │
│    │   Admin UI      │         │   MCP Server    │         │
│    │   Port 2069     │         │   Port 2068     │         │
│    │   (localhost)   │         │   (localhost)   │         │
│    └────────┬────────┘         └────────┬────────┘         │
│             │                           │                   │
├─────────────┴───────────────────────────┴───────────────────┤
│                    INTERNAL NETWORK                         │
│                   (centre-internal)                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │    Qdrant    │  │    Redis     │      │
│  │   (5432)     │  │   (6333)     │  │   (6379)     │      │
│  │   internal   │  │   internal   │  │   internal   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `create_memory` | Store knowledge, facts, reminders |
| `get_memory` | Retrieve memories with semantic search |
| `get_codebase` | Search indexed code repositories |
| `capture_codebase` | Index local codebases |
| `get_instructions` | Retrieve admin-configured instructions |
| `who_am_i_talking_to` | Get admin profile information |
| `project_overview` | View managed projects |
| `conversation_overview` | Access conversation history |
| `web_search` | Search the web via DuckDuckGo |
| `get_knowledge_graph` | Retrieve knowledge graph data |

## MCP Client Configuration

Add this to your MCP client (Claude Desktop, Cline, etc.):

```json
{
  "mcpServers": {
    "centre-ai": {
      "url": "http://localhost:2068/sse",
      "transport": "sse",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_AUTH_TOKEN"
      }
    }
  }
}
```

Find your token in:
- `.env` file (`MCP_AUTH_TOKEN`)
- Admin UI Settings page

## Ports

| Service | Port | Access |
|---------|------|--------|
| MCP Server | 2068 | localhost only |
| Admin UI | 2069 | localhost only |
| PostgreSQL | 5432 | internal only |
| Qdrant | 6333 | internal only |
| Redis | 6379 | internal only |

## Reverse Proxy Setup

For external access, use a reverse proxy. See [ZORAXY.md](ZORAXY.md) for detailed configuration.

## Security

- **Authentication**: All MCP requests require Bearer token
- **Token-based**: 64-character hex tokens
- **Isolated Network**: Database services not exposed
- **Non-root Docker**: Containers run as non-root user
- **Session Management**: Secure session cookies for Admin UI

## Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Restart
docker compose restart

# Check status
docker compose ps
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ADMIN_USERNAME` | Admin login username | `admin` |
| `ADMIN_PASSWORD` | Admin login password | - |
| `SECRET_KEY` | Session encryption key | - |
| `MCP_AUTH_TOKEN` | MCP authentication token | - |
| `POSTGRES_DB` | Database name | `centre_ai` |
| `POSTGRES_USER` | Database user | `centre_ai` |
| `POSTGRES_PASSWORD` | Database password | - |
| `MCP_PORT` | MCP server port | `2068` |
| `ADMIN_PORT` | Admin UI port | `2069` |
| `LOG_LEVEL` | Logging level | `INFO` |

## File Structure

```
centre-ai/
├── mcp_server/           # MCP Server code
│   ├── __init__.py
│   ├── config.py         # Configuration management
│   ├── database.py       # Database connections
│   ├── server.py         # MCP SSE server
│   └── tools.py          # MCP tools implementation
├── admin_ui/             # Admin Web UI
│   ├── __init__.py
│   ├── app.py            # FastAPI application
│   └── templates/        # Jinja2 templates
├── docker-compose.yml    # Docker services
├── Dockerfile.mcp        # MCP server container
├── Dockerfile.admin      # Admin UI container
├── init-db.sql           # Database schema
├── setup.sh              # Setup wizard
├── requirements.txt      # Python dependencies
├── ZORAXY.md            # Reverse proxy guide
└── README.md            # This file
```

## License

MIT

## Contributing

Contributions welcome! Please read the contributing guidelines first.
