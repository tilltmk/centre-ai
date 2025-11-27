#!/usr/bin/env python3
"""
Simplified MCP stdio Wrapper for Claude Code/Desktop

This wrapper creates a local stdio-based MCP server that proxies all
requests to the remote HTTP/SSE MCP server.

Usage in claude_desktop_config.json:
{
  "mcpServers": {
    "centre-ai": {
      "command": "python3",
      "args": [
        "/path/to/centre-ai/mcp_stdio_wrapper.py"
      ],
      "env": {
        "MCP_SERVER_URL": "http://localhost:3001",
        "MCP_AUTH_TOKEN": "your-token-here"
      }
    }
  }
}
"""
import sys
import os
import json
import asyncio
import logging
from typing import Any, Dict

# MCP SDK imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Setup logging to stderr (stdout is for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("mcp-wrapper")

# Configuration from environment
SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:3001")
AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")

if not AUTH_TOKEN:
    logger.error("MCP_AUTH_TOKEN environment variable is required!")
    sys.exit(1)


class MCPProxy:
    """Proxy MCP server that forwards to HTTP/SSE backend"""

    def __init__(self):
        self.server = Server("centre-ai-proxy")
        self.http_client = None
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup MCP protocol handlers that proxy to HTTP server"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """Fetch tools from remote server"""
            tools_data = await self._request("tools/list")
            return [
                Tool(
                    name=t["name"],
                    description=t["description"],
                    inputSchema=t["inputSchema"]
                )
                for t in tools_data.get("tools", [])
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Forward tool call to remote server"""
            logger.info(f"Proxying tool call: {name}")

            result = await self._request(
                "tools/call",
                {"name": name, "arguments": arguments}
            )

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]

    async def _request(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request to backend server"""
        import httpx

        if not self.http_client:
            self.http_client = httpx.AsyncClient(
                base_url=SERVER_URL,
                headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
                timeout=30.0
            )

        try:
            if data:
                response = await self.http_client.post(f"/api/{endpoint}", json=data)
            else:
                response = await self.http_client.get(f"/api/{endpoint}")

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Request to {endpoint} failed: {e}")
            return {"error": str(e)}

    async def run(self):
        """Run the stdio server"""
        logger.info(f"Starting MCP stdio wrapper, connecting to {SERVER_URL}")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    proxy = MCPProxy()
    await proxy.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
