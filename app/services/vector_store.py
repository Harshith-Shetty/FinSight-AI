"""
Qdrant vector store operations.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
import uuid

from app.core.config import settings
from app.core.exceptions import VectorStoreError


class QdrantVectorStore:
    """
    Manages vector storage and retrieval using Qdrant.
    """
    
    COLLECTION_NAME = "financial_filings"
    VECTOR_DIMENSION = 384  # all-MiniLM-L6-v2 dimension
    
    def __init__(self):
        """Initialize Qdrant client."""
        self.client = QdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY
        )
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.COLLECTION_NAME not in collection_names:
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self.VECTOR_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            raise VectorStoreError(f"Failed to create collection: {str(e)}")
    
    async def upsert_vectors(
        self,
        ticker: str,
        year: int,
        chunks: List[str],
        embeddings: Any  # numpy array
    ):
        """
        Store document chunks and their embeddings in Qdrant.
        
        Args:
            ticker: Stock ticker symbol
            year: Filing year
            chunks: List of text chunks
            embeddings: Numpy array of embeddings
        """
        try:
            points = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.tolist(),
                    payload={
                        "ticker": ticker,
                        "year": year,
                        "chunk_id": idx,
                        "text": chunk,
                        "section": "general"  # Could be enhanced to detect sections
                    }
                )
                points.append(point)
            
            # Batch upsert
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=points
            )
            
        except Exception as e:
            raise VectorStoreError(f"Failed to upsert vectors: {str(e)}")
    
    async def search(
        self,
        query_embedding: Any,  # numpy array
        ticker: str,
        year: int,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using vector similarity.
        
        Args:
            query_embedding: Query vector
            ticker: Filter by ticker
            year: Filter by year
            top_k: Number of results to return
            
        Returns:
            List of matching chunks with metadata
        """
        try:
            results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_embedding.tolist(),
                query_filter={
                    "must": [
                        {"key": "ticker", "match": {"value": ticker}},
                        {"key": "year", "match": {"value": year}}
                    ]
                },
                limit=top_k
            )
            
            return [
                {
                    "text": hit.payload["text"],
                    "section": hit.payload.get("section", "unknown"),
                    "chunk_id": hit.payload["chunk_id"],
                    "score": hit.score
                }
                for hit in results
            ]
            
        except Exception as e:
            raise VectorStoreError(f"Failed to search vectors: {str(e)}")
