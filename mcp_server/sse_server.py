#!/usr/bin/env python3
"""
Centre AI MCP SSE Server
Standalone Server-Sent Events server for MCP integration
Compatible with Claude Desktop and other SSE-based clients
"""
import asyncio
import logging
import os
import signal
import sys
from typing import Optional

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import Response
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from mcp.server.sse import SseServerTransport

from .config import config
from .database import init_databases, close_databases
from .server import SecureMCPServer

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.server.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_sse_server")


class SSEServer:
    """Standalone SSE server for MCP tools"""

    def __init__(self, host: str = None, port: int = None):
        self.host = host or config.server.mcp_host
        self.port = port or int(os.getenv("SSE_PORT", 2071))  # Different port for SSE
        self.mcp_server = SecureMCPServer()
        self.server: Optional[uvicorn.Server] = None
        self.shutdown_event = asyncio.Event()
        self.app = self._create_app()

    def _create_app(self) -> Starlette:
        """Create SSE application"""

        async def handle_sse(request):
            """Handle SSE connections for MCP"""

            # Create SSE transport
            async with SseServerTransport("/messages") as (read_stream, write_stream):
                # Run MCP server with SSE transport
                await self.mcp_server.server.run(
                    read_stream,
                    write_stream,
                    self.mcp_server.server.create_initialization_options()
                )

        async def handle_health(request):
            """Health check for SSE server"""
            return Response(
                content='{"status":"healthy","transport":"sse","timestamp":"' +
                       asyncio.get_event_loop().time().__str__() + '"}',
                media_type="application/json"
            )

        async def handle_info(request):
            """SSE server information"""
            return Response(
                content='{"name":"Centre AI MCP SSE Server","version":"2.0.0","transport":"SSE","compatible_with":["Claude Desktop","MCP Clients","SSE-based tools"]}',
                media_type="application/json"
            )

        # Define routes
        routes = [
            Route("/", handle_info),
            Route("/health", handle_health),
            Route("/sse", handle_sse),
            Route("/messages", handle_sse),  # Alternative endpoint
        ]

        # CORS middleware
        middleware = [
            Middleware(
                CORSMiddleware,
                allow_origins=config.security.allowed_origins,
                allow_credentials=True,
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["*"]
            )
        ]

        return Starlette(routes=routes, middleware=middleware)

    async def startup(self):
        """Initialize server components"""
        logger.info("Starting MCP SSE Server...")

        try:
            # Initialize databases
            await init_databases()
            logger.info("Database connections initialized")

            logger.info(f"SSE server ready at http://{self.host}:{self.port}")
            logger.info(f"SSE endpoint: http://{self.host}:{self.port}/sse")
            logger.info(f"Claude Desktop compatible: ws://{self.host}:{self.port}/messages")

        except Exception as e:
            logger.error(f"SSE startup failed: {e}")
            raise

    async def shutdown(self):
        """Cleanup server components"""
        logger.info("Shutting down MCP SSE Server...")

        try:
            await close_databases()
            logger.info("Database connections closed")

        except Exception as e:
            logger.error(f"SSE shutdown error: {e}")

        logger.info("MCP SSE Server stopped")

    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            asyncio.create_task(self.graceful_shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def graceful_shutdown(self):
        """Gracefully shutdown the server"""
        self.shutdown_event.set()
        if self.server:
            self.server.should_exit = True

    async def run(self):
        """Run the SSE server"""
        try:
            await self.startup()

            # Configure uvicorn
            uvicorn_config = uvicorn.Config(
                app=self.app,
                host=self.host,
                port=self.port,
                log_level=config.server.log_level.lower(),
                access_log=True,
                server_header=False,
                date_header=False
            )

            self.server = uvicorn.Server(uvicorn_config)

            # Setup signal handlers
            self.setup_signal_handlers()

            # Start server
            await self.server.serve()

        except Exception as e:
            logger.error(f"SSE server error: {e}")
            raise
        finally:
            await self.shutdown()


async def main():
    """Main entry point"""
    try:
        server = SSEServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("SSE server interrupted by user")
    except Exception as e:
        logger.error(f"SSE server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the SSE server
    asyncio.run(main())