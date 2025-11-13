"""
Centre AI - Flask MCP Server
Main application entry point
"""

import os
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from src.mcp.server import MCPServer
from src.auth.manager import AuthManager
from src.memory.store import MemoryStore
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Initialize components
auth_manager = AuthManager()
memory_store = MemoryStore()
mcp_server = MCPServer(memory_store=memory_store)


# ============================================================================
# Authentication Decorator
# ============================================================================

def require_auth(f):
    """Decorator to require authentication for endpoints"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_result = auth_manager.authenticate(request)
        if not auth_result['authenticated']:
            return jsonify({
                'error': 'Authentication required',
                'message': auth_result.get('message', 'Invalid credentials')
            }), 401

        request.user = auth_result.get('user')
        return f(*args, **kwargs)

    return decorated_function


# ============================================================================
# Dashboard Routes
# ============================================================================

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('dashboard.html')


@app.route('/api/status')
@require_auth
def get_status():
    """Get server status"""
    return jsonify({
        'status': 'running',
        'version': '1.0.0',
        'mcp_server': {
            'initialized': mcp_server.is_initialized(),
            'tools_count': len(mcp_server.list_tools()),
            'memory_items': memory_store.count()
        }
    })


@app.route('/api/stats')
@require_auth
def get_stats():
    """Get usage statistics"""
    return jsonify({
        'total_requests': mcp_server.get_request_count(),
        'tools_executed': mcp_server.get_execution_count(),
        'memory_usage': memory_store.get_stats(),
        'active_sessions': mcp_server.get_active_sessions()
    })


# ============================================================================
# MCP Server Routes
# ============================================================================

@app.route('/mcp/initialize', methods=['POST'])
@require_auth
def mcp_initialize():
    """Initialize MCP server connection"""
    try:
        data = request.get_json() or {}
        client_info = {
            'name': data.get('client_name', 'unknown'),
            'version': data.get('client_version', '1.0.0'),
            'user': request.user
        }

        result = mcp_server.initialize(client_info)
        logger.info(f"MCP server initialized for {client_info['name']}")

        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error initializing MCP server: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/mcp/tools/list', methods=['GET'])
@require_auth
def mcp_list_tools():
    """List all available tools"""
    try:
        tools = mcp_server.list_tools()
        return jsonify({
            'tools': tools,
            'count': len(tools)
        }), 200
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/mcp/tools/execute', methods=['POST'])
@require_auth
def mcp_execute_tool():
    """Execute a tool"""
    try:
        data = request.get_json()
        if not data or 'tool_name' not in data:
            return jsonify({'error': 'tool_name is required'}), 400

        tool_name = data['tool_name']
        parameters = data.get('parameters', {})

        result = mcp_server.execute_tool(tool_name, parameters, user=request.user)
        logger.info(f"Tool {tool_name} executed by {request.user}")

        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error executing tool: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/mcp/memory/store', methods=['POST'])
@require_auth
def mcp_store_memory():
    """Store data in memory"""
    try:
        data = request.get_json()
        if not data or 'key' not in data or 'value' not in data:
            return jsonify({'error': 'key and value are required'}), 400

        key = data['key']
        value = data['value']
        tags = data.get('tags', [])
        ttl = data.get('ttl')

        result = memory_store.store(
            key=key,
            value=value,
            user=request.user,
            tags=tags,
            ttl=ttl
        )

        logger.info(f"Memory stored: {key} by {request.user}")
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error storing memory: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/mcp/memory/retrieve', methods=['GET'])
@require_auth
def mcp_retrieve_memory():
    """Retrieve data from memory"""
    try:
        key = request.args.get('key')
        tags = request.args.getlist('tags')

        if key:
            result = memory_store.retrieve(key, user=request.user)
        elif tags:
            result = memory_store.search_by_tags(tags, user=request.user)
        else:
            result = memory_store.list_all(user=request.user)

        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error retrieving memory: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/mcp/memory/delete', methods=['DELETE'])
@require_auth
def mcp_delete_memory():
    """Delete data from memory"""
    try:
        key = request.args.get('key')
        if not key:
            return jsonify({'error': 'key is required'}), 400

        result = memory_store.delete(key, user=request.user)
        logger.info(f"Memory deleted: {key} by {request.user}")

        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error deleting memory: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Health Check
# ============================================================================

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'centre-ai-mcp-server'
    }), 200


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'

    logger.info(f"Starting Centre AI MCP Server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")

    app.run(host=host, port=port, debug=debug)
