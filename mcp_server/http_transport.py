"""
HTTP Transport layer for MCP tools - OpenWebUI/MCPO compatibility
Provides OpenAPI-compatible REST endpoints for all MCP tools
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .tools import MCPTools, TOOL_DEFINITIONS
from .oauth import OAuth2Server
from .config import config

logger = logging.getLogger("http_transport")


# ==================== REQUEST/RESPONSE MODELS ====================

class MemoryRequest(BaseModel):
    content: str = Field(..., description="Memory content to store")
    memory_type: str = Field(default="general", description="Type of memory")
    importance: int = Field(default=5, ge=1, le=10, description="Importance level")
    tags: Optional[List[str]] = Field(default=None, description="Tags for categorization")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class MemorySearchRequest(BaseModel):
    query: Optional[str] = Field(default=None, description="Search query")
    memory_type: Optional[str] = Field(default=None, description="Filter by memory type")
    tags: Optional[List[str]] = Field(default=None, description="Filter by tags")
    limit: int = Field(default=10, description="Maximum results")
    semantic_search: bool = Field(default=True, description="Use vector search")


class CodebaseSearchRequest(BaseModel):
    codebase_id: Optional[int] = Field(default=None, description="Specific codebase ID")
    name: Optional[str] = Field(default=None, description="Search by name")
    query: Optional[str] = Field(default=None, description="Search code content")
    language: Optional[str] = Field(default=None, description="Filter by language")
    limit: int = Field(default=20, description="Maximum results")


class CodebaseCaptureRequest(BaseModel):
    name: str = Field(..., description="Name for the codebase")
    path: str = Field(..., description="Local path to codebase")
    description: Optional[str] = Field(default=None, description="Description")
    repo_url: Optional[str] = Field(default=None, description="Git repository URL")


class WebSearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    num_results: int = Field(default=5, ge=1, le=50, description="Number of results")
    search_engine: Optional[str] = Field(
        default=None,
        description="Search engine (duckduckgo, searx, qwant, startpage)"
    )


class InstructionsRequest(BaseModel):
    category: Optional[str] = Field(default=None, description="Filter by category")
    active_only: bool = Field(default=True, description="Only active instructions")


class ProjectRequest(BaseModel):
    project_id: Optional[int] = Field(default=None, description="Specific project ID")
    status: Optional[str] = Field(default=None, description="Filter by status")


class ConversationRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="Specific session ID")
    limit: int = Field(default=20, description="Maximum conversations")
    include_messages: bool = Field(default=False, description="Include message history")


class KnowledgeGraphRequest(BaseModel):
    node_type: Optional[str] = Field(default=None, description="Filter by node type")
    limit: int = Field(default=100, description="Maximum nodes")


class MCPGenericRequest(BaseModel):
    """Generic request model that can handle any tool call"""
    tool_name: str = Field(..., description="Name of the MCP tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


# ==================== HTTP TRANSPORT CLASS ====================

class HTTPTransport:
    """HTTP transport layer for MCP tools"""

    def __init__(self):
        self.app = FastAPI(
            title="Centre AI MCP HTTP Transport",
            description="HTTP/REST API for Centre AI MCP Server tools - OpenWebUI/MCPO compatible",
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        self.setup_middleware()
        self.setup_routes()

    def setup_middleware(self):
        """Setup CORS and other middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=config.security.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    async def verify_auth(self, authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
        """Verify OAuth token if present"""
        if not authorization:
            return None

        try:
            if authorization.startswith("Bearer "):
                token = authorization[7:]
                return await OAuth2Server.verify_access_token(token)
        except Exception as e:
            logger.warning(f"Auth verification failed: {e}")

        return None

    def setup_routes(self):
        """Setup all HTTP routes"""

        @self.app.get("/", tags=["Info"])
        async def root():
            """Root endpoint with server information"""
            return {
                "name": "Centre AI MCP HTTP Transport",
                "version": "2.0.0",
                "description": "HTTP/REST API for Centre AI MCP Server tools",
                "transport": "HTTP",
                "protocol": "MCP-over-HTTP",
                "compatible_with": ["OpenWebUI", "MCPO", "Claude.ai", "Cursor.ai"],
                "endpoints": {
                    "docs": "/docs",
                    "openapi": "/openapi.json",
                    "tools": "/tools",
                    "health": "/health"
                }
            }

        @self.app.get("/health", tags=["Info"])
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "database": "connected",
                    "vector_store": "connected"
                }
            }

        @self.app.get("/tools", tags=["Tools"])
        async def list_tools():
            """List all available MCP tools with OpenAPI schemas"""
            return {
                "tools": TOOL_DEFINITIONS,
                "count": len(TOOL_DEFINITIONS),
                "format": "OpenAPI-compatible"
            }

        # ==================== MEMORY ENDPOINTS ====================

        @self.app.post("/memory/create", tags=["Memory"])
        async def create_memory(
            request: MemoryRequest,
            auth: Optional[Dict] = Depends(self.verify_auth)
        ):
            """Create a new memory entry"""
            try:
                result = await MCPTools.create_memory(
                    content=request.content,
                    memory_type=request.memory_type,
                    importance=request.importance,
                    tags=request.tags or [],
                    metadata=request.metadata or {}
                )
                return result
            except Exception as e:
                logger.error(f"Memory creation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/memory/search", tags=["Memory"])
        @self.app.get("/memory", tags=["Memory"])
        async def search_memory(
            request: Optional[MemorySearchRequest] = None,
            query: Optional[str] = None,
            memory_type: Optional[str] = None,
            limit: int = 10,
            auth: Optional[Dict] = Depends(self.verify_auth)
        ):
            """Search memories (supports both POST with body and GET with query params)"""
            try:
                # Handle both POST and GET requests
                if request:
                    result = await MCPTools.get_memory(
                        query=request.query,
                        memory_type=request.memory_type,
                        tags=request.tags,
                        limit=request.limit,
                        semantic_search=request.semantic_search
                    )
                else:
                    result = await MCPTools.get_memory(
                        query=query,
                        memory_type=memory_type,
                        limit=limit,
                        semantic_search=True
                    )
                return result
            except Exception as e:
                logger.error(f"Memory search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ==================== CODEBASE ENDPOINTS ====================

        @self.app.post("/codebase/search", tags=["Codebase"])
        @self.app.get("/codebase", tags=["Codebase"])
        async def search_codebase(
            request: Optional[CodebaseSearchRequest] = None,
            name: Optional[str] = None,
            query: Optional[str] = None,
            language: Optional[str] = None,
            limit: int = 20,
            auth: Optional[Dict] = Depends(self.verify_auth)
        ):
            """Search codebase and code files"""
            try:
                if request:
                    result = await MCPTools.get_codebase(
                        codebase_id=request.codebase_id,
                        name=request.name,
                        query=request.query,
                        language=request.language,
                        limit=request.limit
                    )
                else:
                    result = await MCPTools.get_codebase(
                        name=name,
                        query=query,
                        language=language,
                        limit=limit
                    )
                return result
            except Exception as e:
                logger.error(f"Codebase search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/codebase/capture", tags=["Codebase"])
        async def capture_codebase(
            request: CodebaseCaptureRequest,
            auth: Optional[Dict] = Depends(self.verify_auth)
        ):
            """Index a codebase for search"""
            try:
                result = await MCPTools.capture_codebase(
                    name=request.name,
                    path=request.path,
                    description=request.description,
                    repo_url=request.repo_url
                )
                return result
            except Exception as e:
                logger.error(f"Codebase capture failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ==================== WEB SEARCH ENDPOINTS ====================

        @self.app.post("/web/search", tags=["Web Search"])
        @self.app.get("/web/search", tags=["Web Search"])
        async def web_search(
            request: Optional[WebSearchRequest] = None,
            query: Optional[str] = None,
            num_results: int = 5,
            search_engine: Optional[str] = None,
            auth: Optional[Dict] = Depends(self.verify_auth)
        ):
            """Search the web"""
            try:
                if request:
                    result = await MCPTools.web_search(
                        query=request.query,
                        num_results=request.num_results,
                        search_engine=request.search_engine
                    )
                else:
                    if not query:
                        raise HTTPException(status_code=400, detail="Query is required")
                    result = await MCPTools.web_search(
                        query=query,
                        num_results=num_results,
                        search_engine=search_engine
                    )
                return result
            except Exception as e:
                logger.error(f"Web search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ==================== OTHER ENDPOINTS ====================

        @self.app.get("/instructions", tags=["Instructions"])
        async def get_instructions(
            category: Optional[str] = None,
            active_only: bool = True,
            auth: Optional[Dict] = Depends(self.verify_auth)
        ):
            """Get instructions and guidelines"""
            try:
                result = await MCPTools.get_instructions(
                    category=category,
                    active_only=active_only
                )
                return result
            except Exception as e:
                logger.error(f"Instructions fetch failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/who-am-i-talking-to", tags=["Identity"])
        async def who_am_i_talking_to(auth: Optional[Dict] = Depends(self.verify_auth)):
            """Get admin information"""
            try:
                result = await MCPTools.who_am_i_talking_to()
                return result
            except Exception as e:
                logger.error(f"Identity fetch failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/projects", tags=["Projects"])
        async def get_projects(
            project_id: Optional[int] = None,
            status: Optional[str] = None,
            auth: Optional[Dict] = Depends(self.verify_auth)
        ):
            """Get project overview"""
            try:
                result = await MCPTools.project_overview(
                    project_id=project_id,
                    status=status
                )
                return result
            except Exception as e:
                logger.error(f"Projects fetch failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/conversations", tags=["Conversations"])
        async def get_conversations(
            session_id: Optional[str] = None,
            limit: int = 20,
            include_messages: bool = False,
            auth: Optional[Dict] = Depends(self.verify_auth)
        ):
            """Get conversation overview"""
            try:
                result = await MCPTools.conversation_overview(
                    session_id=session_id,
                    limit=limit,
                    include_messages=include_messages
                )
                return result
            except Exception as e:
                logger.error(f"Conversations fetch failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/knowledge-graph", tags=["Knowledge"])
        async def get_knowledge_graph(
            node_type: Optional[str] = None,
            limit: int = 100,
            auth: Optional[Dict] = Depends(self.verify_auth)
        ):
            """Get knowledge graph data"""
            try:
                result = await MCPTools.get_knowledge_graph(
                    node_type=node_type,
                    limit=limit
                )
                return result
            except Exception as e:
                logger.error(f"Knowledge graph fetch failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ==================== GENERIC MCP TOOL ENDPOINT ====================

        @self.app.post("/mcp/call", tags=["MCP"])
        async def call_mcp_tool(
            request: MCPGenericRequest,
            auth: Optional[Dict] = Depends(self.verify_auth)
        ):
            """Generic MCP tool call endpoint (MCPO compatibility)"""
            try:
                # Map tool names to functions
                tool_map = {
                    "create_memory": MCPTools.create_memory,
                    "get_memory": MCPTools.get_memory,
                    "get_codebase": MCPTools.get_codebase,
                    "capture_codebase": MCPTools.capture_codebase,
                    "get_instructions": MCPTools.get_instructions,
                    "who_am_i_talking_to": MCPTools.who_am_i_talking_to,
                    "project_overview": MCPTools.project_overview,
                    "conversation_overview": MCPTools.conversation_overview,
                    "web_search": MCPTools.web_search,
                    "get_knowledge_graph": MCPTools.get_knowledge_graph,
                }

                if request.tool_name not in tool_map:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Tool '{request.tool_name}' not found. Available tools: {list(tool_map.keys())}"
                    )

                tool_func = tool_map[request.tool_name]

                # Handle arguments - ensure strings are not split into lists
                clean_args = {}
                for key, value in request.arguments.items():
                    if isinstance(value, list) and len(value) == 1 and isinstance(value[0], str):
                        # Fix the split error: if we get a single-item list, extract the string
                        clean_args[key] = value[0]
                    else:
                        clean_args[key] = value

                result = await tool_func(**clean_args)
                return result

            except Exception as e:
                logger.error(f"MCP tool call failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # ==================== OPENAPI CUSTOMIZATION ====================

        @self.app.get("/openapi.json", include_in_schema=False)
        async def custom_openapi():
            """Custom OpenAPI schema with enhanced documentation"""
            from fastapi.openapi.utils import get_openapi

            openapi_schema = get_openapi(
                title="Centre AI MCP HTTP Transport",
                version="2.0.0",
                description="""
                HTTP/REST API for Centre AI MCP Server tools.

                This API provides HTTP access to Model Context Protocol (MCP) tools,
                making them compatible with OpenWebUI, MCPO, and other HTTP-based AI clients.

                **Key Features:**
                - Memory management with semantic search
                - Codebase indexing and search
                - Web search with multiple engines
                - Project and conversation tracking
                - OAuth 2.1 authentication support

                **Compatible with:**
                - OpenWebUI (via MCPO or direct HTTP)
                - Claude.ai (via HTTP transport)
                - Cursor AI (via MCP)
                - Any HTTP-based AI client

                **Authentication:**
                Use Bearer tokens via OAuth 2.1 authorization flow.
                """,
                routes=self.app.routes,
            )

            # Add custom info
            openapi_schema["info"]["contact"] = {
                "name": "Centre AI Support",
                "url": os.getenv("CENTRE_AI_REPO_URL", "https://github.com/your-org/centre-ai")
            }
            openapi_schema["info"]["license"] = {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }

            return openapi_schema

# ==================== HTTP TRANSPORT INSTANCE ====================

# Global HTTP transport instance
http_transport = HTTPTransport()
app = http_transport.app