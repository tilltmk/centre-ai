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

import httpx
from bs4 import BeautifulSoup

from .database import db, vector_store, VectorStore
from .config import config


class MCPTools:
    """Collection of all MCP tools"""

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
                    results.append({
                        "id": row["id"],
                        "content": row["content"],
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
            '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml', '.md': 'markdown'
        }

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
        errors = []

        for file_path in path.rglob("*"):
            if file_path.is_file() and file_path.suffix in extensions:
                # Skip common ignore patterns
                if any(p in str(file_path) for p in ['.git', 'node_modules', '__pycache__', 'venv', '.env']):
                    continue

                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    if len(content) > 100000:  # Skip very large files
                        continue

                    language = extensions[file_path.suffix]
                    relative_path = str(file_path.relative_to(path))

                    # Generate embedding
                    vector = vector_store.encode(content[:8000])  # Limit for embedding
                    embedding_id = vector_store.generate_id(f"{codebase_id}:{relative_path}")

                    # Store in database
                    async with db.acquire() as conn:
                        await conn.execute("""
                            INSERT INTO code_files (codebase_id, file_path, content, language, embedding_id)
                            VALUES ($1, $2, $3, $4, $5)
                        """, codebase_id, relative_path, content, language, embedding_id)

                    # Store in vector database
                    await vector_store.upsert(
                        VectorStore.COLLECTION_CODE,
                        embedding_id,
                        vector,
                        {
                            "codebase_id": codebase_id,
                            "file_path": relative_path,
                            "language": language,
                            "content": content[:2000]
                        }
                    )

                    files_indexed += 1
                except Exception as e:
                    errors.append(f"{file_path}: {str(e)}")

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

    # ==================== WEB SEARCH TOOL ====================

    @staticmethod
    async def web_search(
        query: str,
        num_results: int = 5,
        search_engine: str = "duckduckgo"
    ) -> Dict[str, Any]:
        """
        Search the web for information.

        Args:
            query: Search query
            num_results: Number of results to return
            search_engine: Search engine to use (duckduckgo, google)

        Returns:
            List of search results with titles, URLs, and snippets
        """
        results = []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
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
                else:
                    return {
                        "success": False,
                        "error": f"Search engine '{search_engine}' not supported"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": f"Search failed: {str(e)}"
            }

        return {
            "success": True,
            "query": query,
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
        "name": "web_search",
        "description": "Search the web for information using DuckDuckGo.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results"
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
