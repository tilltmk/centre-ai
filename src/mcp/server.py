"""
MCP Server Core Implementation
Implements the Model Context Protocol for AI model interactions
"""

import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MCPServer:
    """Main MCP Server class"""

    def __init__(self, memory_store=None):
        self.memory_store = memory_store
        self.initialized = False
        self.client_info = {}
        self.sessions = {}
        self.request_count = 0
        self.execution_count = 0
        self.tools_registry = {}

        # Register default tools
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default tools"""
        from src.tools.text_tools import TextTools
        from src.tools.data_tools import DataTools
        from src.tools.web_tools import WebTools
        from src.tools.file_tools import FileTools

        # Register all tool categories
        text_tools = TextTools()
        data_tools = DataTools()
        web_tools = WebTools()
        file_tools = FileTools()

        for tool in text_tools.get_tools():
            self.register_tool(tool)

        for tool in data_tools.get_tools():
            self.register_tool(tool)

        for tool in web_tools.get_tools():
            self.register_tool(tool)

        for tool in file_tools.get_tools():
            self.register_tool(tool)

        logger.info(f"Registered {len(self.tools_registry)} tools")

    def register_tool(self, tool: Dict[str, Any]):
        """Register a new tool"""
        tool_name = tool.get('name')
        if not tool_name:
            raise ValueError("Tool must have a name")

        self.tools_registry[tool_name] = tool
        logger.debug(f"Registered tool: {tool_name}")

    def initialize(self, client_info: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize MCP server with client information"""
        session_id = str(uuid.uuid4())
        self.client_info = client_info
        self.initialized = True

        self.sessions[session_id] = {
            'client_info': client_info,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat()
        }

        logger.info(f"MCP Server initialized - Session: {session_id}")

        return {
            'status': 'initialized',
            'session_id': session_id,
            'server_info': {
                'name': 'Centre AI MCP Server',
                'version': '1.0.0',
                'capabilities': {
                    'tools': True,
                    'memory': True,
                    'streaming': False
                }
            },
            'available_tools': len(self.tools_registry)
        }

    def is_initialized(self) -> bool:
        """Check if server is initialized"""
        return self.initialized

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools"""
        return list(self.tools_registry.values())

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any], user: str = None) -> Dict[str, Any]:
        """Execute a tool with given parameters"""
        self.request_count += 1

        if tool_name not in self.tools_registry:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool = self.tools_registry[tool_name]
        handler = tool.get('handler')

        if not handler:
            raise ValueError(f"Tool '{tool_name}' has no handler")

        try:
            start_time = time.time()

            # Execute the tool
            result = handler(parameters)

            execution_time = time.time() - start_time
            self.execution_count += 1

            # Log execution
            logger.info(f"Tool '{tool_name}' executed in {execution_time:.3f}s by {user}")

            # Store in memory if available
            if self.memory_store and user:
                self.memory_store.store(
                    key=f"execution_{uuid.uuid4()}",
                    value={
                        'tool': tool_name,
                        'parameters': parameters,
                        'result': result,
                        'execution_time': execution_time,
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    user=user,
                    tags=['execution', tool_name]
                )

            return {
                'success': True,
                'tool': tool_name,
                'result': result,
                'execution_time': execution_time
            }

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {str(e)}")
            return {
                'success': False,
                'tool': tool_name,
                'error': str(e)
            }

    def get_request_count(self) -> int:
        """Get total request count"""
        return self.request_count

    def get_execution_count(self) -> int:
        """Get total execution count"""
        return self.execution_count

    def get_active_sessions(self) -> int:
        """Get number of active sessions"""
        return len(self.sessions)

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get a specific tool by name"""
        return self.tools_registry.get(tool_name)
