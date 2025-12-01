"""
AI Knowledge Management Tools
Tools for managing artifacts, instructions, memories, and projects through AI
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


def get_db_connection():
    """Get PostgreSQL database connection"""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', 5432),
        database=os.getenv('POSTGRES_DB', 'centre_ai'),
        user=os.getenv('POSTGRES_USER', 'centre_ai'),
        password=os.getenv('POSTGRES_PASSWORD', 'centre_ai_secret')
    )


class AITools:
    """AI-powered knowledge management tools"""

    def __init__(self):
        self.artifact_types = ['code', 'document', 'diagram', 'config', 'data', 'image', 'template']
        self.instruction_scopes = ['global', 'project', 'session']
        self.memory_types = ['fact', 'preference', 'context', 'learning', 'reference', 'note']

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of AI tools"""
        return [
            # ========== ARTIFACT TOOLS ==========
            {
                'name': 'artifact_create',
                'description': 'Create and store an artifact (code, document, config, etc.)',
                'parameters': {
                    'title': {'type': 'string', 'required': True, 'description': 'Artifact title'},
                    'content': {'type': 'string', 'required': True, 'description': 'Artifact content'},
                    'artifact_type': {'type': 'string', 'required': True, 'description': f'Type: {", ".join(self.artifact_types)}'},
                    'language': {'type': 'string', 'required': False, 'description': 'Programming language (if code)'},
                    'tags': {'type': 'array', 'required': False, 'description': 'Tags for categorization'},
                    'project_id': {'type': 'integer', 'required': False, 'description': 'Associated project ID'},
                    'metadata': {'type': 'object', 'required': False, 'description': 'Additional metadata'}
                },
                'handler': self.artifact_create
            },
            {
                'name': 'artifact_update',
                'description': 'Update an existing artifact (creates new version)',
                'parameters': {
                    'artifact_id': {'type': 'integer', 'required': True, 'description': 'Artifact ID to update'},
                    'content': {'type': 'string', 'required': True, 'description': 'New content'},
                    'title': {'type': 'string', 'required': False, 'description': 'New title (optional)'}
                },
                'handler': self.artifact_update
            },
            {
                'name': 'artifact_get',
                'description': 'Retrieve an artifact by ID',
                'parameters': {
                    'artifact_id': {'type': 'integer', 'required': True, 'description': 'Artifact ID'}
                },
                'handler': self.artifact_get
            },
            {
                'name': 'artifact_search',
                'description': 'Search artifacts by type, tags, or project',
                'parameters': {
                    'artifact_type': {'type': 'string', 'required': False, 'description': 'Filter by type'},
                    'tags': {'type': 'array', 'required': False, 'description': 'Filter by tags'},
                    'project_id': {'type': 'integer', 'required': False, 'description': 'Filter by project'},
                    'query': {'type': 'string', 'required': False, 'description': 'Search in title/content'},
                    'limit': {'type': 'integer', 'required': False, 'description': 'Max results', 'default': 20}
                },
                'handler': self.artifact_search
            },
            {
                'name': 'artifact_delete',
                'description': 'Delete an artifact',
                'parameters': {
                    'artifact_id': {'type': 'integer', 'required': True, 'description': 'Artifact ID to delete'}
                },
                'handler': self.artifact_delete
            },
            {
                'name': 'artifact_list_versions',
                'description': 'List all versions of an artifact',
                'parameters': {
                    'artifact_id': {'type': 'integer', 'required': True, 'description': 'Artifact ID'}
                },
                'handler': self.artifact_list_versions
            },

            # ========== INSTRUCTION TOOLS ==========
            {
                'name': 'instruction_create',
                'description': 'Create a new instruction/directive for AI behavior',
                'parameters': {
                    'title': {'type': 'string', 'required': True, 'description': 'Instruction title'},
                    'content': {'type': 'string', 'required': True, 'description': 'Instruction content'},
                    'category': {'type': 'string', 'required': False, 'description': 'Category (coding, communication, etc.)'},
                    'priority': {'type': 'integer', 'required': False, 'description': 'Priority 1-10', 'default': 5},
                    'scope': {'type': 'string', 'required': False, 'description': f'Scope: {", ".join(self.instruction_scopes)}', 'default': 'global'}
                },
                'handler': self.instruction_create
            },
            {
                'name': 'instruction_update',
                'description': 'Update an existing instruction',
                'parameters': {
                    'instruction_id': {'type': 'integer', 'required': True, 'description': 'Instruction ID'},
                    'content': {'type': 'string', 'required': False, 'description': 'New content'},
                    'title': {'type': 'string', 'required': False, 'description': 'New title'},
                    'priority': {'type': 'integer', 'required': False, 'description': 'New priority'},
                    'is_active': {'type': 'boolean', 'required': False, 'description': 'Active status'}
                },
                'handler': self.instruction_update
            },
            {
                'name': 'instruction_list',
                'description': 'List all active instructions',
                'parameters': {
                    'category': {'type': 'string', 'required': False, 'description': 'Filter by category'},
                    'scope': {'type': 'string', 'required': False, 'description': 'Filter by scope'},
                    'include_inactive': {'type': 'boolean', 'required': False, 'description': 'Include inactive', 'default': False}
                },
                'handler': self.instruction_list
            },
            {
                'name': 'instruction_delete',
                'description': 'Delete or deactivate an instruction',
                'parameters': {
                    'instruction_id': {'type': 'integer', 'required': True, 'description': 'Instruction ID'},
                    'permanent': {'type': 'boolean', 'required': False, 'description': 'Permanently delete', 'default': False}
                },
                'handler': self.instruction_delete
            },

            # ========== MEMORY TOOLS ==========
            {
                'name': 'memory_create',
                'description': 'Store a new memory/fact for long-term retention',
                'parameters': {
                    'content': {'type': 'string', 'required': True, 'description': 'Memory content'},
                    'memory_type': {'type': 'string', 'required': True, 'description': f'Type: {", ".join(self.memory_types)}'},
                    'importance': {'type': 'integer', 'required': False, 'description': 'Importance 1-10', 'default': 5},
                    'tags': {'type': 'array', 'required': False, 'description': 'Tags for categorization'},
                    'metadata': {'type': 'object', 'required': False, 'description': 'Additional context'}
                },
                'handler': self.memory_create
            },
            {
                'name': 'memory_update',
                'description': 'Update an existing memory',
                'parameters': {
                    'memory_id': {'type': 'integer', 'required': True, 'description': 'Memory ID'},
                    'content': {'type': 'string', 'required': False, 'description': 'New content'},
                    'importance': {'type': 'integer', 'required': False, 'description': 'New importance'},
                    'tags': {'type': 'array', 'required': False, 'description': 'New tags'}
                },
                'handler': self.memory_update
            },
            {
                'name': 'memory_search',
                'description': 'Search memories by type, tags, or content',
                'parameters': {
                    'memory_type': {'type': 'string', 'required': False, 'description': 'Filter by type'},
                    'tags': {'type': 'array', 'required': False, 'description': 'Filter by tags'},
                    'query': {'type': 'string', 'required': False, 'description': 'Search in content'},
                    'min_importance': {'type': 'integer', 'required': False, 'description': 'Minimum importance'},
                    'limit': {'type': 'integer', 'required': False, 'description': 'Max results', 'default': 50}
                },
                'handler': self.memory_search
            },
            {
                'name': 'memory_delete',
                'description': 'Delete a memory',
                'parameters': {
                    'memory_id': {'type': 'integer', 'required': True, 'description': 'Memory ID to delete'}
                },
                'handler': self.memory_delete
            },
            {
                'name': 'memory_get_context',
                'description': 'Get relevant memories for a given context/topic',
                'parameters': {
                    'topic': {'type': 'string', 'required': True, 'description': 'Topic to find memories for'},
                    'limit': {'type': 'integer', 'required': False, 'description': 'Max memories', 'default': 10}
                },
                'handler': self.memory_get_context
            },

            # ========== PROJECT TOOLS ==========
            {
                'name': 'project_create',
                'description': 'Create a new project',
                'parameters': {
                    'name': {'type': 'string', 'required': True, 'description': 'Project name'},
                    'description': {'type': 'string', 'required': False, 'description': 'Project description'},
                    'priority': {'type': 'integer', 'required': False, 'description': 'Priority 1-10', 'default': 5},
                    'tags': {'type': 'array', 'required': False, 'description': 'Project tags'},
                    'metadata': {'type': 'object', 'required': False, 'description': 'Additional metadata'}
                },
                'handler': self.project_create
            },
            {
                'name': 'project_update',
                'description': 'Update a project',
                'parameters': {
                    'project_id': {'type': 'integer', 'required': True, 'description': 'Project ID'},
                    'name': {'type': 'string', 'required': False, 'description': 'New name'},
                    'description': {'type': 'string', 'required': False, 'description': 'New description'},
                    'status': {'type': 'string', 'required': False, 'description': 'Status: active, paused, completed, archived'},
                    'priority': {'type': 'integer', 'required': False, 'description': 'New priority'}
                },
                'handler': self.project_update
            },
            {
                'name': 'project_list',
                'description': 'List all projects',
                'parameters': {
                    'status': {'type': 'string', 'required': False, 'description': 'Filter by status'},
                    'tags': {'type': 'array', 'required': False, 'description': 'Filter by tags'}
                },
                'handler': self.project_list
            },
            {
                'name': 'project_get',
                'description': 'Get project details with associated artifacts',
                'parameters': {
                    'project_id': {'type': 'integer', 'required': True, 'description': 'Project ID'}
                },
                'handler': self.project_get
            },
            {
                'name': 'project_delete',
                'description': 'Delete a project',
                'parameters': {
                    'project_id': {'type': 'integer', 'required': True, 'description': 'Project ID'}
                },
                'handler': self.project_delete
            },

            # ========== CODEBASE INDEXING TOOLS ==========
            {
                'name': 'codebase_index',
                'description': 'Index a local codebase or git repository for semantic search',
                'parameters': {
                    'path': {'type': 'string', 'required': True, 'description': 'Path to codebase or repo name'},
                    'name': {'type': 'string', 'required': False, 'description': 'Name for the codebase index'},
                    'is_git_repo': {'type': 'boolean', 'required': False, 'description': 'If true, path is a git repo name', 'default': False}
                },
                'handler': self.codebase_index
            },
            {
                'name': 'codebase_search',
                'description': 'Semantically search indexed codebases',
                'parameters': {
                    'query': {'type': 'string', 'required': True, 'description': 'Search query'},
                    'repo_id': {'type': 'string', 'required': False, 'description': 'Filter by specific codebase'},
                    'language': {'type': 'string', 'required': False, 'description': 'Filter by programming language'},
                    'limit': {'type': 'integer', 'required': False, 'description': 'Max results', 'default': 10}
                },
                'handler': self.codebase_search
            },
            {
                'name': 'codebase_list',
                'description': 'List all indexed codebases',
                'parameters': {},
                'handler': self.codebase_list
            },

            # ========== KNOWLEDGE GRAPH TOOLS ==========
            {
                'name': 'knowledge_create_node',
                'description': 'Create a knowledge node (concept, entity, topic)',
                'parameters': {
                    'title': {'type': 'string', 'required': True, 'description': 'Node title'},
                    'node_type': {'type': 'string', 'required': True, 'description': 'Type: concept, entity, topic, person, technology, project, event'},
                    'content': {'type': 'string', 'required': False, 'description': 'Detailed description'},
                    'parent_id': {'type': 'integer', 'required': False, 'description': 'Parent node ID for hierarchy'},
                    'metadata': {'type': 'object', 'required': False, 'description': 'Additional metadata'}
                },
                'handler': self.knowledge_create_node
            },
            {
                'name': 'knowledge_connect',
                'description': 'Connect two knowledge nodes with a relationship',
                'parameters': {
                    'source_id': {'type': 'integer', 'required': True, 'description': 'Source node ID'},
                    'target_id': {'type': 'integer', 'required': True, 'description': 'Target node ID'},
                    'relationship': {'type': 'string', 'required': True, 'description': 'Relationship type (e.g. relates_to, depends_on, part_of, uses, created_by)'},
                    'weight': {'type': 'number', 'required': False, 'description': 'Connection strength 0-1', 'default': 1.0},
                    'metadata': {'type': 'object', 'required': False, 'description': 'Additional context'}
                },
                'handler': self.knowledge_connect
            },
            {
                'name': 'knowledge_connect_entities',
                'description': 'Connect any two entities (memory, artifact, project, instruction) in the knowledge graph',
                'parameters': {
                    'source_type': {'type': 'string', 'required': True, 'description': 'Source type: memory, artifact, project, instruction, node'},
                    'source_id': {'type': 'integer', 'required': True, 'description': 'Source entity ID'},
                    'target_type': {'type': 'string', 'required': True, 'description': 'Target type: memory, artifact, project, instruction, node'},
                    'target_id': {'type': 'integer', 'required': True, 'description': 'Target entity ID'},
                    'relationship': {'type': 'string', 'required': True, 'description': 'Relationship description'},
                    'weight': {'type': 'number', 'required': False, 'description': 'Connection strength', 'default': 1.0}
                },
                'handler': self.knowledge_connect_entities
            },
            {
                'name': 'knowledge_get_connections',
                'description': 'Get all connections for a node or entity',
                'parameters': {
                    'node_id': {'type': 'integer', 'required': False, 'description': 'Knowledge node ID'},
                    'entity_type': {'type': 'string', 'required': False, 'description': 'Entity type if not a node'},
                    'entity_id': {'type': 'integer', 'required': False, 'description': 'Entity ID if not a node'},
                    'direction': {'type': 'string', 'required': False, 'description': 'both, outgoing, incoming', 'default': 'both'}
                },
                'handler': self.knowledge_get_connections
            },
            {
                'name': 'knowledge_search_nodes',
                'description': 'Search knowledge nodes',
                'parameters': {
                    'query': {'type': 'string', 'required': False, 'description': 'Search query'},
                    'node_type': {'type': 'string', 'required': False, 'description': 'Filter by node type'},
                    'limit': {'type': 'integer', 'required': False, 'description': 'Max results', 'default': 50}
                },
                'handler': self.knowledge_search_nodes
            },
            {
                'name': 'knowledge_get_graph',
                'description': 'Get the full knowledge graph or a subgraph',
                'parameters': {
                    'center_node_id': {'type': 'integer', 'required': False, 'description': 'Center node for subgraph'},
                    'depth': {'type': 'integer', 'required': False, 'description': 'Traversal depth', 'default': 2},
                    'include_entities': {'type': 'boolean', 'required': False, 'description': 'Include linked entities', 'default': True}
                },
                'handler': self.knowledge_get_graph
            },
            {
                'name': 'knowledge_delete_node',
                'description': 'Delete a knowledge node and its connections',
                'parameters': {
                    'node_id': {'type': 'integer', 'required': True, 'description': 'Node ID to delete'}
                },
                'handler': self.knowledge_delete_node
            },
            {
                'name': 'knowledge_delete_connection',
                'description': 'Delete a connection between nodes',
                'parameters': {
                    'edge_id': {'type': 'integer', 'required': True, 'description': 'Edge ID to delete'}
                },
                'handler': self.knowledge_delete_connection
            }
        ]

    # ========== ARTIFACT IMPLEMENTATIONS ==========

    def artifact_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new artifact"""
        title = params.get('title')
        content = params.get('content')
        artifact_type = params.get('artifact_type')
        language = params.get('language')
        tags = params.get('tags', [])
        project_id = params.get('project_id')
        metadata = params.get('metadata', {})

        if artifact_type not in self.artifact_types:
            return {'success': False, 'error': f'Invalid artifact_type. Must be one of: {", ".join(self.artifact_types)}'}

        # Determine file extension and mime type
        ext_map = {
            'code': {'python': '.py', 'javascript': '.js', 'typescript': '.ts', 'java': '.java', 'go': '.go', 'rust': '.rs'},
            'document': '.md',
            'config': '.json',
            'data': '.json',
            'diagram': '.mmd'
        }

        mime_map = {
            'code': 'text/plain',
            'document': 'text/markdown',
            'config': 'application/json',
            'data': 'application/json',
            'diagram': 'text/plain',
            'image': 'image/png'
        }

        file_ext = None
        if artifact_type == 'code' and language:
            file_ext = ext_map.get('code', {}).get(language.lower(), '.txt')
        elif artifact_type in ext_map:
            file_ext = ext_map[artifact_type] if isinstance(ext_map[artifact_type], str) else '.txt'

        mime_type = mime_map.get(artifact_type, 'text/plain')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                INSERT INTO artifacts (title, content, artifact_type, language, mime_type, file_extension,
                                       project_id, tags, metadata, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, title, artifact_type, version, created_at
            """, (title, content, artifact_type, language, mime_type, file_ext,
                  project_id, tags, json.dumps(metadata), 'ai'))

            artifact = dict(cur.fetchone())
            conn.commit()
            cur.close()
            conn.close()

            logger.info(f"Created artifact: {artifact['id']} - {title}")

            return {
                'success': True,
                'artifact_id': artifact['id'],
                'title': artifact['title'],
                'type': artifact['artifact_type'],
                'version': artifact['version'],
                'message': f'Artifact "{title}" created successfully'
            }

        except Exception as e:
            logger.error(f"Error creating artifact: {str(e)}")
            return {'success': False, 'error': str(e)}

    def artifact_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update an artifact (creates new version)"""
        artifact_id = params.get('artifact_id')
        content = params.get('content')
        title = params.get('title')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get existing artifact
            cur.execute("SELECT * FROM artifacts WHERE id = %s", (artifact_id,))
            existing = cur.fetchone()

            if not existing:
                cur.close()
                conn.close()
                return {'success': False, 'error': f'Artifact {artifact_id} not found'}

            # Create new version
            new_version = existing['version'] + 1
            new_title = title or existing['title']

            cur.execute("""
                INSERT INTO artifacts (title, content, artifact_type, language, mime_type, file_extension,
                                       version, parent_id, project_id, tags, metadata, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, version
            """, (new_title, content, existing['artifact_type'], existing['language'],
                  existing['mime_type'], existing['file_extension'], new_version, artifact_id,
                  existing['project_id'], existing['tags'], existing['metadata'], 'ai'))

            new_artifact = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'artifact_id': new_artifact['id'],
                'version': new_artifact['version'],
                'parent_id': artifact_id,
                'message': f'Artifact updated to version {new_version}'
            }

        except Exception as e:
            logger.error(f"Error updating artifact: {str(e)}")
            return {'success': False, 'error': str(e)}

    def artifact_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get artifact by ID"""
        artifact_id = params.get('artifact_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("SELECT * FROM artifacts WHERE id = %s", (artifact_id,))
            artifact = cur.fetchone()

            cur.close()
            conn.close()

            if not artifact:
                return {'success': False, 'error': f'Artifact {artifact_id} not found'}

            return {
                'success': True,
                'artifact': {
                    'id': artifact['id'],
                    'title': artifact['title'],
                    'content': artifact['content'],
                    'artifact_type': artifact['artifact_type'],
                    'language': artifact['language'],
                    'version': artifact['version'],
                    'tags': artifact['tags'],
                    'metadata': artifact['metadata'],
                    'created_at': artifact['created_at'].isoformat() if artifact['created_at'] else None
                }
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def artifact_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search artifacts"""
        artifact_type = params.get('artifact_type')
        tags = params.get('tags', [])
        project_id = params.get('project_id')
        query = params.get('query')
        limit = params.get('limit', 20)

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            conditions = ["parent_id IS NULL"]  # Only get latest versions
            values = []

            if artifact_type:
                conditions.append("artifact_type = %s")
                values.append(artifact_type)

            if tags:
                conditions.append("tags && %s")
                values.append(tags)

            if project_id:
                conditions.append("project_id = %s")
                values.append(project_id)

            if query:
                conditions.append("(title ILIKE %s OR content ILIKE %s)")
                values.extend([f'%{query}%', f'%{query}%'])

            where_clause = " AND ".join(conditions)
            values.append(limit)

            cur.execute(f"""
                SELECT id, title, artifact_type, language, version, tags, created_at
                FROM artifacts
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s
            """, values)

            artifacts = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            for a in artifacts:
                if a['created_at']:
                    a['created_at'] = a['created_at'].isoformat()

            return {
                'success': True,
                'artifacts': artifacts,
                'count': len(artifacts)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def artifact_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an artifact"""
        artifact_id = params.get('artifact_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("DELETE FROM artifacts WHERE id = %s OR parent_id = %s", (artifact_id, artifact_id))
            deleted = cur.rowcount

            conn.commit()
            cur.close()
            conn.close()

            if deleted == 0:
                return {'success': False, 'error': f'Artifact {artifact_id} not found'}

            return {
                'success': True,
                'message': f'Deleted artifact {artifact_id} and {deleted-1} versions'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def artifact_list_versions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all versions of an artifact"""
        artifact_id = params.get('artifact_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT id, title, version, created_at
                FROM artifacts
                WHERE id = %s OR parent_id = %s
                ORDER BY version DESC
            """, (artifact_id, artifact_id))

            versions = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            for v in versions:
                if v['created_at']:
                    v['created_at'] = v['created_at'].isoformat()

            return {
                'success': True,
                'versions': versions,
                'count': len(versions)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== INSTRUCTION IMPLEMENTATIONS ==========

    def instruction_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new instruction"""
        title = params.get('title')
        content = params.get('content')
        category = params.get('category')
        priority = params.get('priority', 5)
        scope = params.get('scope', 'global')

        if scope not in self.instruction_scopes:
            return {'success': False, 'error': f'Invalid scope. Must be one of: {", ".join(self.instruction_scopes)}'}

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                INSERT INTO instructions (title, content, category, priority, scope, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, title, priority, scope
            """, (title, content, category, priority, scope, 'ai'))

            instruction = dict(cur.fetchone())
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'instruction_id': instruction['id'],
                'title': instruction['title'],
                'priority': instruction['priority'],
                'scope': instruction['scope'],
                'message': f'Instruction "{title}" created'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def instruction_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update an instruction"""
        instruction_id = params.get('instruction_id')
        content = params.get('content')
        title = params.get('title')
        priority = params.get('priority')
        is_active = params.get('is_active')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            updates = []
            values = []

            if content is not None:
                updates.append("content = %s")
                values.append(content)
            if title is not None:
                updates.append("title = %s")
                values.append(title)
            if priority is not None:
                updates.append("priority = %s")
                values.append(priority)
            if is_active is not None:
                updates.append("is_active = %s")
                values.append(is_active)

            if not updates:
                return {'success': False, 'error': 'No updates provided'}

            values.append(instruction_id)
            cur.execute(f"""
                UPDATE instructions
                SET {', '.join(updates)}
                WHERE id = %s
            """, values)

            updated = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            if updated == 0:
                return {'success': False, 'error': f'Instruction {instruction_id} not found'}

            return {
                'success': True,
                'message': f'Instruction {instruction_id} updated'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def instruction_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List instructions"""
        category = params.get('category')
        scope = params.get('scope')
        include_inactive = params.get('include_inactive', False)

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            conditions = []
            values = []

            if not include_inactive:
                conditions.append("is_active = true")

            if category:
                conditions.append("category = %s")
                values.append(category)

            if scope:
                conditions.append("scope = %s")
                values.append(scope)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            cur.execute(f"""
                SELECT id, title, content, category, priority, scope, is_active, created_at
                FROM instructions
                WHERE {where_clause}
                ORDER BY priority DESC, created_at DESC
            """, values)

            instructions = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            for i in instructions:
                if i['created_at']:
                    i['created_at'] = i['created_at'].isoformat()

            return {
                'success': True,
                'instructions': instructions,
                'count': len(instructions)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def instruction_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete or deactivate an instruction"""
        instruction_id = params.get('instruction_id')
        permanent = params.get('permanent', False)

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            if permanent:
                cur.execute("DELETE FROM instructions WHERE id = %s", (instruction_id,))
                action = "deleted"
            else:
                cur.execute("UPDATE instructions SET is_active = false WHERE id = %s", (instruction_id,))
                action = "deactivated"

            affected = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            if affected == 0:
                return {'success': False, 'error': f'Instruction {instruction_id} not found'}

            return {
                'success': True,
                'message': f'Instruction {instruction_id} {action}'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== MEMORY IMPLEMENTATIONS ==========

    def memory_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new memory"""
        content = params.get('content')
        memory_type = params.get('memory_type')
        importance = params.get('importance', 5)
        tags = params.get('tags', [])
        metadata = params.get('metadata', {})

        if memory_type not in self.memory_types:
            return {'success': False, 'error': f'Invalid memory_type. Must be one of: {", ".join(self.memory_types)}'}

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                INSERT INTO memories (content, memory_type, importance, tags, metadata, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, memory_type, importance
            """, (content, memory_type, importance, tags, json.dumps(metadata), 'ai'))

            memory = dict(cur.fetchone())
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'memory_id': memory['id'],
                'memory_type': memory['memory_type'],
                'importance': memory['importance'],
                'message': 'Memory stored successfully'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def memory_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a memory"""
        memory_id = params.get('memory_id')
        content = params.get('content')
        importance = params.get('importance')
        tags = params.get('tags')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            updates = []
            values = []

            if content is not None:
                updates.append("content = %s")
                values.append(content)
            if importance is not None:
                updates.append("importance = %s")
                values.append(importance)
            if tags is not None:
                updates.append("tags = %s")
                values.append(tags)

            if not updates:
                return {'success': False, 'error': 'No updates provided'}

            values.append(memory_id)
            cur.execute(f"""
                UPDATE memories
                SET {', '.join(updates)}
                WHERE id = %s
            """, values)

            updated = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            if updated == 0:
                return {'success': False, 'error': f'Memory {memory_id} not found'}

            return {
                'success': True,
                'message': f'Memory {memory_id} updated'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def memory_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search memories"""
        memory_type = params.get('memory_type')
        tags = params.get('tags', [])
        query = params.get('query')
        min_importance = params.get('min_importance')
        limit = params.get('limit', 50)

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            conditions = []
            values = []

            if memory_type:
                conditions.append("memory_type = %s")
                values.append(memory_type)

            if tags:
                conditions.append("tags && %s")
                values.append(tags)

            if query:
                conditions.append("content ILIKE %s")
                values.append(f'%{query}%')

            if min_importance:
                conditions.append("importance >= %s")
                values.append(min_importance)

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            values.append(limit)

            cur.execute(f"""
                SELECT id, content, memory_type, importance, tags, created_at
                FROM memories
                WHERE {where_clause}
                ORDER BY importance DESC, created_at DESC
                LIMIT %s
            """, values)

            memories = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            for m in memories:
                if m['created_at']:
                    m['created_at'] = m['created_at'].isoformat()

            return {
                'success': True,
                'memories': memories,
                'count': len(memories)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def memory_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a memory"""
        memory_id = params.get('memory_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("DELETE FROM memories WHERE id = %s", (memory_id,))
            deleted = cur.rowcount

            conn.commit()
            cur.close()
            conn.close()

            if deleted == 0:
                return {'success': False, 'error': f'Memory {memory_id} not found'}

            return {
                'success': True,
                'message': f'Memory {memory_id} deleted'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def memory_get_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get memories relevant to a topic"""
        topic = params.get('topic')
        limit = params.get('limit', 10)

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Simple keyword search - could be enhanced with embeddings
            cur.execute("""
                SELECT id, content, memory_type, importance, tags
                FROM memories
                WHERE content ILIKE %s
                ORDER BY importance DESC
                LIMIT %s
            """, (f'%{topic}%', limit))

            memories = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            return {
                'success': True,
                'topic': topic,
                'memories': memories,
                'count': len(memories)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== PROJECT IMPLEMENTATIONS ==========

    def project_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project"""
        name = params.get('name')
        description = params.get('description')
        priority = params.get('priority', 5)
        tags = params.get('tags', [])
        metadata = params.get('metadata', {})

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                INSERT INTO projects (name, description, priority, tags, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, name, status
            """, (name, description, priority, tags, json.dumps(metadata)))

            project = dict(cur.fetchone())
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'project_id': project['id'],
                'name': project['name'],
                'status': project['status'],
                'message': f'Project "{name}" created'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def project_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a project"""
        project_id = params.get('project_id')
        name = params.get('name')
        description = params.get('description')
        status = params.get('status')
        priority = params.get('priority')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            updates = []
            values = []

            if name is not None:
                updates.append("name = %s")
                values.append(name)
            if description is not None:
                updates.append("description = %s")
                values.append(description)
            if status is not None:
                updates.append("status = %s")
                values.append(status)
            if priority is not None:
                updates.append("priority = %s")
                values.append(priority)

            if not updates:
                return {'success': False, 'error': 'No updates provided'}

            values.append(project_id)
            cur.execute(f"""
                UPDATE projects
                SET {', '.join(updates)}
                WHERE id = %s
            """, values)

            updated = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            if updated == 0:
                return {'success': False, 'error': f'Project {project_id} not found'}

            return {
                'success': True,
                'message': f'Project {project_id} updated'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def project_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List projects"""
        status = params.get('status')
        tags = params.get('tags', [])

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            conditions = []
            values = []

            if status:
                conditions.append("status = %s")
                values.append(status)

            if tags:
                conditions.append("tags && %s")
                values.append(tags)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            cur.execute(f"""
                SELECT id, name, description, status, priority, tags, created_at
                FROM projects
                WHERE {where_clause}
                ORDER BY priority DESC, created_at DESC
            """, values)

            projects = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            for p in projects:
                if p['created_at']:
                    p['created_at'] = p['created_at'].isoformat()

            return {
                'success': True,
                'projects': projects,
                'count': len(projects)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def project_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get project with artifacts"""
        project_id = params.get('project_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            project = cur.fetchone()

            if not project:
                cur.close()
                conn.close()
                return {'success': False, 'error': f'Project {project_id} not found'}

            # Get associated artifacts
            cur.execute("""
                SELECT id, title, artifact_type, version, created_at
                FROM artifacts
                WHERE project_id = %s AND parent_id IS NULL
                ORDER BY created_at DESC
            """, (project_id,))

            artifacts = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            project = dict(project)
            if project['created_at']:
                project['created_at'] = project['created_at'].isoformat()

            for a in artifacts:
                if a['created_at']:
                    a['created_at'] = a['created_at'].isoformat()

            return {
                'success': True,
                'project': project,
                'artifacts': artifacts,
                'artifact_count': len(artifacts)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def project_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a project"""
        project_id = params.get('project_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))
            deleted = cur.rowcount

            conn.commit()
            cur.close()
            conn.close()

            if deleted == 0:
                return {'success': False, 'error': f'Project {project_id} not found'}

            return {
                'success': True,
                'message': f'Project {project_id} deleted'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== CODEBASE INDEXING IMPLEMENTATIONS ==========

    def codebase_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Index a codebase for semantic search"""
        path = params.get('path')
        name = params.get('name')
        is_git_repo = params.get('is_git_repo', False)

        try:
            from src.indexing.code_indexer import CodeIndexer
            from src.vector.qdrant_client import VectorDB

            # Resolve path
            if is_git_repo:
                git_repos_path = os.path.join(os.path.expanduser('~'), '.centre-ai', 'git_repos')
                codebase_path = os.path.join(git_repos_path, path)
                codebase_name = name or path
            else:
                codebase_path = os.path.expanduser(path)
                codebase_name = name or os.path.basename(codebase_path)

            if not os.path.exists(codebase_path):
                return {'success': False, 'error': f'Path not found: {codebase_path}'}

            # Initialize indexer with vector DB
            vector_db = VectorDB()
            indexer = CodeIndexer(vector_db=vector_db)

            # Scan and index
            files = indexer.scan_repository(codebase_path)

            if not files:
                return {
                    'success': True,
                    'codebase': codebase_name,
                    'files_indexed': 0,
                    'message': 'No code files found to index'
                }

            # Index files
            indexed = 0
            failed = 0
            for file_info in files:
                if indexer.index_file(codebase_name, file_info):
                    indexed += 1
                else:
                    failed += 1

            # Store codebase info in database
            conn = get_db_connection()
            cur = conn.cursor()
            languages = list(set(f['language'] for f in files))
            cur.execute("""
                INSERT INTO codebases (name, local_path, file_count, indexed_at, metadata, language)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    file_count = EXCLUDED.file_count,
                    indexed_at = CURRENT_TIMESTAMP,
                    metadata = EXCLUDED.metadata,
                    local_path = EXCLUDED.local_path
            """, (codebase_name, codebase_path, indexed,
                  json.dumps({'languages': languages}), languages[0] if languages else None))
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'codebase': codebase_name,
                'path': codebase_path,
                'files_scanned': len(files),
                'files_indexed': indexed,
                'files_failed': failed,
                'languages': list(set(f['language'] for f in files))
            }

        except Exception as e:
            logger.error(f"Error indexing codebase: {str(e)}")
            return {'success': False, 'error': str(e)}

    def codebase_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search indexed codebases semantically"""
        query = params.get('query')
        repo_id = params.get('repo_id')
        language = params.get('language')
        limit = params.get('limit', 10)

        if not query:
            return {'success': False, 'error': 'Query is required'}

        try:
            from src.indexing.code_indexer import CodeIndexer
            from src.vector.qdrant_client import VectorDB

            vector_db = VectorDB()
            indexer = CodeIndexer(vector_db=vector_db)

            results = indexer.search_code(
                query=query,
                repo_id=repo_id,
                language=language,
                limit=limit
            )

            return {
                'success': True,
                'query': query,
                'results': results,
                'count': len(results)
            }

        except Exception as e:
            logger.error(f"Error searching codebase: {str(e)}")
            return {'success': False, 'error': str(e)}

    def codebase_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all indexed codebases"""
        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT id, name, local_path, file_count, indexed_at, metadata
                FROM codebases
                ORDER BY indexed_at DESC
            """)

            codebases = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            for cb in codebases:
                if cb['indexed_at']:
                    cb['indexed_at'] = cb['indexed_at'].isoformat()

            return {
                'success': True,
                'codebases': codebases,
                'count': len(codebases)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== KNOWLEDGE GRAPH IMPLEMENTATIONS ==========

    def knowledge_create_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a knowledge node"""
        title = params.get('title')
        node_type = params.get('node_type')
        content = params.get('content')
        parent_id = params.get('parent_id')
        metadata = params.get('metadata', {})

        valid_types = ['concept', 'entity', 'topic', 'person', 'technology', 'project', 'event', 'memory_ref', 'artifact_ref', 'project_ref', 'instruction_ref']
        if node_type not in valid_types:
            return {'success': False, 'error': f'Invalid node_type. Must be one of: {", ".join(valid_types)}'}

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                INSERT INTO knowledge_nodes (title, node_type, content, parent_id, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, title, node_type
            """, (title, node_type, content, parent_id, json.dumps(metadata)))

            node = dict(cur.fetchone())
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'node_id': node['id'],
                'title': node['title'],
                'node_type': node['node_type'],
                'message': f'Knowledge node "{title}" created'
            }

        except Exception as e:
            logger.error(f"Error creating knowledge node: {str(e)}")
            return {'success': False, 'error': str(e)}

    def knowledge_connect(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Connect two knowledge nodes"""
        source_id = params.get('source_id')
        target_id = params.get('target_id')
        relationship = params.get('relationship')
        weight = params.get('weight', 1.0)
        metadata = params.get('metadata', {})

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Verify both nodes exist
            cur.execute("SELECT id, title FROM knowledge_nodes WHERE id IN (%s, %s)", (source_id, target_id))
            nodes = cur.fetchall()
            if len(nodes) < 2:
                cur.close()
                conn.close()
                return {'success': False, 'error': 'One or both nodes not found'}

            # Create edge
            cur.execute("""
                INSERT INTO knowledge_edges (source_id, target_id, relationship, weight, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (source_id, target_id, relationship, weight, json.dumps(metadata)))

            edge = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'edge_id': edge['id'],
                'source_id': source_id,
                'target_id': target_id,
                'relationship': relationship,
                'message': f'Connection "{relationship}" created'
            }

        except Exception as e:
            logger.error(f"Error connecting nodes: {str(e)}")
            return {'success': False, 'error': str(e)}

    def knowledge_connect_entities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Connect any two entities through the knowledge graph"""
        source_type = params.get('source_type')
        source_id = params.get('source_id')
        target_type = params.get('target_type')
        target_id = params.get('target_id')
        relationship = params.get('relationship')
        weight = params.get('weight', 1.0)

        valid_types = ['memory', 'artifact', 'project', 'instruction', 'node']

        if source_type not in valid_types or target_type not in valid_types:
            return {'success': False, 'error': f'Invalid entity type. Must be one of: {", ".join(valid_types)}'}

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Helper to get or create reference node for entity
            def get_or_create_ref_node(entity_type, entity_id):
                if entity_type == 'node':
                    cur.execute("SELECT id, title FROM knowledge_nodes WHERE id = %s", (entity_id,))
                    node = cur.fetchone()
                    if node:
                        return node['id'], node['title']
                    return None, None

                # Map entity types to tables and ref node types
                table_map = {
                    'memory': ('memories', 'content', 'memory_ref'),
                    'artifact': ('artifacts', 'title', 'artifact_ref'),
                    'project': ('projects', 'name', 'project_ref'),
                    'instruction': ('instructions', 'title', 'instruction_ref')
                }

                table, title_col, ref_type = table_map[entity_type]

                # Get entity title
                cur.execute(f"SELECT id, {title_col} as title FROM {table} WHERE id = %s", (entity_id,))
                entity = cur.fetchone()
                if not entity:
                    return None, None

                entity_title = entity['title'][:100] if entity['title'] else f'{entity_type}_{entity_id}'

                # Check if reference node already exists
                cur.execute("""
                    SELECT id, title FROM knowledge_nodes
                    WHERE node_type = %s AND metadata->>'entity_id' = %s
                """, (ref_type, str(entity_id)))
                existing = cur.fetchone()

                if existing:
                    return existing['id'], existing['title']

                # Create reference node
                cur.execute("""
                    INSERT INTO knowledge_nodes (title, node_type, content, metadata)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, title
                """, (entity_title, ref_type, f'Reference to {entity_type} #{entity_id}',
                      json.dumps({'entity_type': entity_type, 'entity_id': entity_id})))

                new_node = cur.fetchone()
                return new_node['id'], new_node['title']

            # Get or create nodes for both entities
            source_node_id, source_title = get_or_create_ref_node(source_type, source_id)
            if not source_node_id:
                cur.close()
                conn.close()
                return {'success': False, 'error': f'Source {source_type} #{source_id} not found'}

            target_node_id, target_title = get_or_create_ref_node(target_type, target_id)
            if not target_node_id:
                cur.close()
                conn.close()
                return {'success': False, 'error': f'Target {target_type} #{target_id} not found'}

            # Create the edge
            cur.execute("""
                INSERT INTO knowledge_edges (source_id, target_id, relationship, weight, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (source_node_id, target_node_id, relationship, weight,
                  json.dumps({'source_entity': f'{source_type}:{source_id}', 'target_entity': f'{target_type}:{target_id}'})))

            edge = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'edge_id': edge['id'],
                'source': {'type': source_type, 'id': source_id, 'node_id': source_node_id, 'title': source_title},
                'target': {'type': target_type, 'id': target_id, 'node_id': target_node_id, 'title': target_title},
                'relationship': relationship,
                'message': f'Connected {source_type} "{source_title}" --[{relationship}]--> {target_type} "{target_title}"'
            }

        except Exception as e:
            logger.error(f"Error connecting entities: {str(e)}")
            return {'success': False, 'error': str(e)}

    def knowledge_get_connections(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get connections for a node or entity"""
        node_id = params.get('node_id')
        entity_type = params.get('entity_type')
        entity_id = params.get('entity_id')
        direction = params.get('direction', 'both')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # If entity specified, find its reference node
            if entity_type and entity_id and not node_id:
                ref_type = f'{entity_type}_ref'
                cur.execute("""
                    SELECT id FROM knowledge_nodes
                    WHERE node_type = %s AND metadata->>'entity_id' = %s
                """, (ref_type, str(entity_id)))
                ref_node = cur.fetchone()
                if ref_node:
                    node_id = ref_node['id']
                else:
                    cur.close()
                    conn.close()
                    return {'success': True, 'connections': [], 'count': 0}

            if not node_id:
                cur.close()
                conn.close()
                return {'success': False, 'error': 'No node_id or entity specified'}

            connections = []

            # Outgoing connections
            if direction in ['both', 'outgoing']:
                cur.execute("""
                    SELECT e.id as edge_id, e.relationship, e.weight, e.metadata as edge_metadata,
                           n.id as target_id, n.title as target_title, n.node_type as target_type
                    FROM knowledge_edges e
                    JOIN knowledge_nodes n ON e.target_id = n.id
                    WHERE e.source_id = %s
                """, (node_id,))
                for row in cur.fetchall():
                    connections.append({
                        'direction': 'outgoing',
                        'edge_id': row['edge_id'],
                        'relationship': row['relationship'],
                        'weight': row['weight'],
                        'node_id': row['target_id'],
                        'node_title': row['target_title'],
                        'node_type': row['target_type']
                    })

            # Incoming connections
            if direction in ['both', 'incoming']:
                cur.execute("""
                    SELECT e.id as edge_id, e.relationship, e.weight, e.metadata as edge_metadata,
                           n.id as source_id, n.title as source_title, n.node_type as source_type
                    FROM knowledge_edges e
                    JOIN knowledge_nodes n ON e.source_id = n.id
                    WHERE e.target_id = %s
                """, (node_id,))
                for row in cur.fetchall():
                    connections.append({
                        'direction': 'incoming',
                        'edge_id': row['edge_id'],
                        'relationship': row['relationship'],
                        'weight': row['weight'],
                        'node_id': row['source_id'],
                        'node_title': row['source_title'],
                        'node_type': row['source_type']
                    })

            cur.close()
            conn.close()

            return {
                'success': True,
                'node_id': node_id,
                'connections': connections,
                'count': len(connections)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def knowledge_search_nodes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search knowledge nodes"""
        query = params.get('query')
        node_type = params.get('node_type')
        limit = params.get('limit', 50)

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            conditions = []
            values = []

            if query:
                conditions.append("(title ILIKE %s OR content ILIKE %s)")
                values.extend([f'%{query}%', f'%{query}%'])

            if node_type:
                conditions.append("node_type = %s")
                values.append(node_type)

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            values.append(limit)

            cur.execute(f"""
                SELECT id, title, node_type, content, parent_id, metadata, created_at
                FROM knowledge_nodes
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s
            """, values)

            nodes = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            for n in nodes:
                if n['created_at']:
                    n['created_at'] = n['created_at'].isoformat()

            return {
                'success': True,
                'nodes': nodes,
                'count': len(nodes)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def knowledge_get_graph(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get knowledge graph data for visualization"""
        center_node_id = params.get('center_node_id')
        depth = params.get('depth', 2)
        include_entities = params.get('include_entities', True)

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            if center_node_id:
                # Get subgraph around center node
                visited = set()
                to_visit = [(center_node_id, 0)]
                nodes = []
                edges = []

                while to_visit:
                    current_id, current_depth = to_visit.pop(0)
                    if current_id in visited or current_depth > depth:
                        continue
                    visited.add(current_id)

                    # Get node
                    cur.execute("SELECT * FROM knowledge_nodes WHERE id = %s", (current_id,))
                    node = cur.fetchone()
                    if node:
                        nodes.append(dict(node))

                        # Get edges
                        cur.execute("""
                            SELECT * FROM knowledge_edges
                            WHERE source_id = %s OR target_id = %s
                        """, (current_id, current_id))

                        for edge in cur.fetchall():
                            edge_dict = dict(edge)
                            if edge_dict not in edges:
                                edges.append(edge_dict)
                            # Add connected nodes to visit
                            next_id = edge['target_id'] if edge['source_id'] == current_id else edge['source_id']
                            if next_id not in visited:
                                to_visit.append((next_id, current_depth + 1))
            else:
                # Get full graph
                cur.execute("SELECT * FROM knowledge_nodes ORDER BY created_at DESC LIMIT 200")
                nodes = [dict(row) for row in cur.fetchall()]

                cur.execute("SELECT * FROM knowledge_edges LIMIT 500")
                edges = [dict(row) for row in cur.fetchall()]

            cur.close()
            conn.close()

            # Format for visualization
            for n in nodes:
                if n.get('created_at'):
                    n['created_at'] = n['created_at'].isoformat()
            for e in edges:
                if e.get('created_at'):
                    e['created_at'] = e['created_at'].isoformat()

            return {
                'success': True,
                'nodes': nodes,
                'edges': edges,
                'node_count': len(nodes),
                'edge_count': len(edges)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def knowledge_delete_node(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a knowledge node"""
        node_id = params.get('node_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("DELETE FROM knowledge_nodes WHERE id = %s", (node_id,))
            deleted = cur.rowcount

            conn.commit()
            cur.close()
            conn.close()

            if deleted == 0:
                return {'success': False, 'error': f'Node {node_id} not found'}

            return {
                'success': True,
                'message': f'Node {node_id} and its connections deleted'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def knowledge_delete_connection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a knowledge edge"""
        edge_id = params.get('edge_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("DELETE FROM knowledge_edges WHERE id = %s", (edge_id,))
            deleted = cur.rowcount

            conn.commit()
            cur.close()
            conn.close()

            if deleted == 0:
                return {'success': False, 'error': f'Edge {edge_id} not found'}

            return {
                'success': True,
                'message': f'Connection {edge_id} deleted'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
