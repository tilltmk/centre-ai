"""
Ollama-based Embedding Service for Centre AI
Supports local embedding models via Ollama, including EmbeddingGemma
"""

import asyncio
import httpx
import logging
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)


class OllamaEmbeddingService:
    """Local embedding service using Ollama"""

    def __init__(
        self,
        model: str = "embeddinggemma",
        base_url: str = "http://localhost:11434",
        max_retries: int = 3,
        timeout: float = 30.0
    ):
        self.model = model
        self.base_url = base_url
        self.max_retries = max_retries
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for a single text"""
        embeddings = await self.get_embeddings([text])
        return embeddings[0] if embeddings else []

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts"""
        if not texts:
            return []

        embeddings = []
        for text in texts:
            try:
                embedding = await self._request_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"Failed to get embedding for text: {e}")
                # Return zero vector as fallback
                embeddings.append([0.0] * 768)  # EmbeddingGemma dimension

        return embeddings

    async def _request_embedding(self, text: str) -> List[float]:
        """Make embedding request to Ollama"""
        for attempt in range(self.max_retries):
            try:
                response = await self.client.post(
                    f"{self.base_url}/api/embed",
                    json={
                        "model": self.model,
                        "input": text
                    }
                )
                response.raise_for_status()
                data = response.json()

                if "embeddings" in data and data["embeddings"]:
                    return data["embeddings"][0]
                else:
                    raise ValueError("No embeddings in response")

            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2 ** attempt)

        return []

    async def health_check(self) -> Dict[str, Any]:
        """Check if Ollama service is healthy"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

            # Check if our model is available
            models = [model["name"] for model in data.get("models", [])]
            model_available = any(self.model in model for model in models)

            return {
                "status": "healthy",
                "model": self.model,
                "model_available": model_available,
                "available_models": models
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model": self.model
            }

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/show",
                json={"name": self.model}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}


class EmbeddingServiceFactory:
    """Factory for creating embedding services"""

    @staticmethod
    def create_service(service_type: str = "ollama", **kwargs) -> OllamaEmbeddingService:
        """Create embedding service based on type"""
        service_type = service_type.lower()

        if service_type == "ollama":
            return OllamaEmbeddingService(**kwargs)
        else:
            raise ValueError(f"Unknown embedding service type: {service_type}")

    @staticmethod
    def from_config() -> OllamaEmbeddingService:
        """Create embedding service from environment configuration"""
        model = os.getenv("OLLAMA_EMBEDDING_MODEL", "embeddinggemma")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        return OllamaEmbeddingService(
            model=model,
            base_url=base_url
        )


# Test function
async def test_embeddings():
    """Test the embedding service"""
    async with OllamaEmbeddingService() as service:
        # Health check
        health = await service.health_check()
        print(f"Health: {health}")

        # Test embedding
        texts = ["Hello world", "Centre AI is awesome", "Embedding test"]
        embeddings = await service.get_embeddings(texts)

        for text, embedding in zip(texts, embeddings):
            print(f"Text: {text}")
            print(f"Embedding dimensions: {len(embedding)}")
            print(f"Sample values: {embedding[:5]}")
            print("---")


if __name__ == "__main__":
    asyncio.run(test_embeddings())