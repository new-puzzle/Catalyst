import chromadb
from chromadb.config import Settings as ChromaSettings
import httpx
from typing import List, Optional
import logging

from config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB vector store for RAG on journal entries."""

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="journal_entries",
            metadata={"hnsw:space": "cosine"}
        )

    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings using Gemini."""
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key required for embeddings")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={settings.gemini_api_key}",
                    json={
                        "model": "models/text-embedding-004",
                        "content": {"parts": [{"text": text}]}
                    },
                    timeout=30.0
                )

                if response.status_code != 200:
                    logger.error(f"Embedding API returned {response.status_code}: {response.text[:500]}")
                    raise ValueError(f"Embedding API error (status {response.status_code})")

                data = response.json()

                if "embedding" in data:
                    return data["embedding"]["values"]
                else:
                    logger.error(f"Embedding error: {data}")
                    raise ValueError(f"Failed to generate embedding: {data.get('error', {}).get('message', 'Unknown error')}")

        except httpx.TimeoutException:
            logger.error("Embedding API timeout")
            raise ValueError("Embedding API timeout")
        except httpx.RequestError as e:
            logger.error(f"Embedding network error: {e}")
            raise ValueError(f"Network error for embeddings: {str(e)}")

    async def add_entry(
        self,
        entry_id: str,
        content: str,
        metadata: dict
    ):
        """Add a journal entry to the vector store."""
        try:
            embedding = await self.embed_text(content)
            self.collection.upsert(
                ids=[entry_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
            logger.info(f"Added entry {entry_id} to vector store")
        except Exception as e:
            logger.error(f"Failed to add entry to vector store: {e}")
            raise

    async def search(
        self,
        query: str,
        user_id: int,
        n_results: int = 5
    ) -> List[dict]:
        """Search for relevant entries."""
        try:
            embedding = await self.embed_text(query)
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results,
                where={"user_id": user_id},
                include=["documents", "metadatas", "distances"]
            )

            entries = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    entries.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results["distances"] else 0
                    })

            return entries
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def delete_entry(self, entry_id: str):
        """Delete an entry from the vector store."""
        try:
            self.collection.delete(ids=[entry_id])
            logger.info(f"Deleted entry {entry_id} from vector store")
        except Exception as e:
            logger.error(f"Failed to delete entry: {e}")

    async def delete_user_entries(self, user_id: int):
        """Delete all entries for a user."""
        try:
            self.collection.delete(where={"user_id": user_id})
            logger.info(f"Deleted all entries for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to delete user entries: {e}")


# Singleton instance
vector_store = VectorStore()
