"""
Memory Store Implementation
Persistent storage for MCP server context and data
"""

import json
import sqlite3
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MemoryStore:
    """Persistent memory store using SQLite"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv('MEMORY_DB_PATH', 'mcp_data/memory.db')

        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create memories table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                user TEXT NOT NULL,
                tags TEXT,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                accessed_at TEXT
            )
        ''')

        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_key ON memories(key)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_user ON memories(user)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tags ON memories(tags)
        ''')

        conn.commit()
        conn.close()
        logger.info(f"Memory store initialized at {self.db_path}")

    def store(self, key: str, value: Any, user: str, tags: List[str] = None, ttl: int = None) -> Dict[str, Any]:
        """Store data in memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Serialize value
        value_json = json.dumps(value)
        tags_json = json.dumps(tags or [])

        created_at = datetime.utcnow().isoformat()
        expires_at = None
        if ttl:
            expires_at = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()

        # Check if key already exists
        cursor.execute('SELECT id FROM memories WHERE key = ? AND user = ?', (key, user))
        existing = cursor.fetchone()

        if existing:
            # Update existing
            cursor.execute('''
                UPDATE memories
                SET value = ?, tags = ?, created_at = ?, expires_at = ?
                WHERE key = ? AND user = ?
            ''', (value_json, tags_json, created_at, expires_at, key, user))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO memories (key, value, user, tags, created_at, expires_at, accessed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (key, value_json, user, tags_json, created_at, expires_at, created_at))

        conn.commit()
        conn.close()

        logger.debug(f"Stored memory: {key} for user {user}")

        return {
            'success': True,
            'key': key,
            'stored_at': created_at
        }

    def retrieve(self, key: str, user: str) -> Dict[str, Any]:
        """Retrieve data from memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT value, tags, created_at, expires_at
            FROM memories
            WHERE key = ? AND user = ?
        ''', (key, user))

        row = cursor.fetchone()

        if not row:
            conn.close()
            return {'success': False, 'error': 'Key not found'}

        value_json, tags_json, created_at, expires_at = row

        # Check expiration
        if expires_at:
            if datetime.fromisoformat(expires_at) < datetime.utcnow():
                self.delete(key, user)
                conn.close()
                return {'success': False, 'error': 'Key expired'}

        # Update accessed_at
        cursor.execute('''
            UPDATE memories
            SET accessed_at = ?
            WHERE key = ? AND user = ?
        ''', (datetime.utcnow().isoformat(), key, user))

        conn.commit()
        conn.close()

        return {
            'success': True,
            'key': key,
            'value': json.loads(value_json),
            'tags': json.loads(tags_json),
            'created_at': created_at
        }

    def delete(self, key: str, user: str) -> Dict[str, Any]:
        """Delete data from memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM memories WHERE key = ? AND user = ?', (key, user))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return {
            'success': deleted,
            'key': key
        }

    def search_by_tags(self, tags: List[str], user: str) -> Dict[str, Any]:
        """Search memories by tags"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT key, value, tags FROM memories WHERE user = ?', (user,))
        rows = cursor.fetchall()
        conn.close()

        results = []
        for key, value_json, tags_json in rows:
            memory_tags = json.loads(tags_json)
            if any(tag in memory_tags for tag in tags):
                results.append({
                    'key': key,
                    'value': json.loads(value_json),
                    'tags': memory_tags
                })

        return {
            'success': True,
            'count': len(results),
            'results': results
        }

    def list_all(self, user: str, limit: int = 100) -> Dict[str, Any]:
        """List all memories for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT key, tags, created_at, accessed_at
            FROM memories
            WHERE user = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user, limit))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for key, tags_json, created_at, accessed_at in rows:
            results.append({
                'key': key,
                'tags': json.loads(tags_json),
                'created_at': created_at,
                'accessed_at': accessed_at
            })

        return {
            'success': True,
            'count': len(results),
            'results': results
        }

    def count(self) -> int:
        """Get total count of memories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM memories')
        count = cursor.fetchone()[0]

        conn.close()
        return count

    def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM memories')
        total_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT user) FROM memories')
        unique_users = cursor.fetchone()[0]

        conn.close()

        return {
            'total_memories': total_count,
            'unique_users': unique_users,
            'db_path': self.db_path
        }

    def cleanup_expired(self) -> int:
        """Clean up expired memories"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.utcnow().isoformat()
        cursor.execute('DELETE FROM memories WHERE expires_at IS NOT NULL AND expires_at < ?', (now,))
        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        logger.info(f"Cleaned up {deleted} expired memories")
        return deleted
