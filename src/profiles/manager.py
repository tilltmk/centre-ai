"""
User Profile Manager
Manages user profiles, preferences, and personal information
"""

import os
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class ProfileManager:
    """Manages user profiles in PostgreSQL"""

    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'postgres'),
            'database': os.getenv('POSTGRES_DB', 'centre_ai'),
            'user': os.getenv('POSTGRES_USER', 'centre_ai'),
            'password': os.getenv('POSTGRES_PASSWORD', 'centre_ai_password')
        }

    def _get_connection(self):
        """Get database connection"""
        return psycopg.connect(**self.db_config, row_factory=dict_row)

    def create_or_update_profile(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        bio: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create or update user profile"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO user_profiles (user_id, full_name, email, bio, preferences, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    full_name = COALESCE(EXCLUDED.full_name, user_profiles.full_name),
                    email = COALESCE(EXCLUDED.email, user_profiles.email),
                    bio = COALESCE(EXCLUDED.bio, user_profiles.bio),
                    preferences = COALESCE(EXCLUDED.preferences, user_profiles.preferences),
                    metadata = COALESCE(EXCLUDED.metadata, user_profiles.metadata),
                    updated_at = CURRENT_TIMESTAMP
                RETURNING *
            """, (user_id, full_name, email, bio, Jsonb(preferences or {}), Jsonb(metadata or {})))

            result = cursor.fetchone()
            conn.commit()
            cursor.close()
            conn.close()

            return {
                'success': True,
                'profile': dict(result)
            }

        except Exception as e:
            logger.error(f"Error creating/updating profile: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result:
                return {
                    'success': True,
                    'profile': dict(result)
                }
            else:
                return {
                    'success': False,
                    'error': 'Profile not found'
                }

        except Exception as e:
            logger.error(f"Error getting profile: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user preferences"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE user_profiles
                SET preferences = preferences || %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s
                RETURNING *
            """, (Jsonb(preferences), user_id))

            result = cursor.fetchone()
            conn.commit()
            cursor.close()
            conn.close()

            if result:
                return {
                    'success': True,
                    'profile': dict(result)
                }
            else:
                return {
                    'success': False,
                    'error': 'Profile not found'
                }

        except Exception as e:
            logger.error(f"Error updating preferences: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_profile(self, user_id: str) -> Dict[str, Any]:
        """Delete user profile"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM user_profiles WHERE user_id = %s", (user_id,))
            deleted = cursor.rowcount > 0

            conn.commit()
            cursor.close()
            conn.close()

            return {
                'success': deleted,
                'message': 'Profile deleted' if deleted else 'Profile not found'
            }

        except Exception as e:
            logger.error(f"Error deleting profile: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class ConversationManager:
    """Manages conversations and messages"""

    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'postgres'),
            'database': os.getenv('POSTGRES_DB', 'centre_ai'),
            'user': os.getenv('POSTGRES_USER', 'centre_ai'),
            'password': os.getenv('POSTGRES_PASSWORD', 'centre_ai_password')
        }

    def _get_connection(self):
        """Get database connection"""
        return psycopg.connect(**self.db_config, row_factory=dict_row)

    def create_conversation(
        self,
        user_id: str,
        session_id: str,
        title: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new conversation"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO conversations (user_id, session_id, title, context)
                VALUES (%s, %s, %s, %s)
                RETURNING *
            """, (user_id, session_id, title, Jsonb(context or {})))

            result = cursor.fetchone()
            conn.commit()
            cursor.close()
            conn.close()

            return {
                'success': True,
                'conversation': dict(result)
            }

        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add message to conversation"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Get conversation ID
            cursor.execute("SELECT id FROM conversations WHERE session_id = %s", (session_id,))
            conv_result = cursor.fetchone()

            if not conv_result:
                cursor.close()
                conn.close()
                return {
                    'success': False,
                    'error': 'Conversation not found'
                }

            conversation_id = conv_result['id']

            # Insert message
            cursor.execute("""
                INSERT INTO messages (conversation_id, role, content, metadata)
                VALUES (%s, %s, %s, %s)
                RETURNING *
            """, (conversation_id, role, content, Jsonb(metadata or {})))

            result = cursor.fetchone()
            conn.commit()
            cursor.close()
            conn.close()

            return {
                'success': True,
                'message': dict(result)
            }

        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get conversation history"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT m.* FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.session_id = %s
                ORDER BY m.created_at ASC
                LIMIT %s
            """, (session_id, limit))

            messages = [dict(row) for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            return {
                'success': True,
                'messages': messages,
                'count': len(messages)
            }

        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_user_conversations(
        self,
        user_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get user's conversations"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM conversations
                WHERE user_id = %s
                ORDER BY updated_at DESC
                LIMIT %s
            """, (user_id, limit))

            conversations = [dict(row) for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            return {
                'success': True,
                'conversations': conversations,
                'count': len(conversations)
            }

        except Exception as e:
            logger.error(f"Error getting user conversations: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class MemoryManager:
    """Manages long-term memories"""

    def __init__(self):
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'postgres'),
            'database': os.getenv('POSTGRES_DB', 'centre_ai'),
            'user': os.getenv('POSTGRES_USER', 'centre_ai'),
            'password': os.getenv('POSTGRES_PASSWORD', 'centre_ai_password')
        }

    def _get_connection(self):
        """Get database connection"""
        return psycopg.connect(**self.db_config, row_factory=dict_row)

    def store_memory(
        self,
        user_id: str,
        memory_type: str,
        content: str,
        importance: int = 5,
        tags: List[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store a memory"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO memories (user_id, memory_type, content, importance, tags, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING *
            """, (user_id, memory_type, content, importance, tags or [], Jsonb(metadata or {})))

            result = cursor.fetchone()
            conn.commit()
            cursor.close()
            conn.close()

            return {
                'success': True,
                'memory': dict(result)
            }

        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_memories(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get memories"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = "SELECT * FROM memories WHERE user_id = %s"
            params = [user_id]

            if memory_type:
                query += " AND memory_type = %s"
                params.append(memory_type)

            if tags:
                query += " AND tags && %s"
                params.append(tags)

            query += " ORDER BY importance DESC, created_at DESC LIMIT %s"
            params.append(limit)

            cursor.execute(query, params)
            memories = [dict(row) for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            return {
                'success': True,
                'memories': memories,
                'count': len(memories)
            }

        except Exception as e:
            logger.error(f"Error getting memories: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """Delete a memory"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM memories WHERE id = %s", (memory_id,))
            deleted = cursor.rowcount > 0

            conn.commit()
            cursor.close()
            conn.close()

            return {
                'success': deleted,
                'message': 'Memory deleted' if deleted else 'Memory not found'
            }

        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
