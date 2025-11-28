"""
Streamable HTTP Transport for Centre AI MCP Server
Implements streaming HTTP responses for real-time tool execution
"""
import asyncio
import json
import logging
import os
from typing import AsyncIterator, Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Header, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .tools import MCPTools, TOOL_DEFINITIONS
from .oauth import OAuth2Server
from .config import config

logger = logging.getLogger("streamable_transport")


# ==================== STREAMING MODELS ====================

class StreamableRequest(BaseModel):
    """Request model for streamable tool execution"""
    tool_name: str
    arguments: Dict[str, Any]
    stream: bool = True
    chunk_size: int = 1024


class StreamChunk(BaseModel):
    """Individual chunk in a stream"""
    type: str  # "progress", "data", "error", "complete"
    timestamp: str
    data: Any = None
    progress: Optional[float] = None
    message: Optional[str] = None


# ==================== STREAMABLE TRANSPORT CLASS ====================

class StreamableTransport:
    """Streamable HTTP transport layer for MCP tools"""

    def __init__(self):
        self.app = FastAPI(
            title="Centre AI Streamable HTTP Transport",
            description="Streamable HTTP API for Centre AI MCP Server tools with real-time execution",
            version="2.0.0",
            docs_url="/stream/docs",
            redoc_url="/stream/redoc"
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

    async def stream_tool_execution(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        chunk_size: int = 1024
    ) -> AsyncIterator[str]:
        """Stream tool execution with progress updates"""

        # Send start notification
        yield self._format_chunk(StreamChunk(
            type="progress",
            timestamp=datetime.utcnow().isoformat(),
            progress=0.0,
            message=f"Starting {tool_name} execution"
        ))

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

            if tool_name not in tool_map:
                yield self._format_chunk(StreamChunk(
                    type="error",
                    timestamp=datetime.utcnow().isoformat(),
                    data={"error": f"Tool '{tool_name}' not found"}
                ))
                return

            # Progress update
            yield self._format_chunk(StreamChunk(
                type="progress",
                timestamp=datetime.utcnow().isoformat(),
                progress=0.3,
                message="Executing tool"
            ))

            # Handle special streaming cases
            if tool_name == "capture_codebase":
                async for chunk in self._stream_codebase_capture(tool_map[tool_name], arguments):
                    yield chunk
            elif tool_name == "web_search":
                async for chunk in self._stream_web_search(tool_map[tool_name], arguments):
                    yield chunk
            else:
                # Standard execution
                result = await tool_map[tool_name](**arguments)

                # Progress update
                yield self._format_chunk(StreamChunk(
                    type="progress",
                    timestamp=datetime.utcnow().isoformat(),
                    progress=0.9,
                    message="Processing results"
                ))

                # Send result in chunks if large
                result_json = json.dumps(result)
                if len(result_json) > chunk_size:
                    async for chunk in self._chunk_large_response(result, chunk_size):
                        yield chunk
                else:
                    yield self._format_chunk(StreamChunk(
                        type="data",
                        timestamp=datetime.utcnow().isoformat(),
                        data=result
                    ))

            # Send completion
            yield self._format_chunk(StreamChunk(
                type="complete",
                timestamp=datetime.utcnow().isoformat(),
                progress=1.0,
                message=f"{tool_name} execution completed"
            ))

        except Exception as e:
            logger.error(f"Streaming execution failed: {e}")
            yield self._format_chunk(StreamChunk(
                type="error",
                timestamp=datetime.utcnow().isoformat(),
                data={"error": str(e)}
            ))

    async def _stream_codebase_capture(self, tool_func, arguments) -> AsyncIterator[str]:
        """Special streaming for codebase capture with progress"""
        yield self._format_chunk(StreamChunk(
            type="progress",
            timestamp=datetime.utcnow().isoformat(),
            progress=0.1,
            message="Initializing codebase capture"
        ))

        # Execute with custom progress tracking
        result = await tool_func(**arguments)

        # Simulate progress updates (in real implementation, modify capture_codebase to yield progress)
        progress_steps = [0.2, 0.4, 0.6, 0.8]
        messages = [
            "Scanning files",
            "Generating embeddings",
            "Storing in vector database",
            "Finalizing index"
        ]

        for progress, message in zip(progress_steps, messages):
            yield self._format_chunk(StreamChunk(
                type="progress",
                timestamp=datetime.utcnow().isoformat(),
                progress=progress,
                message=message
            ))
            await asyncio.sleep(0.1)  # Simulate work

        yield self._format_chunk(StreamChunk(
            type="data",
            timestamp=datetime.utcnow().isoformat(),
            data=result
        ))

    async def _stream_web_search(self, tool_func, arguments) -> AsyncIterator[str]:
        """Special streaming for web search"""
        yield self._format_chunk(StreamChunk(
            type="progress",
            timestamp=datetime.utcnow().isoformat(),
            progress=0.2,
            message=f"Searching with {arguments.get('search_engine', 'default')} engine"
        ))

        result = await tool_func(**arguments)

        yield self._format_chunk(StreamChunk(
            type="progress",
            timestamp=datetime.utcnow().isoformat(),
            progress=0.8,
            message=f"Found {result.get('count', 0)} results"
        ))

        yield self._format_chunk(StreamChunk(
            type="data",
            timestamp=datetime.utcnow().isoformat(),
            data=result
        ))

    async def _chunk_large_response(self, data: Any, chunk_size: int) -> AsyncIterator[str]:
        """Break large responses into chunks"""
        data_str = json.dumps(data)
        total_size = len(data_str)

        for i in range(0, total_size, chunk_size):
            chunk_data = data_str[i:i + chunk_size]
            is_final = (i + chunk_size) >= total_size

            yield self._format_chunk(StreamChunk(
                type="data" if is_final else "partial",
                timestamp=datetime.utcnow().isoformat(),
                data={"chunk": chunk_data, "final": is_final, "offset": i}
            ))

    def _format_chunk(self, chunk: StreamChunk) -> str:
        """Format chunk for streaming"""
        return f"data: {chunk.model_dump_json()}\n\n"

    def setup_routes(self):
        """Setup all streaming routes"""

        @self.app.get("/stream", tags=["Stream Info"])
        async def stream_info():
            """Stream transport information"""
            return {
                "name": "Centre AI Streamable HTTP Transport",
                "version": "2.0.0",
                "transport": "Streamable HTTP",
                "features": ["real-time", "progress-tracking", "chunked-responses"],
                "endpoints": {
                    "stream": "/stream/execute",
                    "tools": "/stream/tools",
                    "docs": "/stream/docs"
                }
            }

        @self.app.get("/stream/tools", tags=["Stream Tools"])
        async def list_stream_tools():
            """List tools available for streaming"""
            return {
                "tools": TOOL_DEFINITIONS,
                "count": len(TOOL_DEFINITIONS),
                "streaming_supported": True
            }

        @self.app.post("/stream/execute", tags=["Stream Execution"])
        async def stream_execute(
            request: StreamableRequest,
            auth: Optional[Dict] = Depends(self.verify_auth)
        ):
            """Execute tool with streaming response"""

            if not request.stream:
                # Non-streaming execution - fall back to regular HTTP
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
                    raise HTTPException(status_code=404, detail=f"Tool '{request.tool_name}' not found")

                result = await tool_map[request.tool_name](**request.arguments)
                return result

            # Streaming execution
            return StreamingResponse(
                self.stream_tool_execution(
                    request.tool_name,
                    request.arguments,
                    request.chunk_size
                ),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # Disable nginx buffering
                }
            )

        @self.app.get("/stream/health", tags=["Stream Health"])
        async def stream_health():
            """Streaming health check"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "transport": "streamable-http"
            }

# ==================== STREAMABLE TRANSPORT INSTANCE ====================

# Global streamable transport instance
streamable_transport = StreamableTransport()
stream_app = streamable_transport.app