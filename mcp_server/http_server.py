#!/usr/bin/env python3
"""
Centre AI MCP HTTP Server
Standalone HTTP server for OpenWebUI/MCPO compatibility
Runs parallel to the main MCP server
"""
import asyncio
import logging
import os
import signal
import sys
from typing import Optional

import uvicorn
from uvicorn.config import LOGGING_CONFIG

from .config import config
from .database import init_databases, close_databases
from .http_transport import app

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.server.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_http_server")


class HTTPServer:
    """HTTP server for MCP tools"""

    def __init__(self, host: str = None, port: int = None):
        self.host = host or config.server.mcp_host
        self.port = port or int(os.getenv("HTTP_PORT", 2070))  # Different from main MCP port
        self.server: Optional[uvicorn.Server] = None
        self.shutdown_event = asyncio.Event()

    async def startup(self):
        """Initialize server components"""
        logger.info("Starting MCP HTTP Server...")

        try:
            # Initialize databases
            await init_databases()
            logger.info("Database connections initialized")

            logger.info(f"HTTP server ready at http://{self.host}:{self.port}")
            logger.info(f"API documentation: http://{self.host}:{self.port}/docs")
            logger.info(f"OpenAPI schema: http://{self.host}:{self.port}/openapi.json")

        except Exception as e:
            logger.error(f"Startup failed: {e}")
            raise

    async def shutdown(self):
        """Cleanup server components"""
        logger.info("Shutting down MCP HTTP Server...")

        try:
            await close_databases()
            logger.info("Database connections closed")

        except Exception as e:
            logger.error(f"Shutdown error: {e}")

        logger.info("MCP HTTP Server stopped")

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
        """Run the HTTP server"""
        try:
            await self.startup()

            # Configure uvicorn
            uvicorn_config = uvicorn.Config(
                app=app,
                host=self.host,
                port=self.port,
                log_level=config.server.log_level.lower(),
                access_log=True,
                server_header=False,
                date_header=False,
                lifespan="on"
            )

            # Custom logging config for cleaner output
            LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s - %(name)s - %(levelprefix)s %(message)s"
            LOGGING_CONFIG["formatters"]["access"]["fmt"] = '%(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s'

            self.server = uvicorn.Server(uvicorn_config)

            # Setup signal handlers
            self.setup_signal_handlers()

            # Start server
            await self.server.serve()

        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
        finally:
            await self.shutdown()


async def main():
    """Main entry point"""
    try:
        server = HTTPServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the HTTP server
    asyncio.run(main())