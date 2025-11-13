"""
Qdrant Vector Database Client
Manages vector storage and semantic search
"""

import os
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, SearchRequest
)
from sentence_transformers import SentenceTransformer
import logging
import uuid

logger = logging.getLogger(__name__)


class VectorDB:
    """Qdrant Vector Database wrapper"""

    def __init__(self, host: str = None, api_key: str = None):
        self.host = host or os.getenv('QDRANT_HOST', 'http://qdrant:6333')
        self.api_key = api_key or os.getenv('QDRANT_API_KEY')

        # Initialize client
        if self.api_key:
            self.client = QdrantClient(url=self.host, api_key=self.api_key)
        else:
            self.client = QdrantClient(url=self.host)

        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384  # Dimension for all-MiniLM-L6-v2

        logger.info(f"Vector DB initialized with host: {self.host}")

    def create_collection(self, collection_name: str, vector_size: int = None) -> bool:
        """Create a new collection"""
        try:
            if vector_size is None:
                vector_size = self.embedding_dim

            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            return False

    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists"""
        try:
            collections = self.client.get_collections().collections
            return any(c.name == collection_name for c in collections)
        except Exception as e:
            logger.error(f"Error checking collection: {str(e)}")
            return False

    def ensure_collection(self, collection_name: str) -> bool:
        """Ensure collection exists, create if not"""
        if not self.collection_exists(collection_name):
            return self.create_collection(collection_name)
        return True

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        return self.embedding_model.encode(text).tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        return self.embedding_model.encode(texts).tolist()

    def upsert_point(
        self,
        collection_name: str,
        point_id: str,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> bool:
        """Insert or update a point"""
        try:
            self.ensure_collection(collection_name)

            point = PointStruct(
                id=point_id,
                vector=vector,
                payload=payload
            )

            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )

            return True

        except Exception as e:
            logger.error(f"Error upserting point: {str(e)}")
            return False

    def upsert_points(
        self,
        collection_name: str,
        points: List[Dict[str, Any]]
    ) -> bool:
        """Insert or update multiple points"""
        try:
            self.ensure_collection(collection_name)

            point_structs = [
                PointStruct(
                    id=p.get('id', str(uuid.uuid4())),
                    vector=p['vector'],
                    payload=p.get('payload', {})
                )
                for p in points
            ]

            self.client.upsert(
                collection_name=collection_name,
                points=point_structs
            )

            logger.info(f"Upserted {len(points)} points to {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error upserting points: {str(e)}")
            return False

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: float = 0.0,
        filter_conditions: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        try:
            if not self.collection_exists(collection_name):
                return []

            # Build filter if provided
            query_filter = None
            if filter_conditions:
                conditions = []
                for key, value in filter_conditions.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                query_filter = Filter(must=conditions)

            # Search
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter
            )

            return [
                {
                    'id': r.id,
                    'score': r.score,
                    'payload': r.payload
                }
                for r in results
            ]

        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            return []

    def search_text(
        self,
        collection_name: str,
        query_text: str,
        limit: int = 10,
        score_threshold: float = 0.0,
        filter_conditions: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search using text query (automatically embedded)"""
        query_vector = self.embed_text(query_text)
        return self.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            filter_conditions=filter_conditions
        )

    def delete_point(self, collection_name: str, point_id: str) -> bool:
        """Delete a point"""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=[point_id]
            )
            return True

        except Exception as e:
            logger.error(f"Error deleting point: {str(e)}")
            return False

    def delete_collection(self, collection_name: str) -> bool:
        """Delete entire collection"""
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Deleted collection: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            return False

    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get collection information"""
        try:
            info = self.client.get_collection(collection_name)
            return {
                'name': collection_name,
                'points_count': info.points_count,
                'vectors_count': info.vectors_count,
                'status': info.status
            }

        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return None

    def list_collections(self) -> List[str]:
        """List all collections"""
        try:
            collections = self.client.get_collections().collections
            return [c.name for c in collections]

        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            return []
