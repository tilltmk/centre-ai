"""
Centre AI - Secure MCP Server Implementation
Uses the official MCP Python SDK with SSE transport for remote access
"""
import asyncio
import json
import logging
import hashlib
import hmac
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import (
    Tool,
    TextContent,
    Resource,
    Prompt,
    PromptMessage,
    GetPromptResult,
    PromptArgument
)
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .config import config
from .database import db, vector_store, init_databases
from .tools import MCPTools, TOOL_DEFINITIONS
from .oauth import OAuth2Server, get_authorization_server_metadata, get_protected_resource_metadata
from .oauth_routes import (
    oauth_metadata,
    protected_resource_metadata,
    oauth_register,
    oauth_authorize,
    oauth_token,
    oauth_revoke,
    claude_connector_info,
    claude_well_known
)
from .oauth import ensure_claude_client_registered

# Configure logging
logging.basicConfig(level=getattr(logging, config.server.log_level))
logger = logging.getLogger("centre-ai-mcp")


def add_cors_headers(response: Response) -> Response:
    """Add CORS headers manually"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Max-Age"] = "86400"
    return response


async def handle_options_request(request: Request) -> Response:
    """Handle all OPTIONS requests"""
    response = Response(status_code=200)
    return add_cors_headers(response)


class SecureMCPServer:
    """Secure MCP Server with authentication"""

    def __init__(self):
        self.server = Server("centre-ai")
        self.tools = MCPTools()
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP protocol handlers"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools"""
            return [
                Tool(
                    name=tool["name"],
                    description=tool["description"],
                    inputSchema=tool["inputSchema"]
                )
                for tool in TOOL_DEFINITIONS
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Execute a tool by name"""
            logger.info(f"Tool call: {name} with args: {arguments}")

            tool_map = {
                "create_memory": self.tools.create_memory,
                "get_memory": self.tools.get_memory,
                "get_codebase": self.tools.get_codebase,
                "capture_codebase": self.tools.capture_codebase,
                "get_instructions": self.tools.get_instructions,
                "who_am_i_talking_to": self.tools.who_am_i_talking_to,
                "project_overview": self.tools.project_overview,
                "conversation_overview": self.tools.conversation_overview,
                "web_search": self.tools.web_search,
                "get_knowledge_graph": self.tools.get_knowledge_graph
            }

            if name not in tool_map:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown tool: {name}"})
                )]

            try:
                result = await tool_map[name](**arguments)
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, default=str)
                )]
            except Exception as e:
                logger.error(f"Tool error: {e}")
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)})
                )]

        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """List available resources"""
            return [
                Resource(
                    uri="centre://memories",
                    name="Memories",
                    description="Access to stored memories and knowledge",
                    mimeType="application/json"
                ),
                Resource(
                    uri="centre://codebases",
                    name="Codebases",
                    description="Access to indexed codebases",
                    mimeType="application/json"
                ),
                Resource(
                    uri="centre://projects",
                    name="Projects",
                    description="Access to project information",
                    mimeType="application/json"
                ),
                Resource(
                    uri="centre://instructions",
                    name="Instructions",
                    description="Access to configured instructions",
                    mimeType="application/json"
                )
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read a resource by URI"""
            resource_map = {
                "centre://memories": lambda: self.tools.get_memory(limit=50),
                "centre://codebases": lambda: self.tools.get_codebase(limit=50),
                "centre://projects": lambda: self.tools.project_overview(),
                "centre://instructions": lambda: self.tools.get_instructions()
            }

            if uri in resource_map:
                result = await resource_map[uri]()
                return json.dumps(result, indent=2, default=str)

            return json.dumps({"error": f"Unknown resource: {uri}"})

        @self.server.list_prompts()
        async def list_prompts() -> list[Prompt]:
            """List available prompts"""
            return [
                Prompt(
                    name="system_context",
                    description="Get full system context including instructions, projects, and admin info",
                    arguments=[]
                ),
                Prompt(
                    name="memory_summary",
                    description="Get a summary of stored memories",
                    arguments=[
                        PromptArgument(
                            name="memory_type",
                            description="Filter by memory type",
                            required=False
                        )
                    ]
                )
            ]

        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Optional[dict] = None) -> GetPromptResult:
            """Get a prompt by name"""
            if name == "system_context":
                instructions = await self.tools.get_instructions()
                admins = await self.tools.who_am_i_talking_to()
                projects = await self.tools.project_overview(status="active")

                context = f"""# System Context

## Instructions
{json.dumps(instructions.get('instructions', []), indent=2)}

## Active Projects
{json.dumps(projects.get('projects', []), indent=2)}

## Administrators
{json.dumps(admins.get('admins', []), indent=2)}
"""
                return GetPromptResult(
                    description="Full system context",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(type="text", text=context)
                        )
                    ]
                )

            elif name == "memory_summary":
                memory_type = arguments.get("memory_type") if arguments else None
                memories = await self.tools.get_memory(memory_type=memory_type, limit=20)

                summary = f"""# Memory Summary

Total memories found: {memories.get('count', 0)}

## Memories
{json.dumps(memories.get('memories', []), indent=2)}
"""
                return GetPromptResult(
                    description="Memory summary",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(type="text", text=summary)
                        )
                    ]
                )

            return GetPromptResult(
                description="Unknown prompt",
                messages=[]
            )


async def verify_auth_token(request: Request) -> bool:
    """
    Verify authentication token
    Supports both:
    1. Static Bearer token (existing)
    2. OAuth 2.1 access tokens (new)
    """
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

        # Try static MCP auth token first (backward compatibility)
        if hmac.compare_digest(token, config.security.mcp_auth_token):
            return True

        # Try OAuth access token
        token_data = await OAuth2Server.verify_access_token(token)
        if token_data:
            # Attach token data to request state for later use
            request.state.oauth_token = token_data
            return True

    # Also check query parameter for SSE connections (static token only)
    token = request.query_params.get("token", "")
    if hmac.compare_digest(token, config.security.mcp_auth_token):
        return True

    return False


def create_mcp_app() -> Starlette:
    """Create the MCP server Starlette application"""

    mcp_server = SecureMCPServer()
    sse_transport = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> Response:
        """Handle SSE connection for MCP"""
        if not await verify_auth_token(request):
            # Return 401 with www-authenticate header for OAuth discovery
            base_url = f"{request.url.scheme}://{request.url.netloc}"
            return JSONResponse(
                {"error": "Unauthorized"},
                status_code=401,
                headers={
                    "WWW-Authenticate": f'Bearer realm="{base_url}", resource="{base_url}/.well-known/oauth-protected-resource"'
                }
            )

        logger.info(f"SSE connection from {request.client.host} - {request.method}")

        # Handle POST requests as messages
        if request.method == "POST":
            return await sse_transport.handle_post_message(
                request.scope,
                request.receive,
                request._send
            )

        # Handle GET requests as SSE connections
        async with sse_transport.connect_sse(
            request.scope,
            request.receive,
            request._send
        ) as streams:
            await mcp_server.server.run(
                streams[0],
                streams[1],
                mcp_server.server.create_initialization_options()
            )

        return Response()

    async def handle_messages(request: Request) -> Response:
        """Handle MCP messages"""
        if not await verify_auth_token(request):
            base_url = f"{request.url.scheme}://{request.url.netloc}"
            return JSONResponse(
                {"error": "Unauthorized"},
                status_code=401,
                headers={
                    "WWW-Authenticate": f'Bearer realm="{base_url}", resource="{base_url}/.well-known/oauth-protected-resource"'
                }
            )

        return await sse_transport.handle_post_message(
            request.scope,
            request.receive,
            request._send
        )

    async def health_check(request: Request) -> JSONResponse:
        """Health check endpoint"""
        return JSONResponse({
            "status": "healthy",
            "server": "centre-ai-mcp",
            "version": "2.0.0"
        })

    async def server_info(request: Request) -> JSONResponse:
        """Server information endpoint"""
        if not await verify_auth_token(request):
            base_url = f"{request.url.scheme}://{request.url.netloc}"
            return JSONResponse(
                {"error": "Unauthorized"},
                status_code=401,
                headers={
                    "WWW-Authenticate": f'Bearer realm="{base_url}", resource="{base_url}/.well-known/oauth-protected-resource"'
                }
            )

        vector_stats = await vector_store.get_stats()

        return JSONResponse({
            "name": "Centre AI MCP Server",
            "version": "2.0.0",
            "protocol": "MCP 1.0",
            "transport": "SSE",
            "tools_count": len(TOOL_DEFINITIONS),
            "vector_stats": vector_stats
        })

    async def connector_metadata(request: Request) -> JSONResponse:
        """Claude Web Connector Metadata"""
        # Detect if request comes through HTTPS proxy (like Zoraxy)
        forwarded_proto = request.headers.get("x-forwarded-proto", "")
        # Get HTTPS detection domains from environment
        https_domains = os.getenv("HTTPS_DOMAINS", "").split(",")
        https_domains = [domain.strip() for domain in https_domains if domain.strip()]

        # Check if domain should use HTTPS
        domain_uses_https = any(domain in str(request.url.netloc) for domain in https_domains)

        is_https = (
            forwarded_proto.lower() == "https" or
            domain_uses_https or
            request.url.scheme == "https"
        )
        scheme = "https" if is_https else request.url.scheme
        base_url = f"{scheme}://{request.url.netloc}"

        return JSONResponse({
            "name": "Centre AI Knowledge Server",
            "description": "AI knowledge management with memory, codebase indexing, and web search capabilities",
            "version": "2.0.0",
            "author": "Centre AI Team",
            "homepage": base_url,
            "repository": "https://github.com/centre-ai/mcp-server",
            "license": "MIT",
            "mcp": {
                "version": "1.0",
                "transport": "sse",
                "endpoint": f"{base_url}/sse"
            },
            "oauth": {
                "authorization_url": f"{base_url}/oauth/authorize",
                "token_url": f"{base_url}/oauth/token",
                "scopes": ["read", "write"],
                "pkce_required": True
            },
            "capabilities": [
                "knowledge_management",
                "codebase_indexing",
                "memory_storage",
                "web_search",
                "project_management"
            ],
            "tools": [
                {
                    "name": tool["name"],
                    "description": tool["description"]
                }
                for tool in TOOL_DEFINITIONS
            ]
        })

    async def openapi_spec(request: Request) -> JSONResponse:
        """OpenAPI specification for OpenWebUI integration"""
        # Detect HTTPS for base URL
        forwarded_proto = request.headers.get("x-forwarded-proto", "")
        # Get HTTPS detection domains from environment
        https_domains = os.getenv("HTTPS_DOMAINS", "").split(",")
        https_domains = [domain.strip() for domain in https_domains if domain.strip()]

        # Check if domain should use HTTPS
        domain_uses_https = any(domain in str(request.url.netloc) for domain in https_domains)

        is_https = (
            forwarded_proto.lower() == "https" or
            domain_uses_https or
            request.url.scheme == "https"
        )
        scheme = "https" if is_https else request.url.scheme
        base_url = f"{scheme}://{request.url.netloc}"

        # Generate OpenAPI paths for each MCP tool
        paths = {}
        components_schemas = {}

        for tool in TOOL_DEFINITIONS:
            tool_name = tool["name"]
            schema = tool["inputSchema"]

            # Create path for each tool
            paths[f"/tools/{tool_name}"] = {
                "post": {
                    "summary": tool["description"],
                    "operationId": f"call_{tool_name}",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": schema
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Tool execution result",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "data": {"type": "object"},
                                            "error": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Unauthorized"
                        },
                        "500": {
                            "description": "Server error"
                        }
                    },
                    "security": [{"bearerAuth": []}]
                }
            }

            # Store schema for reuse
            components_schemas[f"{tool_name}Request"] = schema

        response = JSONResponse({
            "openapi": "3.0.3",
            "info": {
                "title": "Centre AI MCP Server",
                "description": "AI knowledge management with memory, codebase indexing, and web search capabilities",
                "version": "2.0.0",
                "contact": {
                    "name": "Centre AI Team",
                    "url": base_url
                },
                "license": {
                    "name": "MIT"
                }
            },
            "servers": [
                {
                    "url": base_url,
                    "description": "Centre AI MCP Server"
                }
            ],
            "paths": paths,
            "components": {
                "schemas": components_schemas,
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "description": "Bearer authentication using MCP auth token or OAuth access token"
                    }
                }
            },
            "security": [{"bearerAuth": []}]
        })

        return response

    async def startup():
        """Application startup"""
        logger.info("Initializing databases...")
        await init_databases()
        logger.info("Registering Claude OAuth client...")
        await ensure_claude_client_registered()
        logger.info("Centre AI MCP Server started")

    async def handle_tool_call(request: Request) -> JSONResponse:
        """Handle OpenWebUI tool calls via REST API"""
        if not await verify_auth_token(request):
            base_url = f"{request.url.scheme}://{request.url.netloc}"
            response = JSONResponse(
                {"error": "Unauthorized"},
                status_code=401,
                headers={
                    "WWW-Authenticate": f'Bearer realm="{base_url}", resource="{base_url}/.well-known/oauth-protected-resource"'
                }
            )
            return add_cors_headers(response)

        tool_name = request.path_params["tool_name"]

        # Initialize tools instance for each call
        tools = MCPTools()

        # Map tool names to handlers
        tool_map = {
            "create_memory": tools.create_memory,
            "get_memory": tools.get_memory,
            "get_codebase": tools.get_codebase,
            "capture_codebase": tools.capture_codebase,
            "get_instructions": tools.get_instructions,
            "who_am_i_talking_to": tools.who_am_i_talking_to,
            "project_overview": tools.project_overview,
            "conversation_overview": tools.conversation_overview,
            "web_search": tools.web_search,
            "get_knowledge_graph": tools.get_knowledge_graph
        }

        if tool_name not in tool_map:
            response = JSONResponse(
                {"error": f"Unknown tool: {tool_name}"},
                status_code=404
            )
            return add_cors_headers(response)

        try:
            body = await request.json()
            result = await tool_map[tool_name](**body)

            response = JSONResponse({
                "success": True,
                "data": result
            })
            return add_cors_headers(response)

        except Exception as e:
            logger.error(f"Tool call error for {tool_name}: {e}")
            response = JSONResponse(
                {"success": False, "error": str(e)},
                status_code=500
            )
            return add_cors_headers(response)

    async def debug_routes(request: Request) -> JSONResponse:
        """Debug: List all routes"""
        return JSONResponse({
            "message": "OpenAPI route is working",
            "openapi_route": "/openapi.json",
            "tools_route": "/tools/{tool_name}"
        })

    async def handle_options(request: Request) -> Response:
        """Handle CORS preflight OPTIONS requests"""
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "86400"
            }
        )

    async def openapi_options(request: Request) -> Response:
        """Handle CORS preflight for OpenAPI endpoint"""
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "86400"
            }
        )

    async def handle_cors_options(request: Request) -> Response:
        """Handle all CORS OPTIONS requests"""
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "86400"
            }
        )

    routes = [
        Route("/health", health_check),
        Route("/info", server_info),
        Route("/connector.json", connector_metadata),
        Route("/debug", debug_routes),
        Route("/openapi.json", openapi_spec, methods=["GET"]),
        Route("/tools/{tool_name}", handle_tool_call, methods=["POST"]),
        Route("/sse", handle_sse, methods=["GET", "POST"]),
        Route("/messages/", handle_messages, methods=["POST"]),

        # Claude Connector Endpoints
        Route("/claude", claude_connector_info),
        Route("/.well-known/mcp.json", claude_well_known),

        # OAuth 2.1 Endpoints
        Route("/.well-known/oauth-authorization-server", oauth_metadata),
        Route("/.well-known/oauth-protected-resource", protected_resource_metadata),
        Route("/oauth/register", oauth_register, methods=["POST"]),
        Route("/oauth/authorize", oauth_authorize),
        Route("/authorize", oauth_authorize),
        Route("/oauth/token", oauth_token, methods=["POST"]),
        Route("/oauth/revoke", oauth_revoke, methods=["POST"]),
    ]

    # No middleware - using manual CORS headers
    app = Starlette(
        routes=routes,
        on_startup=[startup]
    )

    return app


# Create the application instance
app = create_mcp_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "mcp_server.server:app",
        host=config.server.mcp_host,
        port=config.server.mcp_port,
        reload=config.server.debug
    )
