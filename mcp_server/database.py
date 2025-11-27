"""
Database models and connection management for Centre AI
"""
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import json
import hashlib

import asyncpg
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from sentence_transformers import SentenceTransformer

from .config import config


class Database:
    """PostgreSQL database manager"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()

    async def connect(self):
        """Create connection pool"""
        async with self._lock:
            if self.pool is None:
                self.pool = await asyncpg.create_pool(
                    config.database.connection_string,
                    min_size=2,
                    max_size=10
                )
                await self._init_schema()

    async def _init_schema(self):
        """Initialize database schema"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    display_name VARCHAR(200),
                    email VARCHAR(255),
                    bio TEXT,
                    avatar_url TEXT,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS memories (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    memory_type VARCHAR(50) DEFAULT 'general',
                    importance INTEGER DEFAULT 5,
                    tags TEXT[] DEFAULT '{}',
                    metadata JSONB DEFAULT '{}',
                    embedding_id VARCHAR(100),
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS codebases (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    repo_url TEXT,
                    local_path TEXT,
                    language VARCHAR(50),
                    indexed_at TIMESTAMP,
                    file_count INTEGER DEFAULT 0,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS code_files (
                    id SERIAL PRIMARY KEY,
                    codebase_id INTEGER REFERENCES codebases(id) ON DELETE CASCADE,
                    file_path TEXT NOT NULL,
                    content TEXT,
                    language VARCHAR(50),
                    embedding_id VARCHAR(100),
                    metadata JSONB DEFAULT '{}',
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS instructions (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(200) NOT NULL,
                    content TEXT NOT NULL,
                    category VARCHAR(100),
                    priority INTEGER DEFAULT 5,
                    is_active BOOLEAN DEFAULT true,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    status VARCHAR(50) DEFAULT 'active',
                    priority INTEGER DEFAULT 5,
                    tags TEXT[] DEFAULT '{}',
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS conversations (
                    id SERIAL PRIMARY KEY,
                    session_id VARCHAR(100) UNIQUE NOT NULL,
                    title VARCHAR(200),
                    summary TEXT,
                    participants TEXT[] DEFAULT '{}',
                    message_count INTEGER DEFAULT 0,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
                    role VARCHAR(50) NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS knowledge_nodes (
                    id SERIAL PRIMARY KEY,
                    node_type VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    content TEXT,
                    parent_id INTEGER REFERENCES knowledge_nodes(id),
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS knowledge_edges (
                    id SERIAL PRIMARY KEY,
                    source_id INTEGER REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
                    target_id INTEGER REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
                    relationship VARCHAR(100) NOT NULL,
                    weight FLOAT DEFAULT 1.0,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
                CREATE INDEX IF NOT EXISTS idx_memories_tags ON memories USING GIN(tags);
                CREATE INDEX IF NOT EXISTS idx_code_files_codebase ON code_files(codebase_id);
                CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
                CREATE INDEX IF NOT EXISTS idx_knowledge_edges_source ON knowledge_edges(source_id);
                CREATE INDEX IF NOT EXISTS idx_knowledge_edges_target ON knowledge_edges(target_id);
            """)

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool"""
        async with self.pool.acquire() as conn:
            yield conn

    async def close(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None


class VectorStore:
    """Qdrant vector store manager"""

    COLLECTION_MEMORIES = "memories"
    COLLECTION_CODE = "code_files"
    COLLECTION_KNOWLEDGE = "knowledge"

    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.encoder: Optional[SentenceTransformer] = None
        self._vector_size = 384

    async def connect(self):
        """Initialize Qdrant client and encoder"""
        self.client = QdrantClient(
            url=config.qdrant.url,
            api_key=config.qdrant.api_key
        )
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        await self._init_collections()

    async def _init_collections(self):
        """Initialize vector collections"""
        for collection_name in [self.COLLECTION_MEMORIES, self.COLLECTION_CODE, self.COLLECTION_KNOWLEDGE]:
            try:
                self.client.get_collection(collection_name)
            except Exception:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=qdrant_models.VectorParams(
                        size=self._vector_size,
                        distance=qdrant_models.Distance.COSINE
                    )
                )

    def encode(self, text: str) -> List[float]:
        """Encode text to vector"""
        return self.encoder.encode(text).tolist()

    def generate_id(self, text: str) -> str:
        """Generate unique ID from text"""
        return hashlib.md5(text.encode()).hexdigest()

    async def upsert(self, collection: str, id: str, vector: List[float], payload: Dict[str, Any]):
        """Insert or update a vector"""
        self.client.upsert(
            collection_name=collection,
            points=[
                qdrant_models.PointStruct(
                    id=id,
                    vector=vector,
                    payload=payload
                )
            ]
        )

    async def search(self, collection: str, query: str, limit: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        """Search for similar vectors"""
        query_vector = self.encode(query)

        filter_condition = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, list):
                    conditions.append(
                        qdrant_models.FieldCondition(
                            key=key,
                            match=qdrant_models.MatchAny(any=value)
                        )
                    )
                else:
                    conditions.append(
                        qdrant_models.FieldCondition(
                            key=key,
                            match=qdrant_models.MatchValue(value=value)
                        )
                    )
            if conditions:
                filter_condition = qdrant_models.Filter(must=conditions)

        results = self.client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=filter_condition
        )

        return [
            {
                "id": str(r.id),
                "score": r.score,
                "payload": r.payload
            }
            for r in results
        ]

    async def delete(self, collection: str, id: str):
        """Delete a vector by ID"""
        self.client.delete(
            collection_name=collection,
            points_selector=qdrant_models.PointIdsList(points=[id])
        )

    async def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        stats = {}
        for collection in [self.COLLECTION_MEMORIES, self.COLLECTION_CODE, self.COLLECTION_KNOWLEDGE]:
            try:
                info = self.client.get_collection(collection)
                stats[collection] = {
                    "vectors_count": info.vectors_count,
                    "points_count": info.points_count
                }
            except Exception:
                stats[collection] = {"vectors_count": 0, "points_count": 0}
        return stats


# Global instances
db = Database()
vector_store = VectorStore()


async def init_databases():
    """Initialize all database connections"""
    await db.connect()
    await vector_store.connect()


async def close_databases():
    """Close all database connections"""
    await db.close()
