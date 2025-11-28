#!/usr/bin/env python3
"""
Centre AI MCP Streamable HTTP Server
Standalone server for streamable HTTP transport
"""
import asyncio
import logging
import os
import signal
import sys
from typing import Optional

import uvicorn

from .config import config
from .database import init_databases, close_databases
from .streamable_transport import stream_app

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.server.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_streamable_server")


class StreamableServer:
    """Streamable HTTP server for MCP tools"""

    def __init__(self, host: str = None, port: int = None):
        self.host = host or config.server.mcp_host
        self.port = port or int(os.getenv("STREAM_PORT", 2072))  # Different port for streaming
        self.server: Optional[uvicorn.Server] = None
        self.shutdown_event = asyncio.Event()

    async def startup(self):
        """Initialize server components"""
        logger.info("Starting MCP Streamable HTTP Server...")

        try:
            # Initialize databases
            await init_databases()
            logger.info("Database connections initialized")

            logger.info(f"Streamable server ready at http://{self.host}:{self.port}")
            logger.info(f"API documentation: http://{self.host}:{self.port}/stream/docs")
            logger.info(f"Streaming endpoint: http://{self.host}:{self.port}/stream/execute")

        except Exception as e:
            logger.error(f"Streamable startup failed: {e}")
            raise

    async def shutdown(self):
        """Cleanup server components"""
        logger.info("Shutting down MCP Streamable HTTP Server...")

        try:
            await close_databases()
            logger.info("Database connections closed")

        except Exception as e:
            logger.error(f"Streamable shutdown error: {e}")

        logger.info("MCP Streamable HTTP Server stopped")

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
        """Run the streamable server"""
        try:
            await self.startup()

            # Configure uvicorn
            uvicorn_config = uvicorn.Config(
                app=stream_app,
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
            logger.error(f"Streamable server error: {e}")
            raise
        finally:
            await self.shutdown()


async def main():
    """Main entry point"""
    try:
        server = StreamableServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Streamable server interrupted by user")
    except Exception as e:
        logger.error(f"Streamable server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the streamable server
    asyncio.run(main())