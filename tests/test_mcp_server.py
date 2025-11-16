"""
Tests for MCPServer module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.mcp.server import MCPServer


class TestMCPServer:
    """Test suite for MCPServer"""

    @pytest.fixture
    def server(self):
        """Create MCPServer instance without dependencies"""
        with patch('src.mcp.server.MCPServer._register_default_tools'):
            server = MCPServer()
            server.tools_registry = {}
            return server

    @pytest.fixture
    def server_with_tools(self):
        """Create MCPServer with default tools registered"""
        return MCPServer()

    @pytest.fixture
    def mock_memory_store(self):
        """Create mock memory store"""
        store = Mock()
        store.store = Mock(return_value={'success': True})
        return store

    def test_init_without_dependencies(self, server):
        """Test server initialization without dependencies"""
        assert server.memory_store is None
        assert server.vector_db is None
        assert server.code_indexer is None
        assert server.initialized is False
        assert server.client_info == {}
        assert server.sessions == {}
        assert server.request_count == 0
        assert server.execution_count == 0

    def test_init_with_dependencies(self, mock_memory_store):
        """Test server initialization with dependencies"""
        with patch('src.mcp.server.MCPServer._register_default_tools'):
            server = MCPServer(memory_store=mock_memory_store)
            assert server.memory_store == mock_memory_store

    def test_register_default_tools(self, server_with_tools):
        """Test that default tools are registered"""
        tools = server_with_tools.tools_registry
        assert len(tools) > 0
        # Check some expected tools exist
        assert 'text_length' in tools
        assert 'json_format' in tools
        assert 'file_extension' in tools

    def test_register_tool_basic(self, server):
        """Test registering a basic tool"""
        tool = {
            'name': 'test_tool',
            'description': 'A test tool',
            'parameters': {},
            'handler': lambda x: {'result': 'test'}
        }
        server.register_tool(tool)
        assert 'test_tool' in server.tools_registry
        assert server.tools_registry['test_tool'] == tool

    def test_register_tool_without_name(self, server):
        """Test registering tool without name raises error"""
        tool = {'description': 'No name tool'}
        with pytest.raises(ValueError, match="must have a name"):
            server.register_tool(tool)

    def test_register_tool_overwrite(self, server):
        """Test overwriting existing tool"""
        tool1 = {'name': 'tool', 'handler': lambda x: 'v1'}
        tool2 = {'name': 'tool', 'handler': lambda x: 'v2'}
        server.register_tool(tool1)
        server.register_tool(tool2)
        assert server.tools_registry['tool'] == tool2

    def test_initialize_basic(self, server):
        """Test basic server initialization"""
        client_info = {'name': 'test-client', 'version': '1.0'}
        result = server.initialize(client_info)

        assert result['status'] == 'initialized'
        assert 'session_id' in result
        assert server.initialized is True
        assert server.client_info == client_info

    def test_initialize_creates_session(self, server):
        """Test that initialize creates a session"""
        result = server.initialize({'name': 'client'})
        session_id = result['session_id']

        assert session_id in server.sessions
        assert 'client_info' in server.sessions[session_id]
        assert 'created_at' in server.sessions[session_id]
        assert 'last_activity' in server.sessions[session_id]

    def test_initialize_server_info(self, server):
        """Test server info in initialization response"""
        result = server.initialize({'name': 'client'})

        assert 'server_info' in result
        assert result['server_info']['name'] == 'Centre AI MCP Server'
        assert result['server_info']['version'] == '1.0.0'
        assert result['server_info']['capabilities']['tools'] is True
        assert result['server_info']['capabilities']['memory'] is True

    def test_initialize_multiple_sessions(self, server):
        """Test creating multiple sessions"""
        result1 = server.initialize({'name': 'client1'})
        result2 = server.initialize({'name': 'client2'})

        assert result1['session_id'] != result2['session_id']
        assert len(server.sessions) == 2

    def test_is_initialized_false(self, server):
        """Test is_initialized when not initialized"""
        assert server.is_initialized() is False

    def test_is_initialized_true(self, server):
        """Test is_initialized after initialization"""
        server.initialize({'name': 'client'})
        assert server.is_initialized() is True

    def test_list_tools_empty(self, server):
        """Test listing tools when empty"""
        tools = server.list_tools()
        assert tools == []

    def test_list_tools_with_registered(self, server):
        """Test listing registered tools"""
        tool1 = {'name': 'tool1', 'handler': lambda x: x}
        tool2 = {'name': 'tool2', 'handler': lambda x: x}
        server.register_tool(tool1)
        server.register_tool(tool2)

        tools = server.list_tools()
        assert len(tools) == 2
        assert tool1 in tools
        assert tool2 in tools

    def test_execute_tool_basic(self, server):
        """Test basic tool execution"""
        tool = {
            'name': 'add_numbers',
            'handler': lambda params: {'sum': params['a'] + params['b']}
        }
        server.register_tool(tool)

        result = server.execute_tool('add_numbers', {'a': 2, 'b': 3})
        assert result['success'] is True
        assert result['result']['sum'] == 5
        assert result['tool'] == 'add_numbers'
        assert 'execution_time' in result

    def test_execute_tool_increments_counts(self, server):
        """Test that execution increments counters"""
        tool = {'name': 'test', 'handler': lambda x: {}}
        server.register_tool(tool)

        initial_request = server.request_count
        initial_execution = server.execution_count

        server.execute_tool('test', {})

        assert server.request_count == initial_request + 1
        assert server.execution_count == initial_execution + 1

    def test_execute_tool_not_found(self, server):
        """Test executing non-existent tool"""
        with pytest.raises(ValueError, match="not found"):
            server.execute_tool('nonexistent', {})

    def test_execute_tool_no_handler(self, server):
        """Test executing tool without handler"""
        tool = {'name': 'no_handler'}
        server.tools_registry['no_handler'] = tool

        with pytest.raises(ValueError, match="no handler"):
            server.execute_tool('no_handler', {})

    def test_execute_tool_with_error(self, server):
        """Test tool execution that raises an error"""
        def failing_handler(params):
            raise ValueError("Tool failed!")

        tool = {'name': 'failing', 'handler': failing_handler}
        server.register_tool(tool)

        result = server.execute_tool('failing', {})
        assert result['success'] is False
        assert 'Tool failed!' in result['error']
        assert result['tool'] == 'failing'

    def test_execute_tool_with_memory_store(self):
        """Test tool execution with memory store logging"""
        mock_store = Mock()
        mock_store.store = Mock(return_value={'success': True})

        with patch('src.mcp.server.MCPServer._register_default_tools'):
            server = MCPServer(memory_store=mock_store)
            server.tools_registry = {}

        tool = {'name': 'test', 'handler': lambda x: {'data': 'result'}}
        server.register_tool(tool)

        server.execute_tool('test', {'param': 'value'}, user='testuser')

        # Verify memory store was called
        mock_store.store.assert_called_once()
        call_args = mock_store.store.call_args
        assert 'execution_' in call_args.kwargs['key'] or 'execution_' in call_args[1].get('key', call_args[0][0])

    def test_execute_tool_without_user(self, server):
        """Test execution without user doesn't store to memory"""
        tool = {'name': 'test', 'handler': lambda x: {}}
        server.register_tool(tool)

        # Should not raise error even without memory store or user
        result = server.execute_tool('test', {})
        assert result['success'] is True

    def test_get_request_count(self, server):
        """Test getting request count"""
        assert server.get_request_count() == 0

        tool = {'name': 'test', 'handler': lambda x: {}}
        server.register_tool(tool)
        server.execute_tool('test', {})
        server.execute_tool('test', {})

        assert server.get_request_count() == 2

    def test_get_execution_count(self, server):
        """Test getting execution count"""
        assert server.get_execution_count() == 0

        tool = {'name': 'test', 'handler': lambda x: {}}
        server.register_tool(tool)
        server.execute_tool('test', {})

        assert server.get_execution_count() == 1

    def test_get_execution_count_with_errors(self, server):
        """Test execution count doesn't increment on errors"""
        def error_handler(x):
            raise Exception("Error")

        tool = {'name': 'error', 'handler': error_handler}
        server.register_tool(tool)

        initial = server.get_execution_count()
        server.execute_tool('error', {})

        # Count should not increment on failure
        assert server.get_execution_count() == initial

    def test_get_active_sessions_empty(self, server):
        """Test getting active sessions when empty"""
        assert server.get_active_sessions() == 0

    def test_get_active_sessions_with_sessions(self, server):
        """Test getting active session count"""
        server.initialize({'name': 'client1'})
        server.initialize({'name': 'client2'})

        assert server.get_active_sessions() == 2

    def test_get_tool_exists(self, server):
        """Test getting existing tool"""
        tool = {'name': 'test', 'handler': lambda x: {}}
        server.register_tool(tool)

        retrieved = server.get_tool('test')
        assert retrieved == tool

    def test_get_tool_not_exists(self, server):
        """Test getting non-existent tool"""
        result = server.get_tool('nonexistent')
        assert result is None

    def test_full_workflow(self, server):
        """Test complete server workflow"""
        # Register tool
        tool = {
            'name': 'multiply',
            'description': 'Multiply two numbers',
            'parameters': {'a': 'number', 'b': 'number'},
            'handler': lambda p: {'product': p['a'] * p['b']}
        }
        server.register_tool(tool)

        # Initialize
        init_result = server.initialize({'name': 'test-client'})
        assert init_result['status'] == 'initialized'
        assert server.is_initialized()

        # List tools
        tools = server.list_tools()
        assert len(tools) == 1

        # Execute tool
        exec_result = server.execute_tool('multiply', {'a': 4, 'b': 5}, user='user1')
        assert exec_result['success'] is True
        assert exec_result['result']['product'] == 20

        # Check stats
        assert server.get_request_count() == 1
        assert server.get_execution_count() == 1
        assert server.get_active_sessions() == 1

    def test_default_tools_functionality(self, server_with_tools):
        """Test that default tools actually work"""
        # Test text_length tool
        result = server_with_tools.execute_tool('text_length', {'text': 'hello'})
        assert result['success'] is True
        assert result['result']['length'] == 5

        # Test json_validate tool
        result = server_with_tools.execute_tool('json_validate', {'json_string': '{"key": "value"}'})
        assert result['success'] is True
        assert result['result']['valid'] is True

    def test_tool_execution_timing(self, server):
        """Test that execution time is measured"""
        import time

        def slow_handler(params):
            time.sleep(0.1)
            return {'done': True}

        tool = {'name': 'slow', 'handler': slow_handler}
        server.register_tool(tool)

        result = server.execute_tool('slow', {})
        assert result['execution_time'] >= 0.1

    def test_tool_with_complex_parameters(self, server):
        """Test tool with complex nested parameters"""
        def complex_handler(params):
            return {
                'config_name': params['config']['name'],
                'item_count': len(params['items']),
                'flag': params['flags']['enabled']
            }

        tool = {'name': 'complex', 'handler': complex_handler}
        server.register_tool(tool)

        result = server.execute_tool('complex', {
            'config': {'name': 'test'},
            'items': [1, 2, 3],
            'flags': {'enabled': True}
        })

        assert result['success'] is True
        assert result['result']['config_name'] == 'test'
        assert result['result']['item_count'] == 3
        assert result['result']['flag'] is True
