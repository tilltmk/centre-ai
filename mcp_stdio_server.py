#!/usr/bin/env python3
"""
MCP stdio Server - Runs centrally on the server

This stdio server runs on the same machine as the HTTP/SSE MCP server
and can be accessed via SSH from Claude Desktop/Code.

No local installation needed on client machines!

Usage via SSH in claude_desktop_config.json:
{
  "mcpServers": {
    "centre-ai": {
      "command": "ssh",
      "args": [
        "user@your-server.com",
        "python3",
        "/opt/centre-ai/mcp_stdio_server.py",
        "--token", "YOUR_TOKEN"
      ]
    }
  }
}

Or run as systemd socket service for direct stdio access.
"""
import sys
import os
import json
import asyncio
import argparse
import logging
from typing import Any, Dict
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, Resource
from mcp_server.tools import MCPTools, TOOL_DEFINITIONS
from mcp_server.database import init_databases
from mcp_server.config import config

# Log to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("mcp-stdio-server")


class MCPStdioServer:
    """stdio-based MCP Server that uses the same backend as HTTP/SSE"""

    def __init__(self, auth_token: str = None):
        self.server = Server("centre-ai")
        self.tools = MCPTools()
        self.auth_token = auth_token or config.security.mcp_auth_token
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
            logger.info(f"Tool call: {name}")

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
                logger.error(f"Tool error: {e}", exc_info=True)
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

    async def run(self):
        """Run the stdio server"""
        logger.info("Initializing databases...")
        await init_databases()
        logger.info("MCP stdio server started")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MCP stdio server")
    parser.add_argument("--token", help="Authentication token (optional)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    server = MCPStdioServer(auth_token=args.token)
    await server.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
