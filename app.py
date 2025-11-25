"""
Centre AI - Flask MCP Server (Extended Version)
Main application with all features: Git, Code Indexing, Profiles, Conversations
"""

import os
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from src.mcp.server import MCPServer
from src.auth.manager import AuthManager
from src.memory.store import MemoryStore
from src.vector.qdrant_client import VectorDB
from src.indexing.code_indexer import CodeIndexer
from src.profiles.manager import ProfileManager, ConversationManager, MemoryManager
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
vector_db = VectorDB()
code_indexer = CodeIndexer(vector_db=vector_db)
profile_manager = ProfileManager()
conversation_manager = ConversationManager()
memory_manager = MemoryManager()
mcp_server = MCPServer(
    memory_store=memory_store,
    vector_db=vector_db,
    code_indexer=code_indexer
)


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
        'version': '2.0.0',
        'mcp_server': {
            'initialized': mcp_server.is_initialized(),
            'tools_count': len(mcp_server.list_tools()),
            'memory_items': memory_store.count()
        },
        'services': {
            'vector_db': {
                'connected': len(vector_db.list_collections()) >= 0,
                'collections': vector_db.list_collections()
            },
            'postgres': {
                'connected': True
            }
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
        'active_sessions': mcp_server.get_active_sessions(),
        'vector_collections': len(vector_db.list_collections())
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


# ============================================================================
# Profile Routes
# ============================================================================

@app.route('/api/profile', methods=['GET'])
@require_auth
def get_profile():
    """Get user profile"""
    try:
        result = profile_manager.get_profile(request.user)
        return jsonify(result), 200 if result['success'] else 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile', methods=['POST'])
@require_auth
def create_or_update_profile():
    """Create or update user profile"""
    try:
        data = request.get_json()
        result = profile_manager.create_or_update_profile(
            user_id=request.user,
            full_name=data.get('full_name'),
            email=data.get('email'),
            bio=data.get('bio'),
            preferences=data.get('preferences'),
            metadata=data.get('metadata')
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/profile/preferences', methods=['PUT'])
@require_auth
def update_preferences():
    """Update user preferences"""
    try:
        data = request.get_json()
        result = profile_manager.update_preferences(
            user_id=request.user,
            preferences=data
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Conversation Routes
# ============================================================================

@app.route('/api/conversations', methods=['POST'])
@require_auth
def create_conversation():
    """Create new conversation"""
    try:
        data = request.get_json()
        result = conversation_manager.create_conversation(
            user_id=request.user,
            session_id=data.get('session_id'),
            title=data.get('title'),
            context=data.get('context')
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/conversations/<session_id>/messages', methods=['POST'])
@require_auth
def add_message(session_id):
    """Add message to conversation"""
    try:
        data = request.get_json()
        result = conversation_manager.add_message(
            session_id=session_id,
            role=data.get('role'),
            content=data.get('content'),
            metadata=data.get('metadata')
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/conversations/<session_id>/history', methods=['GET'])
@require_auth
def get_conversation_history(session_id):
    """Get conversation history"""
    try:
        limit = int(request.args.get('limit', 100))
        result = conversation_manager.get_conversation_history(session_id, limit)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/conversations', methods=['GET'])
@require_auth
def get_user_conversations():
    """Get user's conversations"""
    try:
        limit = int(request.args.get('limit', 50))
        result = conversation_manager.get_user_conversations(request.user, limit)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Memory Routes (Long-term)
# ============================================================================

@app.route('/api/memories', methods=['POST'])
@require_auth
def store_memory():
    """Store long-term memory"""
    try:
        data = request.get_json()
        result = memory_manager.store_memory(
            user_id=request.user,
            memory_type=data.get('memory_type'),
            content=data.get('content'),
            importance=data.get('importance', 5),
            tags=data.get('tags'),
            metadata=data.get('metadata')
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/memories', methods=['GET'])
@require_auth
def get_memories():
    """Get memories"""
    try:
        memory_type = request.args.get('memory_type')
        tags = request.args.getlist('tags')
        limit = int(request.args.get('limit', 100))

        result = memory_manager.get_memories(
            user_id=request.user,
            memory_type=memory_type,
            tags=tags if tags else None,
            limit=limit
        )
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/memories/<memory_id>', methods=['DELETE'])
@require_auth
def delete_memory(memory_id):
    """Delete memory"""
    try:
        result = memory_manager.delete_memory(memory_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Code Search Routes
# ============================================================================

@app.route('/api/code/search', methods=['POST'])
@require_auth
def search_code():
    """Search code semantically"""
    try:
        data = request.get_json()
        query = data.get('query')
        repo_id = data.get('repo_id')
        language = data.get('language')
        limit = data.get('limit', 10)

        results = code_indexer.search_code(
            query=query,
            repo_id=repo_id,
            language=language,
            limit=limit
        )

        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# Health Check
# ============================================================================

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'centre-ai-mcp-server',
        'version': '2.0.0'
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

    logger.info(f"Starting Centre AI MCP Server v2.0.0 on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info("Features: Git, Code Indexing, Profiles, Conversations, Memories")

    app.run(host=host, port=port, debug=debug)
