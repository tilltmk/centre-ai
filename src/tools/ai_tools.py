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
