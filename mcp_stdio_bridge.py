#!/usr/bin/env python3
"""
MCP stdio Bridge for Claude Code/Desktop

This bridge allows Claude Code and Claude Desktop to connect to the remote
HTTP/SSE MCP server via stdio (standard input/output).

Usage:
    python mcp_stdio_bridge.py --server-url http://localhost:3001 --token YOUR_TOKEN

Or in claude_desktop_config.json:
    {
      "mcpServers": {
        "centre-ai": {
          "command": "python3",
          "args": [
            "/path/to/mcp_stdio_bridge.py",
            "--server-url", "http://localhost:3001",
            "--token", "YOUR_TOKEN"
          ]
        }
      }
    }
"""
import sys
import json
import asyncio
import argparse
import logging
from typing import Any, Dict, Optional
from pathlib import Path

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Log to stderr so stdout remains clean for MCP protocol
)
logger = logging.getLogger("mcp-stdio-bridge")


class MCPStdioBridge:
    """Bridge between stdio and HTTP/SSE MCP server"""

    def __init__(self, server_url: str, auth_token: str):
        self.server_url = server_url.rstrip('/')
        self.auth_token = auth_token
        self.client: Optional[httpx.AsyncClient] = None

    async def start(self):
        """Start the stdio bridge"""
        logger.info(f"Connecting to MCP server at {self.server_url}")

        # Create HTTP client with auth
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=60.0),
            headers={"Authorization": f"Bearer {self.auth_token}"}
        )

        # Test connection
        try:
            response = await self.client.get(f"{self.server_url}/health")
            if response.status_code != 200:
                logger.error(f"Server health check failed: {response.status_code}")
                sys.exit(1)
            logger.info("Connected to MCP server successfully")
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            sys.exit(1)

        # Start stdio server that forwards to HTTP/SSE
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "mcp_server.server"],  # Dummy, won't be used
            env=None
        )

        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                # Forward all tool calls to remote server
                logger.info("Bridge running, forwarding stdio to HTTP/SSE")

                # Keep connection alive
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    logger.info("Shutting down bridge")

    async def forward_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Forward MCP request to HTTP server"""
        try:
            response = await self.client.post(
                f"{self.server_url}/mcp",
                json={"method": method, "params": params}
            )
            return response.json()
        except Exception as e:
            logger.error(f"Request forwarding failed: {e}")
            return {"error": str(e)}


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MCP stdio bridge for Claude Code/Desktop")
    parser.add_argument("--server-url", required=True, help="MCP server URL (e.g., http://localhost:3001)")
    parser.add_argument("--token", required=True, help="Authentication token")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    bridge = MCPStdioBridge(args.server_url, args.token)
    await bridge.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Bridge crashed: {e}", exc_info=True)
        sys.exit(1)
