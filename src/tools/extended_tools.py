"""
Extended AI Tools for Centre AI
Advanced tools for tasks, milestones, notes, summaries, triggers, and conversation management
"""

import os
import re
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import json
import uuid

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


class ExtendedAITools:
    """Extended AI tools for advanced knowledge management"""

    def __init__(self):
        self.task_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        self.note_types = ['general', 'idea', 'todo', 'question', 'reference', 'meeting', 'research']
        self.trigger_types = ['scheduled', 'event', 'webhook', 'condition', 'keyword']
        self.action_types = ['execute_tool', 'send_notification', 'create_memory', 'create_instruction',
                            'create_note', 'update_project', 'webhook_call']

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of extended AI tools"""
        return [
            # ========== CONVERSATION LOGGING TOOLS ==========
            {
                'name': 'conversation_log',
                'description': 'Log a conversation or message exchange automatically. Use this to store every interaction.',
                'parameters': {
                    'session_id': {'type': 'string', 'required': False, 'description': 'Session ID (auto-generated if not provided)'},
                    'title': {'type': 'string', 'required': False, 'description': 'Conversation title'},
                    'user_message': {'type': 'string', 'required': True, 'description': 'The user message'},
                    'assistant_response': {'type': 'string', 'required': True, 'description': 'The assistant response'},
                    'tool_calls': {'type': 'array', 'required': False, 'description': 'List of tools called during response'},
                    'client_name': {'type': 'string', 'required': False, 'description': 'Client application name'},
                    'extract_instructions': {'type': 'boolean', 'required': False, 'description': 'Auto-extract instructions from conversation', 'default': True}
                },
                'handler': self.conversation_log
            },
            {
                'name': 'conversation_get_history',
                'description': 'Get conversation history for a session or search across conversations',
                'parameters': {
                    'session_id': {'type': 'string', 'required': False, 'description': 'Specific session ID'},
                    'query': {'type': 'string', 'required': False, 'description': 'Search query in content'},
                    'user_id': {'type': 'string', 'required': False, 'description': 'Filter by user'},
                    'from_date': {'type': 'string', 'required': False, 'description': 'Start date (YYYY-MM-DD)'},
                    'to_date': {'type': 'string', 'required': False, 'description': 'End date (YYYY-MM-DD)'},
                    'limit': {'type': 'integer', 'required': False, 'description': 'Max results', 'default': 50}
                },
                'handler': self.conversation_get_history
            },
            {
                'name': 'conversation_summarize',
                'description': 'Generate and store a summary for a conversation',
                'parameters': {
                    'session_id': {'type': 'string', 'required': True, 'description': 'Session ID to summarize'},
                    'title': {'type': 'string', 'required': False, 'description': 'Summary title'},
                    'key_points': {'type': 'array', 'required': False, 'description': 'Key points extracted'},
                    'action_items': {'type': 'array', 'required': False, 'description': 'Action items identified'},
                    'summary_text': {'type': 'string', 'required': True, 'description': 'The summary text'}
                },
                'handler': self.conversation_summarize
            },
            {
                'name': 'conversation_extract_topics',
                'description': 'Extract and store topics discussed in a conversation',
                'parameters': {
                    'session_id': {'type': 'string', 'required': True, 'description': 'Session ID'},
                    'topics': {'type': 'array', 'required': True, 'description': 'List of topics identified'}
                },
                'handler': self.conversation_extract_topics
            },

            # ========== TASK MANAGEMENT TOOLS ==========
            {
                'name': 'task_create',
                'description': 'Create a new task within a project. Tasks can have subtasks and due dates.',
                'parameters': {
                    'project_id': {'type': 'integer', 'required': True, 'description': 'Project ID for this task'},
                    'title': {'type': 'string', 'required': True, 'description': 'Task title'},
                    'description': {'type': 'string', 'required': False, 'description': 'Detailed task description'},
                    'priority': {'type': 'integer', 'required': False, 'description': 'Priority 1-10', 'default': 5},
                    'due_date': {'type': 'string', 'required': False, 'description': 'Due date (YYYY-MM-DD)'},
                    'assigned_to': {'type': 'string', 'required': False, 'description': 'Assignee'},
                    'parent_task_id': {'type': 'integer', 'required': False, 'description': 'Parent task ID for subtasks'},
                    'tags': {'type': 'array', 'required': False, 'description': 'Task tags'}
                },
                'handler': self.task_create
            },
            {
                'name': 'task_update',
                'description': 'Update an existing task status, priority, or details',
                'parameters': {
                    'task_id': {'type': 'integer', 'required': True, 'description': 'Task ID'},
                    'title': {'type': 'string', 'required': False, 'description': 'New title'},
                    'description': {'type': 'string', 'required': False, 'description': 'New description'},
                    'status': {'type': 'string', 'required': False, 'description': 'Status: pending, in_progress, completed, cancelled'},
                    'priority': {'type': 'integer', 'required': False, 'description': 'New priority'},
                    'due_date': {'type': 'string', 'required': False, 'description': 'New due date'},
                    'assigned_to': {'type': 'string', 'required': False, 'description': 'New assignee'}
                },
                'handler': self.task_update
            },
            {
                'name': 'task_list',
                'description': 'List tasks with optional filters by project, status, or assignee',
                'parameters': {
                    'project_id': {'type': 'integer', 'required': False, 'description': 'Filter by project'},
                    'status': {'type': 'string', 'required': False, 'description': 'Filter by status'},
                    'assigned_to': {'type': 'string', 'required': False, 'description': 'Filter by assignee'},
                    'include_subtasks': {'type': 'boolean', 'required': False, 'description': 'Include subtasks', 'default': True},
                    'due_before': {'type': 'string', 'required': False, 'description': 'Filter tasks due before date'},
                    'limit': {'type': 'integer', 'required': False, 'description': 'Max results', 'default': 100}
                },
                'handler': self.task_list
            },
            {
                'name': 'task_get',
                'description': 'Get detailed information about a specific task including subtasks',
                'parameters': {
                    'task_id': {'type': 'integer', 'required': True, 'description': 'Task ID'}
                },
                'handler': self.task_get
            },
            {
                'name': 'task_delete',
                'description': 'Delete a task and its subtasks',
                'parameters': {
                    'task_id': {'type': 'integer', 'required': True, 'description': 'Task ID to delete'}
                },
                'handler': self.task_delete
            },
            {
                'name': 'task_complete',
                'description': 'Mark a task as completed with optional completion notes',
                'parameters': {
                    'task_id': {'type': 'integer', 'required': True, 'description': 'Task ID'},
                    'completion_notes': {'type': 'string', 'required': False, 'description': 'Notes about completion'}
                },
                'handler': self.task_complete
            },

            # ========== MILESTONE TOOLS ==========
            {
                'name': 'milestone_create',
                'description': 'Create a project milestone to track major goals',
                'parameters': {
                    'project_id': {'type': 'integer', 'required': True, 'description': 'Project ID'},
                    'title': {'type': 'string', 'required': True, 'description': 'Milestone title'},
                    'description': {'type': 'string', 'required': False, 'description': 'Milestone description'},
                    'due_date': {'type': 'string', 'required': False, 'description': 'Target date (YYYY-MM-DD)'}
                },
                'handler': self.milestone_create
            },
            {
                'name': 'milestone_update',
                'description': 'Update milestone progress, status, or details',
                'parameters': {
                    'milestone_id': {'type': 'integer', 'required': True, 'description': 'Milestone ID'},
                    'title': {'type': 'string', 'required': False, 'description': 'New title'},
                    'description': {'type': 'string', 'required': False, 'description': 'New description'},
                    'status': {'type': 'string', 'required': False, 'description': 'Status: pending, in_progress, completed'},
                    'progress': {'type': 'integer', 'required': False, 'description': 'Progress percentage 0-100'},
                    'due_date': {'type': 'string', 'required': False, 'description': 'New due date'}
                },
                'handler': self.milestone_update
            },
            {
                'name': 'milestone_list',
                'description': 'List milestones for a project or all milestones',
                'parameters': {
                    'project_id': {'type': 'integer', 'required': False, 'description': 'Filter by project'},
                    'status': {'type': 'string', 'required': False, 'description': 'Filter by status'}
                },
                'handler': self.milestone_list
            },
            {
                'name': 'milestone_delete',
                'description': 'Delete a milestone',
                'parameters': {
                    'milestone_id': {'type': 'integer', 'required': True, 'description': 'Milestone ID'}
                },
                'handler': self.milestone_delete
            },

            # ========== NOTE TOOLS ==========
            {
                'name': 'note_create',
                'description': 'Create a quick note. Notes can be associated with projects or conversations.',
                'parameters': {
                    'content': {'type': 'string', 'required': True, 'description': 'Note content'},
                    'title': {'type': 'string', 'required': False, 'description': 'Note title'},
                    'note_type': {'type': 'string', 'required': False, 'description': f'Type: {", ".join(self.note_types)}', 'default': 'general'},
                    'project_id': {'type': 'integer', 'required': False, 'description': 'Associated project'},
                    'conversation_id': {'type': 'integer', 'required': False, 'description': 'Associated conversation'},
                    'is_pinned': {'type': 'boolean', 'required': False, 'description': 'Pin this note', 'default': False},
                    'tags': {'type': 'array', 'required': False, 'description': 'Note tags'}
                },
                'handler': self.note_create
            },
            {
                'name': 'note_update',
                'description': 'Update an existing note',
                'parameters': {
                    'note_id': {'type': 'integer', 'required': True, 'description': 'Note ID'},
                    'content': {'type': 'string', 'required': False, 'description': 'New content'},
                    'title': {'type': 'string', 'required': False, 'description': 'New title'},
                    'is_pinned': {'type': 'boolean', 'required': False, 'description': 'Pin status'},
                    'tags': {'type': 'array', 'required': False, 'description': 'New tags'}
                },
                'handler': self.note_update
            },
            {
                'name': 'note_search',
                'description': 'Search notes by content, type, or tags',
                'parameters': {
                    'query': {'type': 'string', 'required': False, 'description': 'Search query'},
                    'note_type': {'type': 'string', 'required': False, 'description': 'Filter by type'},
                    'project_id': {'type': 'integer', 'required': False, 'description': 'Filter by project'},
                    'tags': {'type': 'array', 'required': False, 'description': 'Filter by tags'},
                    'pinned_only': {'type': 'boolean', 'required': False, 'description': 'Only pinned notes', 'default': False},
                    'limit': {'type': 'integer', 'required': False, 'description': 'Max results', 'default': 50}
                },
                'handler': self.note_search
            },
            {
                'name': 'note_delete',
                'description': 'Delete a note',
                'parameters': {
                    'note_id': {'type': 'integer', 'required': True, 'description': 'Note ID'}
                },
                'handler': self.note_delete
            },

            # ========== SUMMARY TOOLS ==========
            {
                'name': 'summary_create',
                'description': 'Create a summary for any source (conversation, project, memory collection)',
                'parameters': {
                    'source_type': {'type': 'string', 'required': True, 'description': 'Source type: conversation, project, memory_collection'},
                    'source_id': {'type': 'integer', 'required': True, 'description': 'Source ID'},
                    'title': {'type': 'string', 'required': False, 'description': 'Summary title'},
                    'summary': {'type': 'string', 'required': True, 'description': 'The summary text'},
                    'key_points': {'type': 'array', 'required': False, 'description': 'Key points'},
                    'action_items': {'type': 'array', 'required': False, 'description': 'Action items'},
                    'entities_mentioned': {'type': 'array', 'required': False, 'description': 'Entities mentioned'},
                    'sentiment': {'type': 'string', 'required': False, 'description': 'Overall sentiment'}
                },
                'handler': self.summary_create
            },
            {
                'name': 'summary_get',
                'description': 'Get summaries for a source',
                'parameters': {
                    'source_type': {'type': 'string', 'required': True, 'description': 'Source type'},
                    'source_id': {'type': 'integer', 'required': True, 'description': 'Source ID'}
                },
                'handler': self.summary_get
            },
            {
                'name': 'summary_search',
                'description': 'Search across all summaries',
                'parameters': {
                    'query': {'type': 'string', 'required': False, 'description': 'Search query'},
                    'source_type': {'type': 'string', 'required': False, 'description': 'Filter by source type'},
                    'limit': {'type': 'integer', 'required': False, 'description': 'Max results', 'default': 20}
                },
                'handler': self.summary_search
            },

            # ========== TRIGGER TOOLS ==========
            {
                'name': 'trigger_create',
                'description': 'Create a server-side trigger that executes actions based on events or conditions',
                'parameters': {
                    'name': {'type': 'string', 'required': True, 'description': 'Trigger name'},
                    'description': {'type': 'string', 'required': False, 'description': 'Trigger description'},
                    'trigger_type': {'type': 'string', 'required': True, 'description': f'Type: {", ".join(self.trigger_types)}'},
                    'event_source': {'type': 'string', 'required': False, 'description': 'Event source (conversation, memory, project, etc.)'},
                    'event_pattern': {'type': 'string', 'required': False, 'description': 'Pattern to match (regex or keyword)'},
                    'action_type': {'type': 'string', 'required': True, 'description': f'Action: {", ".join(self.action_types)}'},
                    'action_config': {'type': 'object', 'required': True, 'description': 'Action configuration'},
                    'conditions': {'type': 'object', 'required': False, 'description': 'Additional conditions'}
                },
                'handler': self.trigger_create
            },
            {
                'name': 'trigger_update',
                'description': 'Update a trigger configuration or enable/disable it',
                'parameters': {
                    'trigger_id': {'type': 'integer', 'required': True, 'description': 'Trigger ID'},
                    'name': {'type': 'string', 'required': False, 'description': 'New name'},
                    'is_active': {'type': 'boolean', 'required': False, 'description': 'Active status'},
                    'event_pattern': {'type': 'string', 'required': False, 'description': 'New pattern'},
                    'action_config': {'type': 'object', 'required': False, 'description': 'New action config'},
                    'conditions': {'type': 'object', 'required': False, 'description': 'New conditions'}
                },
                'handler': self.trigger_update
            },
            {
                'name': 'trigger_list',
                'description': 'List all triggers with optional filtering',
                'parameters': {
                    'trigger_type': {'type': 'string', 'required': False, 'description': 'Filter by type'},
                    'is_active': {'type': 'boolean', 'required': False, 'description': 'Filter by active status'},
                    'event_source': {'type': 'string', 'required': False, 'description': 'Filter by event source'}
                },
                'handler': self.trigger_list
            },
            {
                'name': 'trigger_delete',
                'description': 'Delete a trigger',
                'parameters': {
                    'trigger_id': {'type': 'integer', 'required': True, 'description': 'Trigger ID'}
                },
                'handler': self.trigger_delete
            },
            {
                'name': 'trigger_execute',
                'description': 'Manually execute a trigger for testing',
                'parameters': {
                    'trigger_id': {'type': 'integer', 'required': True, 'description': 'Trigger ID'},
                    'test_data': {'type': 'object', 'required': False, 'description': 'Test event data'}
                },
                'handler': self.trigger_execute
            },
            {
                'name': 'trigger_get_logs',
                'description': 'Get execution logs for a trigger',
                'parameters': {
                    'trigger_id': {'type': 'integer', 'required': True, 'description': 'Trigger ID'},
                    'limit': {'type': 'integer', 'required': False, 'description': 'Max logs', 'default': 50}
                },
                'handler': self.trigger_get_logs
            },

            # ========== INSTRUCTION EXTRACTION TOOLS ==========
            {
                'name': 'instruction_extract_from_text',
                'description': 'Extract potential instructions from text (conversation, message, or any content)',
                'parameters': {
                    'text': {'type': 'string', 'required': True, 'description': 'Text to analyze'},
                    'auto_create': {'type': 'boolean', 'required': False, 'description': 'Automatically create instructions', 'default': False},
                    'min_confidence': {'type': 'number', 'required': False, 'description': 'Minimum confidence threshold', 'default': 0.7}
                },
                'handler': self.instruction_extract_from_text
            },
            {
                'name': 'instruction_suggest_from_conversation',
                'description': 'Analyze a conversation and suggest instructions to create',
                'parameters': {
                    'session_id': {'type': 'string', 'required': True, 'description': 'Conversation session ID'}
                },
                'handler': self.instruction_suggest_from_conversation
            },

            # ========== PROJECT EXTENSION TOOLS ==========
            {
                'name': 'project_create_from_description',
                'description': 'Create a full project with tasks and milestones from a description',
                'parameters': {
                    'name': {'type': 'string', 'required': True, 'description': 'Project name'},
                    'description': {'type': 'string', 'required': True, 'description': 'Full project description'},
                    'goals': {'type': 'array', 'required': False, 'description': 'Project goals'},
                    'auto_create_tasks': {'type': 'boolean', 'required': False, 'description': 'Auto-create initial tasks', 'default': True},
                    'auto_create_milestones': {'type': 'boolean', 'required': False, 'description': 'Auto-create milestones', 'default': True},
                    'priority': {'type': 'integer', 'required': False, 'description': 'Project priority', 'default': 5},
                    'tags': {'type': 'array', 'required': False, 'description': 'Project tags'}
                },
                'handler': self.project_create_from_description
            },
            {
                'name': 'project_get_overview',
                'description': 'Get a complete project overview with tasks, milestones, and progress',
                'parameters': {
                    'project_id': {'type': 'integer', 'required': True, 'description': 'Project ID'}
                },
                'handler': self.project_get_overview
            },
            {
                'name': 'project_add_from_instruction',
                'description': 'Create a project based on stored instruction',
                'parameters': {
                    'instruction_id': {'type': 'integer', 'required': True, 'description': 'Instruction ID to base project on'},
                    'name': {'type': 'string', 'required': False, 'description': 'Project name (defaults to instruction title)'}
                },
                'handler': self.project_add_from_instruction
            },

            # ========== CONTEXT TOOLS ==========
            {
                'name': 'context_get_relevant',
                'description': 'Get all relevant context for a topic (memories, notes, instructions, recent conversations)',
                'parameters': {
                    'topic': {'type': 'string', 'required': True, 'description': 'Topic to find context for'},
                    'include_memories': {'type': 'boolean', 'required': False, 'description': 'Include memories', 'default': True},
                    'include_notes': {'type': 'boolean', 'required': False, 'description': 'Include notes', 'default': True},
                    'include_instructions': {'type': 'boolean', 'required': False, 'description': 'Include instructions', 'default': True},
                    'include_conversations': {'type': 'boolean', 'required': False, 'description': 'Include recent conversations', 'default': True},
                    'limit_per_type': {'type': 'integer', 'required': False, 'description': 'Max items per type', 'default': 10}
                },
                'handler': self.context_get_relevant
            },
            {
                'name': 'context_save_session',
                'description': 'Save the current session context for later retrieval',
                'parameters': {
                    'session_name': {'type': 'string', 'required': True, 'description': 'Name for this context'},
                    'context_data': {'type': 'object', 'required': True, 'description': 'Context data to save'},
                    'tags': {'type': 'array', 'required': False, 'description': 'Tags for finding this context'}
                },
                'handler': self.context_save_session
            },
            {
                'name': 'context_restore_session',
                'description': 'Restore a previously saved session context',
                'parameters': {
                    'session_name': {'type': 'string', 'required': True, 'description': 'Context name to restore'}
                },
                'handler': self.context_restore_session
            },

            # ========== FILE MANAGEMENT TOOLS ==========
            {
                'name': 'file_store',
                'description': 'Store a file reference with metadata in the system',
                'parameters': {
                    'file_path': {'type': 'string', 'required': True, 'description': 'Path to the file'},
                    'title': {'type': 'string', 'required': False, 'description': 'Display title'},
                    'description': {'type': 'string', 'required': False, 'description': 'File description'},
                    'project_id': {'type': 'integer', 'required': False, 'description': 'Associated project'},
                    'tags': {'type': 'array', 'required': False, 'description': 'File tags'}
                },
                'handler': self.file_store
            },
            {
                'name': 'file_search',
                'description': 'Search stored file references',
                'parameters': {
                    'query': {'type': 'string', 'required': False, 'description': 'Search query'},
                    'project_id': {'type': 'integer', 'required': False, 'description': 'Filter by project'},
                    'tags': {'type': 'array', 'required': False, 'description': 'Filter by tags'},
                    'limit': {'type': 'integer', 'required': False, 'description': 'Max results', 'default': 50}
                },
                'handler': self.file_search
            },

            # ========== BATCH OPERATIONS ==========
            {
                'name': 'batch_create_tasks',
                'description': 'Create multiple tasks at once for a project',
                'parameters': {
                    'project_id': {'type': 'integer', 'required': True, 'description': 'Project ID'},
                    'tasks': {'type': 'array', 'required': True, 'description': 'Array of task objects with title, description, priority, due_date'}
                },
                'handler': self.batch_create_tasks
            },
            {
                'name': 'batch_create_notes',
                'description': 'Create multiple notes at once',
                'parameters': {
                    'notes': {'type': 'array', 'required': True, 'description': 'Array of note objects with content, title, note_type, tags'}
                },
                'handler': self.batch_create_notes
            }
        ]

    # ========== CONVERSATION LOGGING IMPLEMENTATIONS ==========

    def conversation_log(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Log a conversation exchange"""
        session_id = params.get('session_id') or f"session_{uuid.uuid4().hex[:16]}"
        title = params.get('title')
        user_message = params.get('user_message')
        assistant_response = params.get('assistant_response')
        tool_calls = params.get('tool_calls', [])
        client_name = params.get('client_name', 'unknown')
        extract_instructions = params.get('extract_instructions', True)

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get or create conversation
            cur.execute("SELECT id, message_count FROM conversations WHERE session_id = %s", (session_id,))
            conversation = cur.fetchone()

            if not conversation:
                cur.execute("""
                    INSERT INTO conversations (session_id, title, client_name, is_auto_logged, message_count)
                    VALUES (%s, %s, %s, true, 0)
                    RETURNING id
                """, (session_id, title or f"Conversation {session_id[:8]}", client_name))
                conversation = {'id': cur.fetchone()['id'], 'message_count': 0}

            conv_id = conversation['id']

            # Add user message
            cur.execute("""
                INSERT INTO messages (conversation_id, role, content)
                VALUES (%s, 'user', %s)
                RETURNING id
            """, (conv_id, user_message))
            user_msg_id = cur.fetchone()['id']

            # Add assistant message
            cur.execute("""
                INSERT INTO messages (conversation_id, role, content, tool_calls)
                VALUES (%s, 'assistant', %s, %s)
                RETURNING id
            """, (conv_id, assistant_response, json.dumps(tool_calls) if tool_calls else None))
            assistant_msg_id = cur.fetchone()['id']

            # Update conversation message count
            cur.execute("""
                UPDATE conversations SET message_count = message_count + 2 WHERE id = %s
            """, (conv_id,))

            conn.commit()

            # Extract instructions if enabled
            extracted_count = 0
            if extract_instructions:
                extracted = self._extract_instructions_from_exchange(user_message, assistant_response)
                if extracted:
                    for instr in extracted:
                        cur.execute("""
                            INSERT INTO instructions (title, content, category, scope, created_by, metadata)
                            VALUES (%s, %s, %s, 'session', 'auto_extraction', %s)
                        """, (instr['title'], instr['content'], instr.get('category', 'extracted'),
                              json.dumps({'source_conversation': conv_id, 'confidence': instr.get('confidence', 0.8)})))
                        extracted_count += 1

                    cur.execute("""
                        UPDATE conversations SET extracted_instructions = extracted_instructions + %s WHERE id = %s
                    """, (extracted_count, conv_id))
                    conn.commit()

            cur.close()
            conn.close()

            return {
                'success': True,
                'session_id': session_id,
                'conversation_id': conv_id,
                'messages_added': 2,
                'instructions_extracted': extracted_count,
                'message': f'Conversation logged successfully'
            }

        except Exception as e:
            logger.error(f"Error logging conversation: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _extract_instructions_from_exchange(self, user_msg: str, assistant_msg: str) -> List[Dict[str, Any]]:
        """Extract potential instructions from a conversation exchange"""
        instructions = []
        combined = f"{user_msg}\n{assistant_msg}"

        # Pattern matching for instruction-like content
        patterns = [
            (r'(?:immer|always)\s+(.+?)(?:\.|$)', 'behavior'),
            (r'(?:niemals|never)\s+(.+?)(?:\.|$)', 'restriction'),
            (r'(?:when|wenn)\s+(.+?),?\s+(?:then|dann)\s+(.+?)(?:\.|$)', 'conditional'),
            (r'(?:remember|merke)\s+(?:that|dir)?\s*(.+?)(?:\.|$)', 'memory'),
            (r'(?:preference|präferenz):\s*(.+?)(?:\.|$)', 'preference'),
        ]

        for pattern, category in patterns:
            matches = re.findall(pattern, combined, re.IGNORECASE)
            for match in matches:
                content = match if isinstance(match, str) else ' -> '.join(match)
                if len(content) > 10:  # Filter too short matches
                    instructions.append({
                        'title': f"Extracted: {content[:50]}...",
                        'content': content,
                        'category': category,
                        'confidence': 0.7
                    })

        return instructions[:3]  # Limit to 3 per exchange

    def conversation_get_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get conversation history"""
        session_id = params.get('session_id')
        query = params.get('query')
        user_id = params.get('user_id')
        from_date = params.get('from_date')
        to_date = params.get('to_date')
        limit = params.get('limit', 50)

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            if session_id:
                # Get specific conversation
                cur.execute("""
                    SELECT c.*, array_agg(
                        json_build_object('id', m.id, 'role', m.role, 'content', m.content, 'created_at', m.created_at)
                        ORDER BY m.created_at
                    ) as messages
                    FROM conversations c
                    LEFT JOIN messages m ON c.id = m.conversation_id
                    WHERE c.session_id = %s
                    GROUP BY c.id
                """, (session_id,))
                conversation = cur.fetchone()

                if not conversation:
                    return {'success': False, 'error': 'Conversation not found'}

                conv_dict = dict(conversation)
                for key in ['created_at', 'updated_at']:
                    if conv_dict.get(key):
                        conv_dict[key] = conv_dict[key].isoformat()

                return {'success': True, 'conversation': conv_dict}

            # Search conversations
            conditions = []
            values = []

            if query:
                conditions.append("""
                    c.id IN (SELECT DISTINCT conversation_id FROM messages WHERE content ILIKE %s)
                """)
                values.append(f'%{query}%')

            if user_id:
                conditions.append("c.user_id = %s")
                values.append(user_id)

            if from_date:
                conditions.append("c.created_at >= %s")
                values.append(from_date)

            if to_date:
                conditions.append("c.created_at <= %s")
                values.append(to_date)

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            values.append(limit)

            cur.execute(f"""
                SELECT c.id, c.session_id, c.title, c.message_count, c.topics, c.sentiment,
                       c.created_at, c.client_name
                FROM conversations c
                WHERE {where_clause}
                ORDER BY c.updated_at DESC
                LIMIT %s
            """, values)

            conversations = [dict(row) for row in cur.fetchall()]
            for c in conversations:
                if c.get('created_at'):
                    c['created_at'] = c['created_at'].isoformat()

            cur.close()
            conn.close()

            return {
                'success': True,
                'conversations': conversations,
                'count': len(conversations)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def conversation_summarize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate and store conversation summary"""
        session_id = params.get('session_id')
        title = params.get('title')
        key_points = params.get('key_points', [])
        action_items = params.get('action_items', [])
        summary_text = params.get('summary_text')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get conversation ID
            cur.execute("SELECT id FROM conversations WHERE session_id = %s", (session_id,))
            conv = cur.fetchone()
            if not conv:
                return {'success': False, 'error': 'Conversation not found'}

            # Create summary
            cur.execute("""
                INSERT INTO summaries (source_type, source_id, title, summary, key_points, action_items)
                VALUES ('conversation', %s, %s, %s, %s, %s)
                RETURNING id
            """, (conv['id'], title or f"Summary for {session_id[:8]}", summary_text, key_points, action_items))

            summary_id = cur.fetchone()['id']

            # Update conversation summary field
            cur.execute("""
                UPDATE conversations SET summary = %s WHERE id = %s
            """, (summary_text[:500], conv['id']))

            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'summary_id': summary_id,
                'conversation_id': conv['id'],
                'message': 'Summary created successfully'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def conversation_extract_topics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Store extracted topics for a conversation"""
        session_id = params.get('session_id')
        topics = params.get('topics', [])

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                UPDATE conversations SET topics = %s WHERE session_id = %s
            """, (topics, session_id))

            updated = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            if updated == 0:
                return {'success': False, 'error': 'Conversation not found'}

            return {
                'success': True,
                'session_id': session_id,
                'topics': topics,
                'message': f'{len(topics)} topics stored'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== TASK IMPLEMENTATIONS ==========

    def task_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task"""
        project_id = params.get('project_id')
        title = params.get('title')
        description = params.get('description')
        priority = params.get('priority', 5)
        due_date = params.get('due_date')
        assigned_to = params.get('assigned_to')
        parent_task_id = params.get('parent_task_id')
        tags = params.get('tags', [])

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                INSERT INTO tasks (project_id, title, description, priority, due_date, assigned_to,
                                  parent_task_id, tags, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'ai')
                RETURNING id, title, status, priority
            """, (project_id, title, description, priority, due_date, assigned_to, parent_task_id, tags))

            task = dict(cur.fetchone())
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'task_id': task['id'],
                'title': task['title'],
                'status': task['status'],
                'message': f'Task "{title}" created'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def task_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a task"""
        task_id = params.get('task_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            updates = []
            values = []

            for field in ['title', 'description', 'status', 'priority', 'due_date', 'assigned_to']:
                if params.get(field) is not None:
                    updates.append(f"{field} = %s")
                    values.append(params[field])

            # Handle completion
            if params.get('status') == 'completed':
                updates.append("completed_at = CURRENT_TIMESTAMP")

            if not updates:
                return {'success': False, 'error': 'No updates provided'}

            values.append(task_id)
            cur.execute(f"""
                UPDATE tasks SET {', '.join(updates)} WHERE id = %s
            """, values)

            updated = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            if updated == 0:
                return {'success': False, 'error': f'Task {task_id} not found'}

            return {'success': True, 'message': f'Task {task_id} updated'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def task_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List tasks with filters"""
        project_id = params.get('project_id')
        status = params.get('status')
        assigned_to = params.get('assigned_to')
        include_subtasks = params.get('include_subtasks', True)
        due_before = params.get('due_before')
        limit = params.get('limit', 100)

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            conditions = []
            values = []

            if project_id:
                conditions.append("project_id = %s")
                values.append(project_id)

            if status:
                conditions.append("status = %s")
                values.append(status)

            if assigned_to:
                conditions.append("assigned_to = %s")
                values.append(assigned_to)

            if not include_subtasks:
                conditions.append("parent_task_id IS NULL")

            if due_before:
                conditions.append("due_date <= %s")
                values.append(due_before)

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            values.append(limit)

            cur.execute(f"""
                SELECT t.*, p.name as project_name
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE {where_clause}
                ORDER BY t.priority DESC, t.due_date ASC NULLS LAST
                LIMIT %s
            """, values)

            tasks = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            for t in tasks:
                for key in ['due_date', 'completed_at', 'created_at', 'updated_at']:
                    if t.get(key):
                        t[key] = t[key].isoformat()

            return {
                'success': True,
                'tasks': tasks,
                'count': len(tasks)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def task_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get task details with subtasks"""
        task_id = params.get('task_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT t.*, p.name as project_name
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE t.id = %s
            """, (task_id,))

            task = cur.fetchone()
            if not task:
                return {'success': False, 'error': f'Task {task_id} not found'}

            task = dict(task)

            # Get subtasks
            cur.execute("""
                SELECT * FROM tasks WHERE parent_task_id = %s ORDER BY priority DESC
            """, (task_id,))
            subtasks = [dict(row) for row in cur.fetchall()]

            cur.close()
            conn.close()

            for key in ['due_date', 'completed_at', 'created_at', 'updated_at']:
                if task.get(key):
                    task[key] = task[key].isoformat()

            for st in subtasks:
                for key in ['due_date', 'completed_at', 'created_at', 'updated_at']:
                    if st.get(key):
                        st[key] = st[key].isoformat()

            return {
                'success': True,
                'task': task,
                'subtasks': subtasks,
                'subtask_count': len(subtasks)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def task_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a task"""
        task_id = params.get('task_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("DELETE FROM tasks WHERE id = %s OR parent_task_id = %s", (task_id, task_id))
            deleted = cur.rowcount

            conn.commit()
            cur.close()
            conn.close()

            if deleted == 0:
                return {'success': False, 'error': f'Task {task_id} not found'}

            return {'success': True, 'message': f'Deleted task and {deleted-1} subtasks'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def task_complete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mark task as completed"""
        task_id = params.get('task_id')
        completion_notes = params.get('completion_notes')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            metadata_update = ""
            values = [task_id]

            if completion_notes:
                metadata_update = ", metadata = metadata || %s"
                values.insert(0, json.dumps({'completion_notes': completion_notes}))

            cur.execute(f"""
                UPDATE tasks
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP {metadata_update}
                WHERE id = %s
            """, values)

            updated = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            if updated == 0:
                return {'success': False, 'error': f'Task {task_id} not found'}

            return {'success': True, 'message': f'Task {task_id} marked as completed'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== MILESTONE IMPLEMENTATIONS ==========

    def milestone_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a milestone"""
        project_id = params.get('project_id')
        title = params.get('title')
        description = params.get('description')
        due_date = params.get('due_date')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                INSERT INTO milestones (project_id, title, description, due_date, created_by)
                VALUES (%s, %s, %s, %s, 'ai')
                RETURNING id, title, status
            """, (project_id, title, description, due_date))

            milestone = dict(cur.fetchone())
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'milestone_id': milestone['id'],
                'title': milestone['title'],
                'message': f'Milestone "{title}" created'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def milestone_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a milestone"""
        milestone_id = params.get('milestone_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            updates = []
            values = []

            for field in ['title', 'description', 'status', 'progress', 'due_date']:
                if params.get(field) is not None:
                    updates.append(f"{field} = %s")
                    values.append(params[field])

            if params.get('status') == 'completed':
                updates.append("completed_at = CURRENT_TIMESTAMP")

            if not updates:
                return {'success': False, 'error': 'No updates provided'}

            values.append(milestone_id)
            cur.execute(f"""
                UPDATE milestones SET {', '.join(updates)} WHERE id = %s
            """, values)

            updated = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            if updated == 0:
                return {'success': False, 'error': f'Milestone {milestone_id} not found'}

            return {'success': True, 'message': f'Milestone {milestone_id} updated'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def milestone_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List milestones"""
        project_id = params.get('project_id')
        status = params.get('status')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            conditions = []
            values = []

            if project_id:
                conditions.append("project_id = %s")
                values.append(project_id)

            if status:
                conditions.append("status = %s")
                values.append(status)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            cur.execute(f"""
                SELECT m.*, p.name as project_name
                FROM milestones m
                LEFT JOIN projects p ON m.project_id = p.id
                WHERE {where_clause}
                ORDER BY m.due_date ASC NULLS LAST
            """, values)

            milestones = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            for m in milestones:
                for key in ['due_date', 'completed_at', 'created_at', 'updated_at']:
                    if m.get(key):
                        m[key] = m[key].isoformat()

            return {
                'success': True,
                'milestones': milestones,
                'count': len(milestones)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def milestone_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a milestone"""
        milestone_id = params.get('milestone_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("DELETE FROM milestones WHERE id = %s", (milestone_id,))
            deleted = cur.rowcount

            conn.commit()
            cur.close()
            conn.close()

            if deleted == 0:
                return {'success': False, 'error': f'Milestone {milestone_id} not found'}

            return {'success': True, 'message': f'Milestone {milestone_id} deleted'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== NOTE IMPLEMENTATIONS ==========

    def note_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a note"""
        content = params.get('content')
        title = params.get('title')
        note_type = params.get('note_type', 'general')
        project_id = params.get('project_id')
        conversation_id = params.get('conversation_id')
        is_pinned = params.get('is_pinned', False)
        tags = params.get('tags', [])

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                INSERT INTO notes (content, title, note_type, project_id, conversation_id, is_pinned, tags, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'ai')
                RETURNING id, title, note_type
            """, (content, title, note_type, project_id, conversation_id, is_pinned, tags))

            note = dict(cur.fetchone())
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'note_id': note['id'],
                'title': note['title'],
                'note_type': note['note_type'],
                'message': 'Note created successfully'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def note_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a note"""
        note_id = params.get('note_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            updates = []
            values = []

            for field in ['content', 'title', 'is_pinned', 'tags']:
                if params.get(field) is not None:
                    updates.append(f"{field} = %s")
                    values.append(params[field])

            if not updates:
                return {'success': False, 'error': 'No updates provided'}

            values.append(note_id)
            cur.execute(f"""
                UPDATE notes SET {', '.join(updates)} WHERE id = %s
            """, values)

            updated = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            if updated == 0:
                return {'success': False, 'error': f'Note {note_id} not found'}

            return {'success': True, 'message': f'Note {note_id} updated'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def note_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search notes"""
        query = params.get('query')
        note_type = params.get('note_type')
        project_id = params.get('project_id')
        tags = params.get('tags', [])
        pinned_only = params.get('pinned_only', False)
        limit = params.get('limit', 50)

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            conditions = []
            values = []

            if query:
                conditions.append("(content ILIKE %s OR title ILIKE %s)")
                values.extend([f'%{query}%', f'%{query}%'])

            if note_type:
                conditions.append("note_type = %s")
                values.append(note_type)

            if project_id:
                conditions.append("project_id = %s")
                values.append(project_id)

            if tags:
                conditions.append("tags && %s")
                values.append(tags)

            if pinned_only:
                conditions.append("is_pinned = true")

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            values.append(limit)

            cur.execute(f"""
                SELECT * FROM notes
                WHERE {where_clause}
                ORDER BY is_pinned DESC, created_at DESC
                LIMIT %s
            """, values)

            notes = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            for n in notes:
                for key in ['created_at', 'updated_at']:
                    if n.get(key):
                        n[key] = n[key].isoformat()

            return {
                'success': True,
                'notes': notes,
                'count': len(notes)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def note_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a note"""
        note_id = params.get('note_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("DELETE FROM notes WHERE id = %s", (note_id,))
            deleted = cur.rowcount

            conn.commit()
            cur.close()
            conn.close()

            if deleted == 0:
                return {'success': False, 'error': f'Note {note_id} not found'}

            return {'success': True, 'message': f'Note {note_id} deleted'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== SUMMARY IMPLEMENTATIONS ==========

    def summary_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary"""
        source_type = params.get('source_type')
        source_id = params.get('source_id')
        title = params.get('title')
        summary = params.get('summary')
        key_points = params.get('key_points', [])
        action_items = params.get('action_items', [])
        entities_mentioned = params.get('entities_mentioned', [])
        sentiment = params.get('sentiment')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                INSERT INTO summaries (source_type, source_id, title, summary, key_points,
                                      action_items, entities_mentioned, sentiment)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (source_type, source_id, title, summary, key_points,
                  action_items, entities_mentioned, sentiment))

            summary_id = cur.fetchone()['id']
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'summary_id': summary_id,
                'message': 'Summary created successfully'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def summary_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get summaries for a source"""
        source_type = params.get('source_type')
        source_id = params.get('source_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT * FROM summaries
                WHERE source_type = %s AND source_id = %s
                ORDER BY created_at DESC
            """, (source_type, source_id))

            summaries = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            for s in summaries:
                if s.get('created_at'):
                    s['created_at'] = s['created_at'].isoformat()

            return {
                'success': True,
                'summaries': summaries,
                'count': len(summaries)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def summary_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search summaries"""
        query = params.get('query')
        source_type = params.get('source_type')
        limit = params.get('limit', 20)

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            conditions = []
            values = []

            if query:
                conditions.append("(summary ILIKE %s OR title ILIKE %s)")
                values.extend([f'%{query}%', f'%{query}%'])

            if source_type:
                conditions.append("source_type = %s")
                values.append(source_type)

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            values.append(limit)

            cur.execute(f"""
                SELECT * FROM summaries
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s
            """, values)

            summaries = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            for s in summaries:
                if s.get('created_at'):
                    s['created_at'] = s['created_at'].isoformat()

            return {
                'success': True,
                'summaries': summaries,
                'count': len(summaries)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== TRIGGER IMPLEMENTATIONS ==========

    def trigger_create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a trigger"""
        name = params.get('name')
        description = params.get('description')
        trigger_type = params.get('trigger_type')
        event_source = params.get('event_source')
        event_pattern = params.get('event_pattern')
        action_type = params.get('action_type')
        action_config = params.get('action_config')
        conditions = params.get('conditions', {})

        if trigger_type not in self.trigger_types:
            return {'success': False, 'error': f'Invalid trigger_type. Must be one of: {", ".join(self.trigger_types)}'}

        if action_type not in self.action_types:
            return {'success': False, 'error': f'Invalid action_type. Must be one of: {", ".join(self.action_types)}'}

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                INSERT INTO triggers (name, description, trigger_type, event_source, event_pattern,
                                     action_type, action_config, conditions, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'ai')
                RETURNING id, name, trigger_type, is_active
            """, (name, description, trigger_type, event_source, event_pattern,
                  action_type, json.dumps(action_config), json.dumps(conditions)))

            trigger = dict(cur.fetchone())
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'trigger_id': trigger['id'],
                'name': trigger['name'],
                'trigger_type': trigger['trigger_type'],
                'is_active': trigger['is_active'],
                'message': f'Trigger "{name}" created'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def trigger_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update a trigger"""
        trigger_id = params.get('trigger_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            updates = []
            values = []

            for field in ['name', 'is_active', 'event_pattern']:
                if params.get(field) is not None:
                    updates.append(f"{field} = %s")
                    values.append(params[field])

            if params.get('action_config') is not None:
                updates.append("action_config = %s")
                values.append(json.dumps(params['action_config']))

            if params.get('conditions') is not None:
                updates.append("conditions = %s")
                values.append(json.dumps(params['conditions']))

            if not updates:
                return {'success': False, 'error': 'No updates provided'}

            values.append(trigger_id)
            cur.execute(f"""
                UPDATE triggers SET {', '.join(updates)} WHERE id = %s
            """, values)

            updated = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()

            if updated == 0:
                return {'success': False, 'error': f'Trigger {trigger_id} not found'}

            return {'success': True, 'message': f'Trigger {trigger_id} updated'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def trigger_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List triggers"""
        trigger_type = params.get('trigger_type')
        is_active = params.get('is_active')
        event_source = params.get('event_source')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            conditions = []
            values = []

            if trigger_type:
                conditions.append("trigger_type = %s")
                values.append(trigger_type)

            if is_active is not None:
                conditions.append("is_active = %s")
                values.append(is_active)

            if event_source:
                conditions.append("event_source = %s")
                values.append(event_source)

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            cur.execute(f"""
                SELECT id, name, description, trigger_type, event_source, event_pattern,
                       action_type, is_active, last_triggered_at, trigger_count, created_at
                FROM triggers
                WHERE {where_clause}
                ORDER BY created_at DESC
            """, values)

            triggers = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            for t in triggers:
                for key in ['last_triggered_at', 'created_at']:
                    if t.get(key):
                        t[key] = t[key].isoformat()

            return {
                'success': True,
                'triggers': triggers,
                'count': len(triggers)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def trigger_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a trigger"""
        trigger_id = params.get('trigger_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("DELETE FROM triggers WHERE id = %s", (trigger_id,))
            deleted = cur.rowcount

            conn.commit()
            cur.close()
            conn.close()

            if deleted == 0:
                return {'success': False, 'error': f'Trigger {trigger_id} not found'}

            return {'success': True, 'message': f'Trigger {trigger_id} deleted'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def trigger_execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manually execute a trigger"""
        trigger_id = params.get('trigger_id')
        test_data = params.get('test_data', {})

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get trigger
            cur.execute("SELECT * FROM triggers WHERE id = %s", (trigger_id,))
            trigger = cur.fetchone()

            if not trigger:
                return {'success': False, 'error': f'Trigger {trigger_id} not found'}

            trigger = dict(trigger)
            action_result = {'executed': True, 'action_type': trigger['action_type']}

            # Log execution
            cur.execute("""
                INSERT INTO trigger_logs (trigger_id, event_data, action_result, success)
                VALUES (%s, %s, %s, true)
                RETURNING id
            """, (trigger_id, json.dumps(test_data), json.dumps(action_result)))

            log_id = cur.fetchone()['id']

            # Update trigger stats
            cur.execute("""
                UPDATE triggers SET last_triggered_at = CURRENT_TIMESTAMP, trigger_count = trigger_count + 1
                WHERE id = %s
            """, (trigger_id,))

            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'trigger_id': trigger_id,
                'log_id': log_id,
                'action_result': action_result,
                'message': f'Trigger executed successfully'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def trigger_get_logs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get trigger execution logs"""
        trigger_id = params.get('trigger_id')
        limit = params.get('limit', 50)

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT * FROM trigger_logs
                WHERE trigger_id = %s
                ORDER BY triggered_at DESC
                LIMIT %s
            """, (trigger_id, limit))

            logs = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            for log in logs:
                if log.get('triggered_at'):
                    log['triggered_at'] = log['triggered_at'].isoformat()

            return {
                'success': True,
                'logs': logs,
                'count': len(logs)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== INSTRUCTION EXTRACTION IMPLEMENTATIONS ==========

    def instruction_extract_from_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract instructions from text"""
        text = params.get('text')
        auto_create = params.get('auto_create', False)
        min_confidence = params.get('min_confidence', 0.7)

        extracted = []
        patterns = [
            (r'(?:always|immer)\s+(.+?)(?:\.|$)', 'behavior', 0.8),
            (r'(?:never|niemals)\s+(.+?)(?:\.|$)', 'restriction', 0.85),
            (r'(?:prefer|bevorzuge)\s+(.+?)(?:\.|$)', 'preference', 0.75),
            (r'(?:remember|merke)(?:\s+(?:that|dir))?\s+(.+?)(?:\.|$)', 'memory', 0.7),
            (r'(?:rule|regel):\s*(.+?)(?:\.|$)', 'rule', 0.9),
            (r'(?:when|wenn)\s+(.+?),?\s+(?:then|dann)\s+(.+?)(?:\.|$)', 'conditional', 0.8),
        ]

        for pattern, category, confidence in patterns:
            if confidence < min_confidence:
                continue
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                content = match if isinstance(match, str) else ' -> '.join(match)
                if len(content) > 10:
                    extracted.append({
                        'content': content,
                        'category': category,
                        'confidence': confidence
                    })

        created_ids = []
        if auto_create and extracted:
            try:
                conn = get_db_connection()
                cur = conn.cursor(cursor_factory=RealDictCursor)

                for instr in extracted:
                    cur.execute("""
                        INSERT INTO instructions (title, content, category, scope, created_by, metadata)
                        VALUES (%s, %s, %s, 'global', 'auto_extraction', %s)
                        RETURNING id
                    """, (f"Extracted: {instr['content'][:50]}", instr['content'], instr['category'],
                          json.dumps({'confidence': instr['confidence']})))
                    created_ids.append(cur.fetchone()['id'])

                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                logger.error(f"Error creating extracted instructions: {str(e)}")

        return {
            'success': True,
            'extracted': extracted,
            'count': len(extracted),
            'created_ids': created_ids,
            'auto_created': len(created_ids)
        }

    def instruction_suggest_from_conversation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest instructions from a conversation"""
        session_id = params.get('session_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get conversation messages
            cur.execute("""
                SELECT c.id, array_agg(m.content ORDER BY m.created_at) as messages
                FROM conversations c
                JOIN messages m ON c.id = m.conversation_id
                WHERE c.session_id = %s
                GROUP BY c.id
            """, (session_id,))

            conv = cur.fetchone()
            if not conv:
                return {'success': False, 'error': 'Conversation not found'}

            cur.close()
            conn.close()

            # Analyze all messages
            all_text = ' '.join(conv['messages'])
            result = self.instruction_extract_from_text({
                'text': all_text,
                'auto_create': False,
                'min_confidence': 0.6
            })

            return {
                'success': True,
                'session_id': session_id,
                'suggestions': result['extracted'],
                'count': result['count']
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== PROJECT EXTENSION IMPLEMENTATIONS ==========

    def project_create_from_description(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a project from description"""
        name = params.get('name')
        description = params.get('description')
        goals = params.get('goals', [])
        auto_create_tasks = params.get('auto_create_tasks', True)
        auto_create_milestones = params.get('auto_create_milestones', True)
        priority = params.get('priority', 5)
        tags = params.get('tags', [])

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Create project
            cur.execute("""
                INSERT INTO projects (name, description, priority, tags, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (name, description, priority, tags, json.dumps({'goals': goals})))

            project_id = cur.fetchone()['id']

            tasks_created = 0
            milestones_created = 0

            # Auto-create milestones from goals
            if auto_create_milestones and goals:
                for i, goal in enumerate(goals):
                    cur.execute("""
                        INSERT INTO milestones (project_id, title, description, created_by)
                        VALUES (%s, %s, %s, 'ai')
                    """, (project_id, goal, f"Milestone for: {goal}"))
                    milestones_created += 1

            # Auto-create initial tasks from description
            if auto_create_tasks:
                task_patterns = [
                    r'(?:implement|implementiere)\s+(.+?)(?:\.|,|$)',
                    r'(?:create|erstelle)\s+(.+?)(?:\.|,|$)',
                    r'(?:add|füge)\s+(.+?)(?:\.|,|$)',
                    r'(?:build|baue)\s+(.+?)(?:\.|,|$)',
                ]

                for pattern in task_patterns:
                    matches = re.findall(pattern, description, re.IGNORECASE)
                    for match in matches[:3]:  # Limit to 3 per pattern
                        cur.execute("""
                            INSERT INTO tasks (project_id, title, status, created_by)
                            VALUES (%s, %s, 'pending', 'ai')
                        """, (project_id, match.strip()[:200]))
                        tasks_created += 1

            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'project_id': project_id,
                'name': name,
                'tasks_created': tasks_created,
                'milestones_created': milestones_created,
                'message': f'Project "{name}" created with {tasks_created} tasks and {milestones_created} milestones'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def project_get_overview(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get complete project overview"""
        project_id = params.get('project_id')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get project
            cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            project = cur.fetchone()
            if not project:
                return {'success': False, 'error': f'Project {project_id} not found'}

            project = dict(project)

            # Get tasks
            cur.execute("""
                SELECT * FROM tasks WHERE project_id = %s ORDER BY priority DESC
            """, (project_id,))
            tasks = [dict(row) for row in cur.fetchall()]

            # Get milestones
            cur.execute("""
                SELECT * FROM milestones WHERE project_id = %s ORDER BY due_date ASC NULLS LAST
            """, (project_id,))
            milestones = [dict(row) for row in cur.fetchall()]

            # Get artifacts
            cur.execute("""
                SELECT id, title, artifact_type, version FROM artifacts
                WHERE project_id = %s AND parent_id IS NULL
            """, (project_id,))
            artifacts = [dict(row) for row in cur.fetchall()]

            # Get notes
            cur.execute("""
                SELECT id, title, content, note_type FROM notes WHERE project_id = %s
            """, (project_id,))
            notes = [dict(row) for row in cur.fetchall()]

            cur.close()
            conn.close()

            # Calculate progress
            completed_tasks = len([t for t in tasks if t['status'] == 'completed'])
            total_tasks = len(tasks)
            progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            # Format dates
            for key in ['created_at', 'updated_at']:
                if project.get(key):
                    project[key] = project[key].isoformat()

            for t in tasks:
                for key in ['due_date', 'completed_at', 'created_at', 'updated_at']:
                    if t.get(key):
                        t[key] = t[key].isoformat()

            for m in milestones:
                for key in ['due_date', 'completed_at', 'created_at', 'updated_at']:
                    if m.get(key):
                        m[key] = m[key].isoformat()

            return {
                'success': True,
                'project': project,
                'tasks': tasks,
                'milestones': milestones,
                'artifacts': artifacts,
                'notes': notes,
                'stats': {
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'progress_percentage': round(progress, 1),
                    'total_milestones': len(milestones),
                    'total_artifacts': len(artifacts),
                    'total_notes': len(notes)
                }
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def project_add_from_instruction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create project from instruction"""
        instruction_id = params.get('instruction_id')
        name = params.get('name')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Get instruction
            cur.execute("SELECT * FROM instructions WHERE id = %s", (instruction_id,))
            instruction = cur.fetchone()
            if not instruction:
                return {'success': False, 'error': f'Instruction {instruction_id} not found'}

            instruction = dict(instruction)
            project_name = name or instruction['title']

            # Create project
            cur.execute("""
                INSERT INTO projects (name, description, priority, metadata)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (project_name, instruction['content'], instruction.get('priority', 5),
                  json.dumps({'source_instruction': instruction_id})))

            project_id = cur.fetchone()['id']
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'project_id': project_id,
                'name': project_name,
                'source_instruction_id': instruction_id,
                'message': f'Project "{project_name}" created from instruction'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== CONTEXT IMPLEMENTATIONS ==========

    def context_get_relevant(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all relevant context for a topic"""
        topic = params.get('topic')
        include_memories = params.get('include_memories', True)
        include_notes = params.get('include_notes', True)
        include_instructions = params.get('include_instructions', True)
        include_conversations = params.get('include_conversations', True)
        limit_per_type = params.get('limit_per_type', 10)

        context = {}

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            if include_memories:
                cur.execute("""
                    SELECT id, content, memory_type, importance, tags
                    FROM memories WHERE content ILIKE %s
                    ORDER BY importance DESC LIMIT %s
                """, (f'%{topic}%', limit_per_type))
                context['memories'] = [dict(row) for row in cur.fetchall()]

            if include_notes:
                cur.execute("""
                    SELECT id, title, content, note_type
                    FROM notes WHERE content ILIKE %s OR title ILIKE %s
                    ORDER BY created_at DESC LIMIT %s
                """, (f'%{topic}%', f'%{topic}%', limit_per_type))
                context['notes'] = [dict(row) for row in cur.fetchall()]

            if include_instructions:
                cur.execute("""
                    SELECT id, title, content, category, priority
                    FROM instructions WHERE is_active = true AND (content ILIKE %s OR title ILIKE %s)
                    ORDER BY priority DESC LIMIT %s
                """, (f'%{topic}%', f'%{topic}%', limit_per_type))
                context['instructions'] = [dict(row) for row in cur.fetchall()]

            if include_conversations:
                cur.execute("""
                    SELECT DISTINCT c.id, c.session_id, c.title, c.summary
                    FROM conversations c
                    JOIN messages m ON c.id = m.conversation_id
                    WHERE m.content ILIKE %s
                    ORDER BY c.updated_at DESC LIMIT %s
                """, (f'%{topic}%', limit_per_type))
                context['conversations'] = [dict(row) for row in cur.fetchall()]

            cur.close()
            conn.close()

            total_items = sum(len(v) for v in context.values())

            return {
                'success': True,
                'topic': topic,
                'context': context,
                'total_items': total_items
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def context_save_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Save session context"""
        session_name = params.get('session_name')
        context_data = params.get('context_data')
        tags = params.get('tags', [])

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Store as a special memory
            cur.execute("""
                INSERT INTO memories (content, memory_type, importance, tags, metadata, created_by)
                VALUES (%s, 'context', 10, %s, %s, 'ai')
                ON CONFLICT DO NOTHING
                RETURNING id
            """, (json.dumps({'name': session_name, 'data': context_data}),
                  tags + ['session_context'], json.dumps({'session_name': session_name})))

            result = cur.fetchone()
            conn.commit()
            cur.close()
            conn.close()

            if result:
                return {
                    'success': True,
                    'memory_id': result['id'],
                    'session_name': session_name,
                    'message': f'Session context "{session_name}" saved'
                }
            else:
                return {'success': False, 'error': 'Failed to save context'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def context_restore_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Restore session context"""
        session_name = params.get('session_name')

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            cur.execute("""
                SELECT content, metadata FROM memories
                WHERE memory_type = 'context' AND metadata->>'session_name' = %s
                ORDER BY created_at DESC LIMIT 1
            """, (session_name,))

            result = cur.fetchone()
            cur.close()
            conn.close()

            if not result:
                return {'success': False, 'error': f'Session context "{session_name}" not found'}

            context_content = json.loads(result['content'])

            return {
                'success': True,
                'session_name': session_name,
                'context_data': context_content.get('data', {}),
                'message': f'Session context "{session_name}" restored'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== FILE MANAGEMENT IMPLEMENTATIONS ==========

    def file_store(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Store a file reference"""
        file_path = params.get('file_path')
        title = params.get('title')
        description = params.get('description')
        project_id = params.get('project_id')
        tags = params.get('tags', [])

        # Determine file type
        ext = os.path.splitext(file_path)[1].lower()
        file_type = 'code' if ext in ['.py', '.js', '.ts', '.go', '.rs', '.java'] else 'document'

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            # Store as artifact
            cur.execute("""
                INSERT INTO artifacts (title, content, artifact_type, file_extension, project_id, tags,
                                      metadata, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'ai')
                RETURNING id
            """, (title or os.path.basename(file_path), description or '', file_type, ext,
                  project_id, tags, json.dumps({'file_path': file_path})))

            artifact_id = cur.fetchone()['id']
            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'artifact_id': artifact_id,
                'file_path': file_path,
                'message': f'File reference stored'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def file_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search stored file references"""
        query = params.get('query')
        project_id = params.get('project_id')
        tags = params.get('tags', [])
        limit = params.get('limit', 50)

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            conditions = ["metadata->>'file_path' IS NOT NULL"]
            values = []

            if query:
                conditions.append("(title ILIKE %s OR metadata->>'file_path' ILIKE %s)")
                values.extend([f'%{query}%', f'%{query}%'])

            if project_id:
                conditions.append("project_id = %s")
                values.append(project_id)

            if tags:
                conditions.append("tags && %s")
                values.append(tags)

            where_clause = " AND ".join(conditions)
            values.append(limit)

            cur.execute(f"""
                SELECT id, title, artifact_type, file_extension, tags, metadata
                FROM artifacts
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s
            """, values)

            files = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.close()

            return {
                'success': True,
                'files': files,
                'count': len(files)
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== BATCH OPERATIONS ==========

    def batch_create_tasks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create multiple tasks at once"""
        project_id = params.get('project_id')
        tasks = params.get('tasks', [])

        if not tasks:
            return {'success': False, 'error': 'No tasks provided'}

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            created_ids = []
            for task in tasks:
                cur.execute("""
                    INSERT INTO tasks (project_id, title, description, priority, due_date, tags, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, 'ai')
                    RETURNING id
                """, (project_id, task.get('title'), task.get('description'),
                      task.get('priority', 5), task.get('due_date'), task.get('tags', [])))
                created_ids.append(cur.fetchone()['id'])

            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'task_ids': created_ids,
                'count': len(created_ids),
                'message': f'{len(created_ids)} tasks created'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def batch_create_notes(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create multiple notes at once"""
        notes = params.get('notes', [])

        if not notes:
            return {'success': False, 'error': 'No notes provided'}

        try:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=RealDictCursor)

            created_ids = []
            for note in notes:
                cur.execute("""
                    INSERT INTO notes (content, title, note_type, tags, created_by)
                    VALUES (%s, %s, %s, %s, 'ai')
                    RETURNING id
                """, (note.get('content'), note.get('title'),
                      note.get('note_type', 'general'), note.get('tags', [])))
                created_ids.append(cur.fetchone()['id'])

            conn.commit()
            cur.close()
            conn.close()

            return {
                'success': True,
                'note_ids': created_ids,
                'count': len(created_ids),
                'message': f'{len(created_ids)} notes created'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}
