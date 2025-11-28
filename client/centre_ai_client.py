#!/usr/bin/env python3
"""
Centre AI MCP STDIO Client
Standalone client for connecting to Centre AI MCP Server via STDIO
Can be downloaded and used independently from Git repository

Usage:
    python centre_ai_client.py [--host HOST] [--port PORT] [--transport TRANSPORT]

Transports:
    - stdio: Direct STDIO communication (default)
    - http: HTTP REST API
    - sse: Server-Sent Events
    - stream: Streamable HTTP
"""
import argparse
import asyncio
import json
import logging
import sys
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

try:
    import httpx
    import websockets
except ImportError:
    print("Missing dependencies. Install with: pip install httpx websockets")
    sys.exit(1)


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("centre_ai_client")


@dataclass
class ClientConfig:
    """Client configuration"""
    host: str = "localhost"
    http_port: int = 2070
    sse_port: int = 2071
    stream_port: int = 2072
    mcp_port: int = 2068
    transport: str = "http"  # http, sse, stream, stdio
    auth_token: Optional[str] = None


class CentreAIClient:
    """Centre AI MCP Client with multiple transport support"""

    def __init__(self, config: ClientConfig):
        self.config = config
        self.session: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry"""
        if self.config.transport in ["http", "stream"]:
            self.session = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()

    def get_base_url(self) -> str:
        """Get base URL for current transport"""
        if self.config.transport == "http":
            return f"http://{self.config.host}:{self.config.http_port}"
        elif self.config.transport == "stream":
            return f"http://{self.config.host}:{self.config.stream_port}"
        elif self.config.transport == "sse":
            return f"http://{self.config.host}:{self.config.sse_port}"
        else:  # stdio or others
            return f"http://{self.config.host}:{self.config.mcp_port}"

    def get_headers(self) -> Dict[str, str]:
        """Get headers including auth if available"""
        headers = {"Content-Type": "application/json"}
        if self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        return headers

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        if self.config.transport == "http":
            url = f"{self.get_base_url()}/tools"
            response = await self.session.get(url, headers=self.get_headers())
            response.raise_for_status()
            data = response.json()
            return data.get("tools", [])

        elif self.config.transport == "stream":
            url = f"{self.get_base_url()}/stream/tools"
            response = await self.session.get(url, headers=self.get_headers())
            response.raise_for_status()
            data = response.json()
            return data.get("tools", [])

        else:
            raise NotImplementedError(f"Tool listing not implemented for {self.config.transport}")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool"""
        if self.config.transport == "http":
            url = f"{self.get_base_url()}/mcp/call"
            payload = {"tool_name": tool_name, "arguments": arguments}
            response = await self.session.post(url, json=payload, headers=self.get_headers())
            response.raise_for_status()
            return response.json()

        elif self.config.transport == "stream":
            url = f"{self.get_base_url()}/stream/execute"
            payload = {"tool_name": tool_name, "arguments": arguments, "stream": False}
            response = await self.session.post(url, json=payload, headers=self.get_headers())
            response.raise_for_status()
            return response.json()

        else:
            raise NotImplementedError(f"Tool calling not implemented for {self.config.transport}")

    async def stream_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Stream tool execution (only for streamable transport)"""
        if self.config.transport != "stream":
            raise ValueError("Streaming only supported with 'stream' transport")

        url = f"{self.get_base_url()}/stream/execute"
        payload = {"tool_name": tool_name, "arguments": arguments, "stream": True}

        async with self.session.stream(
            "POST", url, json=payload, headers=self.get_headers()
        ) as response:
            response.raise_for_status()

            async for chunk in response.aiter_lines():
                if chunk.startswith("data: "):
                    try:
                        data = json.loads(chunk[6:])  # Remove "data: " prefix
                        yield data
                    except json.JSONDecodeError:
                        continue

    async def health_check(self) -> Dict[str, Any]:
        """Check server health"""
        if self.config.transport == "http":
            url = f"{self.get_base_url()}/health"
        elif self.config.transport == "stream":
            url = f"{self.get_base_url()}/stream/health"
        else:
            url = f"{self.get_base_url()}/health"

        response = await self.session.get(url)
        response.raise_for_status()
        return response.json()

    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        base_url = self.get_base_url()
        if self.config.transport == "stream":
            base_url += "/stream"

        response = await self.session.get(base_url)
        response.raise_for_status()
        return response.json()


# ==================== CLI INTERFACE ====================

async def interactive_mode(client: CentreAIClient):
    """Interactive mode for tool execution"""
    print("\n🤖 Centre AI Interactive Client")
    print("================================")

    try:
        # Get server info
        info = await client.get_server_info()
        print(f"Connected to: {info.get('name', 'Centre AI Server')}")
        print(f"Transport: {client.config.transport}")

        # Get available tools
        tools = await client.list_tools()
        print(f"\nAvailable tools ({len(tools)}):")
        for i, tool in enumerate(tools, 1):
            print(f"  {i:2d}. {tool['name']} - {tool['description'][:60]}...")

        while True:
            print("\nOptions:")
            print("  1-N: Execute tool by number")
            print("  list: Show tools again")
            print("  health: Check server health")
            print("  quit: Exit")

            choice = input("\n> ").strip()

            if choice.lower() in ["quit", "exit", "q"]:
                break
            elif choice.lower() == "list":
                for i, tool in enumerate(tools, 1):
                    print(f"  {i:2d}. {tool['name']} - {tool['description'][:60]}...")
            elif choice.lower() == "health":
                health = await client.health_check()
                print(f"Health: {health}")
            elif choice.isdigit():
                tool_idx = int(choice) - 1
                if 0 <= tool_idx < len(tools):
                    await execute_tool_interactive(client, tools[tool_idx])
                else:
                    print("Invalid tool number")
            else:
                print("Invalid choice")

    except Exception as e:
        logger.error(f"Interactive mode error: {e}")


async def execute_tool_interactive(client: CentreAIClient, tool: Dict[str, Any]):
    """Execute a tool interactively"""
    tool_name = tool["name"]
    schema = tool.get("inputSchema", {})
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    print(f"\n🔧 Executing tool: {tool_name}")
    print(f"Description: {tool['description']}")

    # Collect arguments
    arguments = {}

    if properties:
        print("\nProvide arguments (press Enter to skip optional):")
        for prop_name, prop_info in properties.items():
            is_required = prop_name in required
            prompt = f"  {prop_name}"
            if is_required:
                prompt += " (required)"
            prompt += f" [{prop_info.get('type', 'any')}]: "

            if prop_info.get('type') == 'boolean':
                value = input(prompt).strip().lower()
                if value:
                    arguments[prop_name] = value in ['true', 'yes', '1', 'y']
            elif prop_info.get('type') == 'integer':
                value = input(prompt).strip()
                if value:
                    try:
                        arguments[prop_name] = int(value)
                    except ValueError:
                        print(f"    Invalid integer, skipping {prop_name}")
            elif prop_info.get('type') == 'array':
                value = input(prompt).strip()
                if value:
                    # Simple comma-separated parsing
                    arguments[prop_name] = [item.strip() for item in value.split(',') if item.strip()]
            else:
                value = input(prompt).strip()
                if value:
                    arguments[prop_name] = value

    # Ask about streaming if available
    use_streaming = False
    if client.config.transport == "stream":
        stream_choice = input("\nUse streaming execution? [y/N]: ").strip().lower()
        use_streaming = stream_choice in ['y', 'yes', '1']

    print(f"\nExecuting {tool_name}...")

    try:
        if use_streaming:
            print("Streaming results:")
            async for chunk in client.stream_tool(tool_name, arguments):
                chunk_type = chunk.get('type', 'unknown')
                if chunk_type == 'progress':
                    progress = chunk.get('progress', 0) * 100
                    message = chunk.get('message', '')
                    print(f"  Progress: {progress:5.1f}% - {message}")
                elif chunk_type == 'data':
                    print(f"  Result: {json.dumps(chunk.get('data'), indent=2)}")
                elif chunk_type == 'error':
                    print(f"  Error: {chunk.get('data')}")
                elif chunk_type == 'complete':
                    print(f"  Completed: {chunk.get('message')}")
        else:
            result = await client.call_tool(tool_name, arguments)
            print(f"Result:\n{json.dumps(result, indent=2)}")

    except Exception as e:
        logger.error(f"Tool execution failed: {e}")


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Centre AI MCP Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode with HTTP transport
  python centre_ai_client.py

  # Use streaming transport
  python centre_ai_client.py --transport stream

  # Call specific tool
  python centre_ai_client.py --tool get_memory --args '{"query": "test", "limit": 5}'

  # Check server health
  python centre_ai_client.py --health

  # List available tools
  python centre_ai_client.py --list-tools
        """
    )

    parser.add_argument("--host", default="localhost", help="Server host (default: localhost)")
    parser.add_argument("--http-port", type=int, default=2070, help="HTTP port (default: 2070)")
    parser.add_argument("--sse-port", type=int, default=2071, help="SSE port (default: 2071)")
    parser.add_argument("--stream-port", type=int, default=2072, help="Stream port (default: 2072)")
    parser.add_argument("--mcp-port", type=int, default=2068, help="MCP port (default: 2068)")

    parser.add_argument(
        "--transport",
        choices=["http", "sse", "stream", "stdio"],
        default="http",
        help="Transport method (default: http)"
    )

    parser.add_argument("--auth-token", help="OAuth authentication token")
    parser.add_argument("--tool", help="Tool name to execute")
    parser.add_argument("--args", help="Tool arguments as JSON string")
    parser.add_argument("--health", action="store_true", help="Check server health")
    parser.add_argument("--list-tools", action="store_true", help="List available tools")
    parser.add_argument("--stream", action="store_true", help="Use streaming execution (if available)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    return parser


async def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create client config
    config = ClientConfig(
        host=args.host,
        http_port=args.http_port,
        sse_port=args.sse_port,
        stream_port=args.stream_port,
        mcp_port=args.mcp_port,
        transport=args.transport,
        auth_token=args.auth_token
    )

    async with CentreAIClient(config) as client:
        try:
            if args.health:
                health = await client.health_check()
                print(json.dumps(health, indent=2))

            elif args.list_tools:
                tools = await client.list_tools()
                print(f"Available tools ({len(tools)}):")
                for tool in tools:
                    print(f"  - {tool['name']}: {tool['description']}")

            elif args.tool:
                # Execute specific tool
                arguments = json.loads(args.args) if args.args else {}

                if args.stream and config.transport == "stream":
                    print(f"Streaming execution of {args.tool}...")
                    async for chunk in client.stream_tool(args.tool, arguments):
                        print(f"Chunk: {chunk}")
                else:
                    result = await client.call_tool(args.tool, arguments)
                    print(json.dumps(result, indent=2))

            else:
                # Interactive mode
                await interactive_mode(client)

        except Exception as e:
            logger.error(f"Client error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nClient interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)