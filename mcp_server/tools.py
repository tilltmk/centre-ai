"""
MCP Tools implementation for Centre AI
All tools available to AI clients via MCP protocol
"""
import asyncio
import json
import os
import subprocess
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path
import hashlib
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from .database import db, vector_store, VectorStore
from .config import config


class MCPTools:
    """Collection of all MCP tools"""

    # CRITICAL: Response size limits to prevent context overflow
    MAX_RESPONSE_SIZE = 50000  # 50k characters max per response
    MAX_MEMORY_CONTENT_SIZE = 4000  # 4k characters for memory content

    @staticmethod
    def _limit_response_size(content: str, max_size: int = None) -> dict:
        """Truncate content if it exceeds size limits"""
        if max_size is None:
            max_size = MCPTools.MAX_RESPONSE_SIZE

        if len(content) <= max_size:
            return {"content": content, "truncated": False, "original_size": len(content)}

        truncated = content[:max_size] + f"\n\n[TRUNCATED - Original: {len(content)} chars, Showing: {max_size} chars]"
        return {"content": truncated, "truncated": True, "original_size": len(content)}

    # ==================== MEMORY TOOLS ====================

    @staticmethod
    async def create_memory(
        content: str,
        memory_type: str = "general",
        importance: int = 5,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a new memory entry in the knowledge base.

        Args:
            content: The memory content to store
            memory_type: Type of memory (general, fact, reminder, context, preference)
            importance: Importance level 1-10 (10 being most important)
            tags: List of tags for categorization
            metadata: Additional metadata dictionary

        Returns:
            Created memory with ID and confirmation
        """
        tags = tags or []
        metadata = metadata or {}

        # Generate embedding
        vector = vector_store.encode(content)
        embedding_id = vector_store.generate_id(content + str(datetime.now()))

        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO memories (content, memory_type, importance, tags, metadata, embedding_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, content, memory_type, importance, tags, created_at
            """, content, memory_type, importance, tags, json.dumps(metadata), embedding_id)

        # Store in vector database
        await vector_store.upsert(
            VectorStore.COLLECTION_MEMORIES,
            embedding_id,
            vector,
            {
                "id": row["id"],
                "content": content,
                "memory_type": memory_type,
                "importance": importance,
                "tags": tags
            }
        )

        return {
            "success": True,
            "memory": {
                "id": row["id"],
                "content": row["content"],
                "memory_type": row["memory_type"],
                "importance": row["importance"],
                "tags": row["tags"],
                "created_at": row["created_at"].isoformat()
            }
        }

    @staticmethod
    async def get_memory(
        query: Optional[str] = None,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10,
        semantic_search: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve memories from the knowledge base.

        Args:
            query: Search query (uses semantic search if enabled)
            memory_type: Filter by memory type
            tags: Filter by tags (any match)
            limit: Maximum number of results
            semantic_search: Use vector similarity search

        Returns:
            List of matching memories
        """
        results = []

        if query and semantic_search:
            # Use vector search
            filters = {}
            if memory_type:
                filters["memory_type"] = memory_type
            if tags:
                filters["tags"] = tags

            vector_results = await vector_store.search(
                VectorStore.COLLECTION_MEMORIES,
                query,
                limit=limit,
                filters=filters if filters else None
            )

            for vr in vector_results:
                results.append({
                    "id": vr["payload"].get("id"),
                    "content": vr["payload"].get("content"),
                    "memory_type": vr["payload"].get("memory_type"),
                    "importance": vr["payload"].get("importance"),
                    "tags": vr["payload"].get("tags", []),
                    "relevance_score": vr["score"]
                })
        else:
            # Use database search
            async with db.acquire() as conn:
                sql = "SELECT id, content, memory_type, importance, tags, created_at FROM memories WHERE 1=1"
                params = []
                param_idx = 1

                if memory_type:
                    sql += f" AND memory_type = ${param_idx}"
                    params.append(memory_type)
                    param_idx += 1

                if tags:
                    sql += f" AND tags && ${param_idx}"
                    params.append(tags)
                    param_idx += 1

                if query:
                    sql += f" AND content ILIKE ${param_idx}"
                    params.append(f"%{query}%")
                    param_idx += 1

                sql += f" ORDER BY importance DESC, created_at DESC LIMIT ${param_idx}"
                params.append(limit)

                rows = await conn.fetch(sql, *params)

                for row in rows:
                    # CRITICAL: Limit memory content size in responses
                    limited_content = MCPTools._limit_response_size(row["content"], MCPTools.MAX_MEMORY_CONTENT_SIZE)
                    results.append({
                        "id": row["id"],
                        "content": limited_content["content"],
                        "content_truncated": limited_content["truncated"],
                        "memory_type": row["memory_type"],
                        "importance": row["importance"],
                        "tags": list(row["tags"]) if row["tags"] else [],
                        "created_at": row["created_at"].isoformat()
                    })

        return {
            "success": True,
            "count": len(results),
            "memories": results
        }

    # ==================== CODEBASE TOOLS ====================

    @staticmethod
    async def get_codebase(
        codebase_id: Optional[int] = None,
        name: Optional[str] = None,
        query: Optional[str] = None,
        language: Optional[str] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Retrieve codebase information and search code files.

        Args:
            codebase_id: Specific codebase ID to retrieve
            name: Search by codebase name
            query: Search code content (semantic)
            language: Filter by programming language
            limit: Maximum results

        Returns:
            Codebase information and matching code files
        """
        results = {"codebases": [], "code_files": []}

        async with db.acquire() as conn:
            # Get codebases
            if codebase_id:
                rows = await conn.fetch("""
                    SELECT id, name, description, repo_url, language, file_count, indexed_at
                    FROM codebases WHERE id = $1
                """, codebase_id)
            elif name:
                rows = await conn.fetch("""
                    SELECT id, name, description, repo_url, language, file_count, indexed_at
                    FROM codebases WHERE name ILIKE $1
                """, f"%{name}%")
            else:
                rows = await conn.fetch("""
                    SELECT id, name, description, repo_url, language, file_count, indexed_at
                    FROM codebases ORDER BY updated_at DESC LIMIT $1
                """, limit)

            for row in rows:
                results["codebases"].append({
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "repo_url": row["repo_url"],
                    "language": row["language"],
                    "file_count": row["file_count"],
                    "indexed_at": row["indexed_at"].isoformat() if row["indexed_at"] else None
                })

        # Search code files
        if query:
            filters = {}
            if language:
                filters["language"] = language
            if codebase_id:
                filters["codebase_id"] = codebase_id

            vector_results = await vector_store.search(
                VectorStore.COLLECTION_CODE,
                query,
                limit=limit,
                filters=filters if filters else None
            )

            for vr in vector_results:
                results["code_files"].append({
                    "file_path": vr["payload"].get("file_path"),
                    "language": vr["payload"].get("language"),
                    "content_preview": vr["payload"].get("content", "")[:500],
                    "codebase_id": vr["payload"].get("codebase_id"),
                    "relevance_score": vr["score"]
                })

        return {
            "success": True,
            "results": results
        }

    @staticmethod
    async def capture_codebase(
        name: str,
        path: str,
        description: Optional[str] = None,
        repo_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Index a codebase from a local path or git repository.

        Args:
            name: Name for the codebase
            path: Local path to the codebase
            description: Optional description
            repo_url: Git repository URL if applicable

        Returns:
            Indexing results and statistics
        """
        path = Path(path)
        if not path.exists():
            return {"success": False, "error": f"Path does not exist: {path}"}

        # Supported extensions
        extensions = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.jsx': 'javascript', '.tsx': 'typescript', '.java': 'java',
            '.go': 'go', '.rs': 'rust', '.c': 'c', '.cpp': 'cpp',
            '.h': 'c', '.hpp': 'cpp', '.rb': 'ruby', '.php': 'php',
            '.swift': 'swift', '.kt': 'kotlin', '.scala': 'scala',
            '.sh': 'bash', '.sql': 'sql', '.html': 'html', '.css': 'css',
            '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml', '.md': 'markdown',
            '.cs': 'csharp', '.r': 'r', '.scss': 'scss', '.xml': 'xml',
            '.rst': 'rst', '.tex': 'latex'
        }

        # Ignore patterns (like .gitignore)
        ignore_patterns = [
            '.git/',
            '__pycache__/',
            'node_modules/',
            'venv/',
            'env/',
            '.env/',
            'dist/',
            'build/',
            '.next/',
            '.cache/',
            'target/',
            'bin/',
            'obj/',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '*.so',
            '*.dll',
            '*.dylib',
            '*.exe',
            '*.o',
            '*.a',
            '*.class',
            '*.jar',
            '*.war',
            '*.ear',
            '*.min.js',
            '*.min.css',
            '*.map',
            'package-lock.json',
            'yarn.lock',
            '.DS_Store'
        ]

        ignore_spec = PathSpec.from_lines(GitWildMatchPattern, ignore_patterns)

        def chunk_code(content: str, chunk_size: int = 500) -> List[str]:
            """Split code into chunks for better indexing"""
            lines = content.split('\n')
            chunks = []
            current_chunk = []
            current_size = 0

            for line in lines:
                line_size = len(line) + 1
                if current_size + line_size > chunk_size and current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                current_chunk.append(line)
                current_size += line_size

            if current_chunk:
                chunks.append('\n'.join(current_chunk))

            return chunks

        # Create codebase entry
        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO codebases (name, description, repo_url, local_path)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, name, description, repo_url, str(path))
            codebase_id = row["id"]

        # Index files
        files_indexed = 0
        chunks_indexed = 0
        errors = []

        # Collect all files first to show total
        all_files = []
        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue
            if file_path.suffix not in extensions:
                continue

            try:
                relative_path = str(file_path.relative_to(path))
            except ValueError:
                continue

            if ignore_spec.match_file(relative_path):
                continue

            all_files.append((file_path, relative_path))

        total_files = len(all_files)
        print(f"[Codebase Indexing] Found {total_files} files to index")

        for idx, (file_path, relative_path) in enumerate(all_files, 1):
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')

                # Skip empty files
                if not content.strip():
                    continue

                # Skip very large files (>500KB)
                if len(content) > 500000:
                    errors.append(f"{relative_path}: File too large (>500KB)")
                    continue

                language = extensions[file_path.suffix]

                # Store complete file in database
                async with db.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO code_files (codebase_id, file_path, content, language, embedding_id)
                        VALUES ($1, $2, $3, $4, $5)
                    """, codebase_id, relative_path, content, language, f"{codebase_id}:{relative_path}")

                # Chunk the content for better vector search
                chunks = chunk_code(content)

                for i, chunk in enumerate(chunks):
                    # Generate embedding for chunk
                    vector = vector_store.encode(chunk)
                    embedding_id = vector_store.generate_id(f"{codebase_id}:{relative_path}:chunk{i}")

                    # Store chunk in vector database
                    await vector_store.upsert(
                        VectorStore.COLLECTION_CODE,
                        embedding_id,
                        vector,
                        {
                            "codebase_id": codebase_id,
                            "file_path": relative_path,
                            "language": language,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "content": chunk
                        }
                    )
                    chunks_indexed += 1

                files_indexed += 1

                # Progress logging every 10 files
                if files_indexed % 10 == 0:
                    print(f"[Codebase Indexing] Progress: {files_indexed}/{total_files} files ({chunks_indexed} chunks)")

            except Exception as e:
                errors.append(f"{relative_path}: {str(e)}")

        print(f"[Codebase Indexing] Completed: {files_indexed}/{total_files} files, {chunks_indexed} chunks")

        # Update codebase stats
        async with db.acquire() as conn:
            await conn.execute("""
                UPDATE codebases SET file_count = $1, indexed_at = CURRENT_TIMESTAMP
                WHERE id = $2
            """, files_indexed, codebase_id)

        return {
            "success": True,
            "codebase_id": codebase_id,
            "files_indexed": files_indexed,
            "chunks_indexed": chunks_indexed,
            "errors": errors[:10] if errors else []
        }

    # ==================== INSTRUCTIONS TOOLS ====================

    @staticmethod
    async def get_instructions(
        category: Optional[str] = None,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve general instructions and guidelines.

        Args:
            category: Filter by category
            active_only: Only return active instructions

        Returns:
            List of instructions
        """
        async with db.acquire() as conn:
            sql = "SELECT id, title, content, category, priority FROM instructions WHERE 1=1"
            params = []
            param_idx = 1

            if active_only:
                sql += " AND is_active = true"

            if category:
                sql += f" AND category = ${param_idx}"
                params.append(category)
                param_idx += 1

            sql += " ORDER BY priority DESC, created_at DESC"

            rows = await conn.fetch(sql, *params)

            instructions = []
            for row in rows:
                instructions.append({
                    "id": row["id"],
                    "title": row["title"],
                    "content": row["content"],
                    "category": row["category"],
                    "priority": row["priority"]
                })

        return {
            "success": True,
            "count": len(instructions),
            "instructions": instructions
        }

    # ==================== ADMIN/IDENTITY TOOLS ====================

    @staticmethod
    async def who_am_i_talking_to() -> Dict[str, Any]:
        """
        Get information about the MCP server administrators.

        Returns:
            List of admin profiles with public information
        """
        async with db.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, username, display_name, email, bio, avatar_url, metadata
                FROM admins ORDER BY id
            """)

            admins = []
            for row in rows:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                admins.append({
                    "username": row["username"],
                    "display_name": row["display_name"],
                    "email": row["email"],
                    "bio": row["bio"],
                    "avatar_url": row["avatar_url"],
                    "timezone": metadata.get("timezone"),
                    "languages": metadata.get("languages", []),
                    "expertise": metadata.get("expertise", [])
                })

        return {
            "success": True,
            "server_name": "Centre AI",
            "version": "2.0.0",
            "admins": admins
        }

    # ==================== PROJECT TOOLS ====================

    @staticmethod
    async def project_overview(
        project_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get overview of projects being managed.

        Args:
            project_id: Specific project ID
            status: Filter by status (active, completed, paused, archived)

        Returns:
            List of projects with details
        """
        async with db.acquire() as conn:
            sql = "SELECT id, name, description, status, priority, tags, metadata, created_at, updated_at FROM projects WHERE 1=1"
            params = []
            param_idx = 1

            if project_id:
                sql += f" AND id = ${param_idx}"
                params.append(project_id)
                param_idx += 1

            if status:
                sql += f" AND status = ${param_idx}"
                params.append(status)
                param_idx += 1

            sql += " ORDER BY priority DESC, updated_at DESC"

            rows = await conn.fetch(sql, *params)

            projects = []
            for row in rows:
                metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                projects.append({
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "status": row["status"],
                    "priority": row["priority"],
                    "tags": list(row["tags"]) if row["tags"] else [],
                    "milestones": metadata.get("milestones", []),
                    "team": metadata.get("team", []),
                    "created_at": row["created_at"].isoformat(),
                    "updated_at": row["updated_at"].isoformat()
                })

        return {
            "success": True,
            "count": len(projects),
            "projects": projects
        }

    # ==================== CONVERSATION TOOLS ====================

    @staticmethod
    async def conversation_overview(
        session_id: Optional[str] = None,
        limit: int = 20,
        include_messages: bool = False
    ) -> Dict[str, Any]:
        """
        Get overview of recorded conversations.

        Args:
            session_id: Specific conversation session ID
            limit: Maximum conversations to return
            include_messages: Include message history

        Returns:
            List of conversations with optional messages
        """
        async with db.acquire() as conn:
            if session_id:
                rows = await conn.fetch("""
                    SELECT id, session_id, title, summary, participants, message_count, created_at, updated_at
                    FROM conversations WHERE session_id = $1
                """, session_id)
            else:
                rows = await conn.fetch("""
                    SELECT id, session_id, title, summary, participants, message_count, created_at, updated_at
                    FROM conversations ORDER BY updated_at DESC LIMIT $1
                """, limit)

            conversations = []
            for row in rows:
                conv = {
                    "id": row["id"],
                    "session_id": row["session_id"],
                    "title": row["title"],
                    "summary": row["summary"],
                    "participants": list(row["participants"]) if row["participants"] else [],
                    "message_count": row["message_count"],
                    "created_at": row["created_at"].isoformat(),
                    "updated_at": row["updated_at"].isoformat()
                }

                if include_messages:
                    messages = await conn.fetch("""
                        SELECT role, content, created_at FROM messages
                        WHERE conversation_id = $1 ORDER BY created_at
                    """, row["id"])
                    conv["messages"] = [
                        {
                            "role": m["role"],
                            "content": m["content"],
                            "timestamp": m["created_at"].isoformat()
                        }
                        for m in messages
                    ]

                conversations.append(conv)

        return {
            "success": True,
            "count": len(conversations),
            "conversations": conversations
        }

    @staticmethod
    async def conversation_log(
        user_message: str,
        assistant_response: str,
        session_id: Optional[str] = None,
        title: Optional[str] = None,
        tool_calls: Optional[List[str]] = None,
        client_name: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Log a conversation or message exchange.

        Args:
            user_message: The user message
            assistant_response: The assistant response
            session_id: Session ID (auto-generated if not provided)
            title: Conversation title
            tool_calls: List of tools called during response
            client_name: Client application name

        Returns:
            Created conversation info with IDs
        """
        import uuid

        session_id = session_id or f"session_{uuid.uuid4().hex[:16]}"
        tool_calls = tool_calls or []

        async with db.acquire() as conn:
            # Get or create conversation
            row = await conn.fetchrow(
                "SELECT id, message_count FROM conversations WHERE session_id = $1",
                session_id
            )

            if not row:
                row = await conn.fetchrow("""
                    INSERT INTO conversations (session_id, title, client_name, is_auto_logged, message_count)
                    VALUES ($1, $2, $3, true, 0)
                    RETURNING id, message_count
                """, session_id, title or f"Conversation {session_id[:8]}", client_name)

            conv_id = row["id"]

            # Add user message
            await conn.execute("""
                INSERT INTO messages (conversation_id, role, content)
                VALUES ($1, 'user', $2)
            """, conv_id, user_message)

            # Add assistant message
            await conn.execute("""
                INSERT INTO messages (conversation_id, role, content, tool_calls)
                VALUES ($1, 'assistant', $2, $3)
            """, conv_id, assistant_response, json.dumps(tool_calls) if tool_calls else None)

            # Update conversation message count
            await conn.execute("""
                UPDATE conversations SET message_count = message_count + 2, updated_at = CURRENT_TIMESTAMP WHERE id = $1
            """, conv_id)

        return {
            "success": True,
            "session_id": session_id,
            "conversation_id": conv_id,
            "messages_added": 2,
            "message": "Conversation logged successfully"
        }

    # ==================== NOTE TOOLS ====================

    @staticmethod
    async def note_create(
        content: str,
        title: Optional[str] = None,
        note_type: str = "general",
        project_id: Optional[int] = None,
        is_pinned: bool = False,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a quick note.

        Args:
            content: Note content
            title: Note title
            note_type: Type of note
            project_id: Associated project ID
            is_pinned: Pin this note
            tags: Note tags

        Returns:
            Created note info
        """
        tags = tags or []

        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO notes (content, title, note_type, project_id, is_pinned, tags, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, 'ai')
                RETURNING id, title, note_type, created_at
            """, content, title, note_type, project_id, is_pinned, tags)

        return {
            "success": True,
            "note_id": row["id"],
            "title": row["title"],
            "note_type": row["note_type"],
            "created_at": row["created_at"].isoformat(),
            "message": "Note created successfully"
        }

    @staticmethod
    async def note_search(
        query: Optional[str] = None,
        note_type: Optional[str] = None,
        project_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        pinned_only: bool = False,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search notes.

        Args:
            query: Search query
            note_type: Filter by note type
            project_id: Filter by project
            tags: Filter by tags
            pinned_only: Only pinned notes
            limit: Maximum results

        Returns:
            List of matching notes
        """
        async with db.acquire() as conn:
            conditions = []
            params = []
            param_idx = 1

            if query:
                conditions.append(f"(content ILIKE ${param_idx} OR title ILIKE ${param_idx})")
                params.append(f"%{query}%")
                param_idx += 1

            if note_type:
                conditions.append(f"note_type = ${param_idx}")
                params.append(note_type)
                param_idx += 1

            if project_id:
                conditions.append(f"project_id = ${param_idx}")
                params.append(project_id)
                param_idx += 1

            if tags:
                conditions.append(f"tags && ${param_idx}")
                params.append(tags)
                param_idx += 1

            if pinned_only:
                conditions.append("is_pinned = true")

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            params.append(limit)

            rows = await conn.fetch(f"""
                SELECT id, content, title, note_type, project_id, is_pinned, tags, created_at
                FROM notes
                WHERE {where_clause}
                ORDER BY is_pinned DESC, created_at DESC
                LIMIT ${param_idx}
            """, *params)

            notes = []
            for row in rows:
                notes.append({
                    "id": row["id"],
                    "content": MCPTools._limit_response_size(row["content"], 1000)["content"],
                    "title": row["title"],
                    "note_type": row["note_type"],
                    "project_id": row["project_id"],
                    "is_pinned": row["is_pinned"],
                    "tags": list(row["tags"]) if row["tags"] else [],
                    "created_at": row["created_at"].isoformat()
                })

        return {
            "success": True,
            "count": len(notes),
            "notes": notes
        }

    # ==================== TASK TOOLS ====================

    @staticmethod
    async def task_create(
        project_id: int,
        title: str,
        description: Optional[str] = None,
        priority: int = 5,
        due_date: Optional[str] = None,
        assigned_to: Optional[str] = None,
        parent_task_id: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new task within a project.

        Args:
            project_id: Project ID for this task
            title: Task title
            description: Detailed task description
            priority: Priority 1-10
            due_date: Due date (YYYY-MM-DD)
            assigned_to: Assignee
            parent_task_id: Parent task ID for subtasks
            tags: Task tags

        Returns:
            Created task info
        """
        tags = tags or []

        async with db.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO tasks (project_id, title, description, priority, due_date, assigned_to, parent_task_id, tags, created_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'ai')
                RETURNING id, title, status, priority, created_at
            """, project_id, title, description, priority, due_date, assigned_to, parent_task_id, tags)

        return {
            "success": True,
            "task_id": row["id"],
            "title": row["title"],
            "status": row["status"],
            "priority": row["priority"],
            "created_at": row["created_at"].isoformat(),
            "message": f'Task "{title}" created'
        }

    @staticmethod
    async def task_list(
        project_id: Optional[int] = None,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        include_subtasks: bool = True,
        due_before: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        List tasks with filters.

        Args:
            project_id: Filter by project
            status: Filter by status
            assigned_to: Filter by assignee
            include_subtasks: Include subtasks
            due_before: Filter tasks due before date
            limit: Maximum results

        Returns:
            List of tasks
        """
        async with db.acquire() as conn:
            conditions = []
            params = []
            param_idx = 1

            if project_id:
                conditions.append(f"t.project_id = ${param_idx}")
                params.append(project_id)
                param_idx += 1

            if status:
                conditions.append(f"t.status = ${param_idx}")
                params.append(status)
                param_idx += 1

            if assigned_to:
                conditions.append(f"t.assigned_to = ${param_idx}")
                params.append(assigned_to)
                param_idx += 1

            if not include_subtasks:
                conditions.append("t.parent_task_id IS NULL")

            if due_before:
                conditions.append(f"t.due_date <= ${param_idx}")
                params.append(due_before)
                param_idx += 1

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            params.append(limit)

            rows = await conn.fetch(f"""
                SELECT t.id, t.title, t.description, t.status, t.priority, t.due_date,
                       t.assigned_to, t.parent_task_id, t.tags, t.created_at, p.name as project_name
                FROM tasks t
                LEFT JOIN projects p ON t.project_id = p.id
                WHERE {where_clause}
                ORDER BY t.priority DESC, t.due_date ASC NULLS LAST
                LIMIT ${param_idx}
            """, *params)

            tasks = []
            for row in rows:
                tasks.append({
                    "id": row["id"],
                    "title": row["title"],
                    "description": row["description"],
                    "status": row["status"],
                    "priority": row["priority"],
                    "due_date": row["due_date"].isoformat() if row["due_date"] else None,
                    "assigned_to": row["assigned_to"],
                    "parent_task_id": row["parent_task_id"],
                    "tags": list(row["tags"]) if row["tags"] else [],
                    "project_name": row["project_name"],
                    "created_at": row["created_at"].isoformat()
                })

        return {
            "success": True,
            "count": len(tasks),
            "tasks": tasks
        }

    @staticmethod
    async def task_update(
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
        due_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing task.

        Args:
            task_id: Task ID
            title: New title
            description: New description
            status: New status
            priority: New priority
            due_date: New due date

        Returns:
            Update confirmation
        """
        async with db.acquire() as conn:
            updates = []
            params = []
            param_idx = 1

            if title is not None:
                updates.append(f"title = ${param_idx}")
                params.append(title)
                param_idx += 1

            if description is not None:
                updates.append(f"description = ${param_idx}")
                params.append(description)
                param_idx += 1

            if status is not None:
                updates.append(f"status = ${param_idx}")
                params.append(status)
                param_idx += 1
                if status == "completed":
                    updates.append("completed_at = CURRENT_TIMESTAMP")

            if priority is not None:
                updates.append(f"priority = ${param_idx}")
                params.append(priority)
                param_idx += 1

            if due_date is not None:
                updates.append(f"due_date = ${param_idx}")
                params.append(due_date)
                param_idx += 1

            if not updates:
                return {"success": False, "error": "No updates provided"}

            params.append(task_id)
            result = await conn.execute(f"""
                UPDATE tasks SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ${param_idx}
            """, *params)

            if result == "UPDATE 0":
                return {"success": False, "error": f"Task {task_id} not found"}

        return {
            "success": True,
            "task_id": task_id,
            "message": f"Task {task_id} updated"
        }

    # ==================== WEB SEARCH TOOL ====================

    @staticmethod
    async def web_search(
        query: str,
        num_results: int = 5,
        search_engine: str = None
    ) -> Dict[str, Any]:
        """
        Search the web for information.

        Args:
            query: Search query
            num_results: Number of search results to return
            search_engine: Search engine to use (duckduckgo, searx, qwant, google)
                          If None, uses default from system settings

        Returns:
            List of search results with titles, URLs, and snippets
        """
        # Get default search engine from settings if not specified
        if search_engine is None:
            async with db.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT setting_value FROM system_settings
                    WHERE setting_key = 'search_engine'
                """)
                search_engine = row["setting_value"] if row else "duckduckgo"

        results = []

        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                if search_engine == "duckduckgo":
                    # DuckDuckGo HTML search
                    response = await client.get(
                        "https://html.duckduckgo.com/html/",
                        params={"q": query},
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    )

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')

                        for result in soup.select('.result')[:num_results]:
                            title_elem = result.select_one('.result__title')
                            snippet_elem = result.select_one('.result__snippet')
                            link_elem = result.select_one('.result__url')

                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                                url = link_elem.get_text(strip=True) if link_elem else ""

                                results.append({
                                    "title": title,
                                    "url": url,
                                    "snippet": snippet
                                })

                elif search_engine == "searx":
                    # Get SearX instance URL from settings
                    async with db.acquire() as conn:
                        row = await conn.fetchrow("""
                            SELECT setting_value FROM system_settings
                            WHERE setting_key = 'searx_instance_url'
                        """)
                        searx_url = row["setting_value"] if row else "https://searx.be"

                    # SearX JSON API
                    response = await client.get(
                        f"{searx_url}/search",
                        params={
                            "q": query,
                            "format": "json",
                            "pageno": 1
                        },
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    )

                    if response.status_code == 200:
                        data = response.json()
                        for result in data.get("results", [])[:num_results]:
                            results.append({
                                "title": result.get("title", ""),
                                "url": result.get("url", ""),
                                "snippet": result.get("content", "")
                            })

                elif search_engine == "qwant":
                    # Qwant API
                    response = await client.get(
                        "https://api.qwant.com/v3/search/web",
                        params={
                            "q": query,
                            "count": num_results,
                            "locale": "de_DE",
                            "device": "desktop"
                        },
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        items = data.get("data", {}).get("result", {}).get("items", [])

                        for item in items[:num_results]:
                            results.append({
                                "title": item.get("title", ""),
                                "url": item.get("url", ""),
                                "snippet": item.get("desc", "")
                            })

                elif search_engine == "startpage":
                    # Startpage search (HTML scraping)
                    response = await client.get(
                        "https://www.startpage.com/sp/search",
                        params={
                            "query": query,
                            "language": "deutsch",
                            "cat": "web"
                        },
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    )

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')

                        for result in soup.select('.w-gl__result')[:num_results]:
                            title_elem = result.select_one('.w-gl__result-title')
                            snippet_elem = result.select_one('.w-gl__description')
                            link_elem = result.select_one('.w-gl__result-url')

                            if title_elem:
                                title = title_elem.get_text(strip=True)
                                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                                url = link_elem.get_text(strip=True) if link_elem else ""

                                results.append({
                                    "title": title,
                                    "url": url,
                                    "snippet": snippet
                                })

                else:
                    return {
                        "success": False,
                        "error": f"Search engine '{search_engine}' not supported. Available: duckduckgo, searx, qwant, startpage"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Search failed: {str(e)}"
            }

        return {
            "success": True,
            "query": query,
            "engine": search_engine,
            "count": len(results),
            "results": results
        }

    # ==================== KNOWLEDGE VISUALIZATION ====================

    @staticmethod
    async def get_knowledge_graph(
        node_type: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get knowledge graph data for visualization.

        Args:
            node_type: Filter by node type
            limit: Maximum nodes to return

        Returns:
            Nodes and edges for graph visualization
        """
        async with db.acquire() as conn:
            # Get nodes
            if node_type:
                nodes = await conn.fetch("""
                    SELECT id, node_type, title, content, parent_id
                    FROM knowledge_nodes WHERE node_type = $1 LIMIT $2
                """, node_type, limit)
            else:
                nodes = await conn.fetch("""
                    SELECT id, node_type, title, content, parent_id
                    FROM knowledge_nodes LIMIT $1
                """, limit)

            node_ids = [n["id"] for n in nodes]

            # Get edges
            if node_ids:
                edges = await conn.fetch("""
                    SELECT id, source_id, target_id, relationship, weight
                    FROM knowledge_edges
                    WHERE source_id = ANY($1) OR target_id = ANY($1)
                """, node_ids)
            else:
                edges = []

        return {
            "success": True,
            "nodes": [
                {
                    "id": n["id"],
                    "type": n["node_type"],
                    "title": n["title"],
                    "content": n["content"][:200] if n["content"] else None,
                    "parent_id": n["parent_id"]
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": e["id"],
                    "source": e["source_id"],
                    "target": e["target_id"],
                    "relationship": e["relationship"],
                    "weight": e["weight"]
                }
                for e in edges
            ]
        }

    # ==================== WEB FETCHING & DOCUMENTATION TOOLS ====================

    @staticmethod
    async def fetch_webpage(
        url: str,
        save_as_memory: bool = True,
        extract_text: bool = True,
        follow_redirects: bool = True,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Fetch and optionally save webpage content.
        """
        try:
            import httpx
            from bs4 import BeautifulSoup
            from datetime import datetime

            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=follow_redirects,
                headers={"User-Agent": "Centre AI Documentation Bot 1.0"}
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                content_type = response.headers.get('content-type', '').lower()

                result = {
                    "url": str(response.url),
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "headers": dict(response.headers),
                    "raw_content": MCPTools._limit_response_size(response.text)["content"],
                    "fetched_at": datetime.utcnow().isoformat()
                }

                # Extract structured content for HTML
                if 'html' in content_type and extract_text:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()

                    result.update({
                        "title": soup.title.string.strip() if soup.title else "",
                        "text_content": MCPTools._limit_response_size(soup.get_text().strip(), 10000)["content"],
                        "links": [{"text": a.get_text().strip(), "href": a.get('href')}
                                for a in soup.find_all('a', href=True)],
                        "headings": [{"level": h.name, "text": h.get_text().strip()}
                                   for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])],
                        "word_count": len(result.get("text_content", "").split())
                    })

                # Save as memory if requested
                if save_as_memory and 'html' in content_type:
                    memory_content = f"Documentation from {url}\n\n"
                    if result.get("title"):
                        memory_content += f"Title: {result['title']}\n\n"
                    memory_content += result.get("text_content", response.text)[:4000]  # Limit size

                    # Create memory entry
                    await MCPTools.create_memory(
                        content=memory_content,
                        memory_type="documentation",
                        priority=3,
                        metadata={
                            "source_url": str(response.url),
                            "fetched_at": result["fetched_at"],
                            "content_type": content_type,
                            "word_count": result.get("word_count", 0)
                        }
                    )
                    result["saved_as_memory"] = True

                return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": url
            }

    @staticmethod
    async def fetch_documentation_site(
        base_url: str,
        max_pages: int = 10,
        save_as_memory: bool = True,
        include_patterns: List[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch and index an entire documentation website.
        """
        import httpx
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse

        if include_patterns is None:
            include_patterns = []

        crawled_urls = set()
        results = []
        queue = [base_url]
        base_domain = urlparse(base_url).netloc

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                while queue and len(crawled_urls) < max_pages:
                    current_url = queue.pop(0)

                    if current_url in crawled_urls:
                        continue

                    crawled_urls.add(current_url)

                    try:
                        # Fetch the page
                        page_result = await MCPTools.fetch_webpage(
                            url=current_url,
                            save_as_memory=save_as_memory,
                            extract_text=True,
                            follow_redirects=True
                        )

                        if page_result.get("status_code") == 200:
                            results.append({
                                "url": current_url,
                                "title": page_result.get("title", ""),
                                "word_count": page_result.get("word_count", 0),
                                "saved_as_memory": page_result.get("saved_as_memory", False)
                            })

                            # Extract links for further crawling
                            for link in page_result.get("links", []):
                                if link.get("href"):
                                    full_url = urljoin(current_url, link["href"])
                                    parsed = urlparse(full_url)

                                    # Only crawl same domain
                                    if parsed.netloc == base_domain:
                                        # Check include patterns
                                        if not include_patterns or any(pattern in full_url for pattern in include_patterns):
                                            if full_url not in crawled_urls and full_url not in queue:
                                                queue.append(full_url)

                    except Exception as e:
                        results.append({
                            "url": current_url,
                            "error": str(e)
                        })

            return {
                "success": True,
                "base_url": base_url,
                "pages_crawled": len(results),
                "pages_with_errors": len([r for r in results if "error" in r]),
                "total_words": sum(r.get("word_count", 0) for r in results),
                "results": results
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "base_url": base_url
            }

    @staticmethod
    async def search_saved_documentation(
        query: str,
        limit: int = 10,
        min_relevance: float = 0.3
    ) -> Dict[str, Any]:
        """
        Search through saved documentation memories.
        """
        # Use the existing search_memory functionality but filter for documentation
        search_results = await MCPTools.search_memory(
            query=query,
            limit=limit * 2,  # Get more to filter
            memory_type="documentation",
            min_similarity=min_relevance
        )

        if not search_results.get("success"):
            return search_results

        # Filter and format results specifically for documentation
        filtered_results = []
        for result in search_results.get("memories", []):
            if result.get("memory_type") == "documentation":
                payload = result.get("payload", {})
                metadata = payload.get("metadata", {})

                filtered_results.append({
                    "id": result.get("id"),
                    "title": result.get("title", "Untitled Documentation"),
                    "content_preview": result.get("content", "")[:500] + "..." if len(result.get("content", "")) > 500 else result.get("content", ""),
                    "relevance_score": result.get("similarity_score", 0.0),
                    "source_url": metadata.get("source_url", ""),
                    "fetched_at": metadata.get("fetched_at", ""),
                    "word_count": metadata.get("word_count", 0)
                })

        return {
            "query": query,
            "total_results": len(filtered_results),
            "results": filtered_results[:limit]
        }


# Tool definitions for MCP protocol
TOOL_DEFINITIONS = [
    {
        "name": "create_memory",
        "description": "Create a new memory entry in the knowledge base. Use this to store important information, facts, reminders, or context that should be remembered.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The memory content to store"
                },
                "memory_type": {
                    "type": "string",
                    "enum": ["general", "fact", "reminder", "context", "preference"],
                    "description": "Type of memory"
                },
                "importance": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Importance level (1-10)"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for categorization"
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata"
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "get_memory",
        "description": "Retrieve memories from the knowledge base using semantic search or filters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "memory_type": {
                    "type": "string",
                    "description": "Filter by memory type"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results"
                },
                "semantic_search": {
                    "type": "boolean",
                    "description": "Use vector similarity search"
                }
            }
        }
    },
    {
        "name": "get_codebase",
        "description": "Retrieve codebase information and search code files using semantic search.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "codebase_id": {
                    "type": "integer",
                    "description": "Specific codebase ID"
                },
                "name": {
                    "type": "string",
                    "description": "Search by name"
                },
                "query": {
                    "type": "string",
                    "description": "Search code content"
                },
                "language": {
                    "type": "string",
                    "description": "Filter by language"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results"
                }
            }
        }
    },
    {
        "name": "capture_codebase",
        "description": "Index a codebase from a local path for semantic search.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name for the codebase"
                },
                "path": {
                    "type": "string",
                    "description": "Local path to the codebase"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description"
                },
                "repo_url": {
                    "type": "string",
                    "description": "Git repository URL"
                }
            },
            "required": ["name", "path"]
        }
    },
    {
        "name": "get_instructions",
        "description": "Retrieve general instructions and guidelines configured by the administrators.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by category"
                },
                "active_only": {
                    "type": "boolean",
                    "description": "Only return active instructions"
                }
            }
        }
    },
    {
        "name": "who_am_i_talking_to",
        "description": "Get information about the MCP server administrators and their profiles.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "project_overview",
        "description": "Get overview of projects being managed with status, priorities, and details.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "Specific project ID"
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "completed", "paused", "archived"],
                    "description": "Filter by status"
                }
            }
        }
    },
    {
        "name": "conversation_overview",
        "description": "Get overview of recorded conversations and their content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Specific session ID"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum conversations"
                },
                "include_messages": {
                    "type": "boolean",
                    "description": "Include message history"
                }
            }
        }
    },
    {
        "name": "conversation_log",
        "description": "Log a conversation or message exchange. Use this to store interactions for later retrieval. Creates a new conversation if session_id doesn't exist.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID (auto-generated if not provided)"
                },
                "title": {
                    "type": "string",
                    "description": "Conversation title"
                },
                "user_message": {
                    "type": "string",
                    "description": "The user message"
                },
                "assistant_response": {
                    "type": "string",
                    "description": "The assistant response"
                },
                "tool_calls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of tools called during response"
                },
                "client_name": {
                    "type": "string",
                    "description": "Client application name"
                }
            },
            "required": ["user_message", "assistant_response"]
        }
    },
    {
        "name": "note_create",
        "description": "Create a quick note. Notes can be associated with projects or conversations. Use for ideas, todos, questions, references, or general notes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Note content"
                },
                "title": {
                    "type": "string",
                    "description": "Note title"
                },
                "note_type": {
                    "type": "string",
                    "enum": ["general", "idea", "todo", "question", "reference", "meeting", "research"],
                    "description": "Type of note"
                },
                "project_id": {
                    "type": "integer",
                    "description": "Associated project ID"
                },
                "is_pinned": {
                    "type": "boolean",
                    "description": "Pin this note"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Note tags"
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "note_search",
        "description": "Search notes by content, type, or tags.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "note_type": {
                    "type": "string",
                    "description": "Filter by note type"
                },
                "project_id": {
                    "type": "integer",
                    "description": "Filter by project"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags"
                },
                "pinned_only": {
                    "type": "boolean",
                    "description": "Only pinned notes"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results"
                }
            }
        }
    },
    {
        "name": "task_create",
        "description": "Create a new task within a project. Tasks can have subtasks and due dates.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "Project ID for this task"
                },
                "title": {
                    "type": "string",
                    "description": "Task title"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed task description"
                },
                "priority": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "description": "Priority 1-10"
                },
                "due_date": {
                    "type": "string",
                    "description": "Due date (YYYY-MM-DD)"
                },
                "assigned_to": {
                    "type": "string",
                    "description": "Assignee"
                },
                "parent_task_id": {
                    "type": "integer",
                    "description": "Parent task ID for subtasks"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Task tags"
                }
            },
            "required": ["project_id", "title"]
        }
    },
    {
        "name": "task_list",
        "description": "List tasks with optional filters by project, status, or assignee.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "integer",
                    "description": "Filter by project"
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "cancelled"],
                    "description": "Filter by status"
                },
                "assigned_to": {
                    "type": "string",
                    "description": "Filter by assignee"
                },
                "include_subtasks": {
                    "type": "boolean",
                    "description": "Include subtasks"
                },
                "due_before": {
                    "type": "string",
                    "description": "Filter tasks due before date"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results"
                }
            }
        }
    },
    {
        "name": "task_update",
        "description": "Update an existing task status, priority, or details.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "Task ID"
                },
                "title": {
                    "type": "string",
                    "description": "New title"
                },
                "description": {
                    "type": "string",
                    "description": "New description"
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed", "cancelled"],
                    "description": "New status"
                },
                "priority": {
                    "type": "integer",
                    "description": "New priority"
                },
                "due_date": {
                    "type": "string",
                    "description": "New due date"
                }
            },
            "required": ["task_id"]
        }
    },
    {
        "name": "web_search",
        "description": "Search the web for information using configurable search engines. Supports DuckDuckGo, SearX, Qwant, and Startpage. Uses default search engine from system settings if not specified.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of search results to return (1-50). Uses system default if not specified.",
                    "minimum": 1,
                    "maximum": 50
                },
                "search_engine": {
                    "type": "string",
                    "enum": ["duckduckgo", "searx", "qwant", "startpage"],
                    "description": "Search engine to use. If not specified, uses the default from system settings. Options: duckduckgo (privacy-focused), searx (configurable instance), qwant (European privacy-focused), startpage (Google proxy with privacy)"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_knowledge_graph",
        "description": "Get knowledge graph data for visualization.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_type": {
                    "type": "string",
                    "description": "Filter by node type"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum nodes"
                }
            }
        }
    }
]

# Add the new tool schemas to the TOOL_DEFINITIONS list
TOOL_DEFINITIONS.extend([
    {
        "name": "fetch_webpage",
        "description": "Fetch and optionally save webpage content to memory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to fetch"
                },
                "save_as_memory": {
                    "type": "boolean",
                    "description": "Whether to save content as memory",
                    "default": True
                },
                "extract_text": {
                    "type": "boolean",
                    "description": "Whether to extract plain text from HTML",
                    "default": True
                },
                "follow_redirects": {
                    "type": "boolean",
                    "description": "Whether to follow redirects",
                    "default": True
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "default": 30
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "fetch_documentation_site",
        "description": "Fetch and index an entire documentation website",
        "inputSchema": {
            "type": "object",
            "properties": {
                "base_url": {
                    "type": "string",
                    "description": "Base URL of the documentation site"
                },
                "max_pages": {
                    "type": "integer",
                    "description": "Maximum pages to crawl",
                    "default": 10
                },
                "save_as_memory": {
                    "type": "boolean",
                    "description": "Whether to save pages as memories",
                    "default": True
                },
                "include_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "URL patterns to include",
                    "default": []
                }
            },
            "required": ["base_url"]
        }
    },
    {
        "name": "search_saved_documentation",
        "description": "Search through saved documentation memories",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 10
                },
                "min_relevance": {
                    "type": "number",
                    "description": "Minimum relevance score",
                    "default": 0.3
                }
            },
            "required": ["query"]
        }
    }
])

# Extension to MCPTools class with new documentation methods
class MCPToolsExtensions:
    @staticmethod
    async def fetch_webpage(
        url: str,
        save_as_memory: bool = True,
        extract_text: bool = True,
        follow_redirects: bool = True,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Fetch and optionally save webpage content.

        Args:
            url: URL to fetch
            save_as_memory: Whether to save the content as a memory for future reference
            extract_text: Whether to extract plain text from HTML
            follow_redirects: Whether to follow redirects
            timeout: Request timeout in seconds

        Returns:
            Webpage content with metadata
        """
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                follow_redirects=follow_redirects,
                headers={"User-Agent": "Centre AI Documentation Bot 1.0"}
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                content_type = response.headers.get('content-type', '').lower()

                result = {
                    "url": str(response.url),
                    "status_code": response.status_code,
                    "content_type": content_type,
                    "headers": dict(response.headers),
                    "raw_content": MCPTools._limit_response_size(response.text)["content"],
                    "fetched_at": datetime.utcnow().isoformat()
                }

                # Extract structured content for HTML
                if 'html' in content_type:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Extract title
                    title_elem = soup.find('title')
                    title = title_elem.get_text(strip=True) if title_elem else url

                    # Extract meta description
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    description = meta_desc.get('content', '') if meta_desc else ''

                    # Extract main content
                    if extract_text:
                        # Remove script and style elements
                        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                            script.decompose()

                        # Extract text from main content areas
                        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.find('body')
                        text_content = main_content.get_text(separator='\n', strip=True) if main_content else soup.get_text(separator='\n', strip=True)

                        result.update({
                            "title": title,
                            "description": description,
                            "text_content": text_content,
                            "word_count": len(text_content.split()),
                            "char_count": len(text_content)
                        })

                    # Extract links
                    links = []
                    for link in soup.find_all('a', href=True):
                        href = link.get('href')
                        link_text = link.get_text(strip=True)
                        if href and link_text:
                            links.append({"url": href, "text": link_text})

                    result["links"] = links[:20]  # Limit to first 20 links

                # Save as memory if requested
                if save_as_memory and 'title' in result:
                    memory_content = f"Documentation: {result['title']}\nURL: {url}\nDescription: {result.get('description', '')}\n\nContent:\n{result.get('text_content', '')}"

                    await MCPTools.create_memory(
                        content=memory_content,
                        memory_type="documentation",
                        importance=7,
                        tags=["documentation", "web", "fetched"],
                        metadata={
                            "source_url": url,
                            "fetched_at": result["fetched_at"],
                            "content_type": content_type,
                            "word_count": result.get("word_count", 0)
                        }
                    )

                    result["saved_as_memory"] = True

                return {
                    "success": True,
                    "data": result
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": f"Timeout after {timeout} seconds",
                "url": url
            }
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.reason_phrase}",
                "url": url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": url
            }

    @staticmethod
    async def fetch_documentation_site(
        base_url: str,
        max_pages: int = 10,
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
        save_all: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch multiple pages from a documentation site.

        Args:
            base_url: Base URL of the documentation site
            max_pages: Maximum number of pages to fetch
            include_patterns: URL patterns to include (wildcards supported)
            exclude_patterns: URL patterns to exclude (wildcards supported)
            save_all: Whether to save all pages as memories

        Returns:
            Summary of fetched documentation
        """
        include_patterns = include_patterns or ["*"]
        exclude_patterns = exclude_patterns or []

        visited_urls = set()
        to_visit = [base_url]
        fetched_pages = []

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            while to_visit and len(fetched_pages) < max_pages:
                current_url = to_visit.pop(0)

                if current_url in visited_urls:
                    continue

                visited_urls.add(current_url)

                # Check patterns
                url_matches_include = any(current_url.find(pattern.replace('*', '')) != -1 for pattern in include_patterns)
                url_matches_exclude = any(current_url.find(pattern.replace('*', '')) != -1 for pattern in exclude_patterns)

                if not url_matches_include or url_matches_exclude:
                    continue

                try:
                    response = await client.get(current_url)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')

                        # Extract page info
                        title = soup.find('title')
                        title_text = title.get_text(strip=True) if title else current_url

                        # Extract text content
                        for script in soup(["script", "style", "nav", "header", "footer"]):
                            script.decompose()

                        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.find('body')
                        text_content = main_content.get_text(separator='\n', strip=True) if main_content else soup.get_text(separator='\n', strip=True)

                        page_data = {
                            "url": current_url,
                            "title": title_text,
                            "content": text_content,
                            "word_count": len(text_content.split()),
                            "fetched_at": datetime.utcnow().isoformat()
                        }

                        fetched_pages.append(page_data)

                        # Save as memory if requested
                        if save_all:
                            memory_content = f"Documentation: {title_text}\nURL: {current_url}\n\nContent:\n{text_content}"

                            await MCPTools.create_memory(
                                content=memory_content,
                                memory_type="documentation",
                                importance=6,
                                tags=["documentation", "bulk-fetch", "site"],
                                metadata={
                                    "source_url": current_url,
                                    "fetched_at": page_data["fetched_at"],
                                    "word_count": page_data["word_count"],
                                    "base_site": base_url
                                }
                            )

                        # Find more links to explore
                        if len(fetched_pages) < max_pages:
                            for link in soup.find_all('a', href=True):
                                href = link.get('href')
                                if href:
                                    # Convert relative URLs to absolute
                                    if href.startswith('/'):
                                        from urllib.parse import urljoin
                                        href = urljoin(current_url, href)

                                    # Only add URLs from the same domain
                                    if href.startswith(base_url) and href not in visited_urls and href not in to_visit:
                                        to_visit.append(href)

                except Exception as e:
                    continue

        return {
            "success": True,
            "base_url": base_url,
            "pages_fetched": len(fetched_pages),
            "total_words": sum(page["word_count"] for page in fetched_pages),
            "pages": fetched_pages[:5],  # Return first 5 as sample
            "saved_as_memories": save_all
        }

    @staticmethod
    async def search_saved_documentation(
        query: str,
        limit: int = 10,
        min_relevance: float = 0.3
    ) -> Dict[str, Any]:
        """
        Search through saved documentation memories.

        Args:
            query: Search query
            limit: Maximum number of results
            min_relevance: Minimum relevance score

        Returns:
            Relevant documentation memories
        """
        # Search in vector store for documentation memories
        vector_results = await vector_store.search(
            collection=VectorStore.COLLECTION_MEMORIES,
            query=query,
            limit=limit * 2,  # Get more to filter
            filters={"memory_type": "documentation"}
        )

        # Filter by relevance and format results
        filtered_results = []
        for result in vector_results:
            if result.get("score", 0) >= min_relevance:
                payload = result.get("payload", {})

                filtered_results.append({
                    "content": payload.get("content", ""),
                    "relevance_score": result.get("score", 0),
                    "source_url": payload.get("metadata", {}).get("source_url", ""),
                    "fetched_at": payload.get("metadata", {}).get("fetched_at", ""),
                    "word_count": payload.get("metadata", {}).get("word_count", 0)
                })

        return {
            "query": query,
            "total_results": len(filtered_results),
            "results": filtered_results[:limit]
        }
