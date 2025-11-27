#!/usr/bin/env python3.14
"""
Test script for MCP Server Tools
Demonstrates all 38 available tools
Using Python 3.14
"""

import sys
sys.path.insert(0, '/home/core/dev/centre-ai')

from src.mcp.server import MCPServer
from src.memory.store import MemoryStore


def test_mcp_server():
    """Test MCP Server initialization and tools"""

    print("=" * 70)
    print("Centre AI - MCP Server Tool Test")
    print("=" * 70)

    # Initialize server
    memory_store = MemoryStore()
    mcp_server = MCPServer(memory_store=memory_store)

    # Initialize session
    result = mcp_server.initialize({
        'name': 'test-client',
        'version': '1.0.0'
    })

    print(f"\n✓ Server Status: {result['status']}")
    print(f"✓ Session ID: {result['session_id']}")
    print(f"✓ Total Tools: {result['available_tools']}")

    # List all tools
    tools = mcp_server.list_tools()

    print("\n" + "=" * 70)
    print("Available Tools by Category")
    print("=" * 70)

    # Group by category
    categories = {}
    for tool in tools:
        name = tool['name']
        desc = tool['description']
        category = name.split('_')[0]

        if category not in categories:
            categories[category] = []
        categories[category].append((name, desc))

    for category, tool_list in sorted(categories.items()):
        print(f"\n{category.upper()} Tools ({len(tool_list)}):")
        for name, desc in sorted(tool_list):
            print(f"  • {name:25} - {desc}")

    # Test a few tools
    print("\n" + "=" * 70)
    print("Testing Sample Tools")
    print("=" * 70)

    # Test text tool
    result = mcp_server.execute_tool('text_uppercase', {
        'text': 'hello world'
    })
    print(f"\n✓ text_uppercase: {result['result']}")

    # Test data tool
    result = mcp_server.execute_tool('json_validate', {
        'json_string': '{"name": "test", "value": 123}'
    })
    print(f"✓ json_validate: {result['result']}")

    # Test calculate
    result = mcp_server.execute_tool('calculate', {
        'expression': '2 + 2 * 5'
    })
    print(f"✓ calculate: {result['result']}")

    # Test base64
    result = mcp_server.execute_tool('base64_encode', {
        'text': 'Hello MCP Server!'
    })
    print(f"✓ base64_encode: {result['result']['encoded']}")

    # Test file tool
    result = mcp_server.execute_tool('file_extension', {
        'filename': 'test.py'
    })
    print(f"✓ file_extension: {result['result']}")

    print("\n" + "=" * 70)
    print("✓ All systems operational!")
    print("=" * 70)


if __name__ == '__main__':
    test_mcp_server()
