"""
Qdrant vector store operations.
"""

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Dict, Any
import uuid

from app.core.config import settings
from app.core.exceptions import VectorStoreError


class QdrantVectorStore:
    """
    Manages vector storage and retrieval using Qdrant.
    """
    
    COLLECTION_NAME = "financial_filings"
    SYSTEM_KB_COLLECTION = "system_knowledge_base"
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
    
    def create_user_collection(self, user_id: str):
        """
        Create a user-specific collection if it doesn't exist.
        
        Args:
            user_id: User UUID
        """
        collection_name = f"user_{user_id}_documents"
        
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.VECTOR_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            raise VectorStoreError(f"Failed to create user collection: {str(e)}")
    
    async def upsert_user_vectors(
        self,
        user_id: str,
        document_id: str,
        filename: str,
        chunks: List[str],
        embeddings: Any  # numpy array
    ):
        """
        Store user document chunks and embeddings in user-specific collection.
        
        Args:
            user_id: User UUID
            document_id: Document UUID
            filename: Original filename
            chunks: List of text chunks
            embeddings: Numpy array of embeddings
        """
        collection_name = f"user_{user_id}_documents"
        
        # Ensure collection exists
        self.create_user_collection(user_id)
        
        try:
            points = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                # Qdrant requires UUID or unsigned int — use deterministic UUID5
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}_chunk_{idx}"))
                point = PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        "document_id": document_id,
                        "user_id": user_id,
                        "filename": filename,
                        "chunk_id": idx,
                        "text": chunk
                    }
                )
                points.append(point)
            
            # Batch upsert
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
        except Exception as e:
            raise VectorStoreError(f"Failed to upsert user vectors: {str(e)}")
    
    async def delete_user_document(self, user_id: str, document_id: str):
        """
        Delete all vectors for a specific document.
        
        Args:
            user_id: User UUID
            document_id: Document UUID
        """
        collection_name = f"user_{user_id}_documents"
        
        try:
            # Delete all points with matching document_id
            self.client.delete(
                collection_name=collection_name,
                points_selector={
                    "filter": Filter(
                        must=[
                            FieldCondition(
                                key="document_id",
                                match=MatchValue(value=document_id)
                            )
                        ]
                    )
                }
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to delete document vectors: {str(e)}")
    
    async def search_user_documents(
        self,
        user_id: str,
        query_embedding: Any,  # numpy array
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search user's documents using vector similarity.
        
        Args:
            user_id: User UUID
            query_embedding: Query vector
            top_k: Number of results to return
            
        Returns:
            List of matching chunks with metadata
        """
        collection_name = f"user_{user_id}_documents"
        
        try:
            # Check if the user's collection exists first
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if collection_name not in collection_names:
                # No documents uploaded yet — return empty results
                return []
            
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding.tolist(),
                limit=top_k
            )
            
            return [
                {
                    "text": hit.payload["text"],
                    "filename": hit.payload.get("filename", "unknown"),
                    "document_id": hit.payload["document_id"],
                    "chunk_id": hit.payload["chunk_id"],
                    "score": hit.score
                }
                for hit in results
            ]
            
        except Exception as e:
            raise VectorStoreError(f"Failed to search user documents: {str(e)}")
    
    async def upsert_vectors(
        self,
        ticker: str,
        year: int,
        chunks: List[str],
        embeddings: Any,  # numpy array
        sections: List[str] = None
    ):
        """
        Store document chunks and their embeddings in Qdrant.

        Args:
            ticker: Stock ticker symbol
            year: Filing year
            chunks: List of text chunks
            embeddings: Numpy array of embeddings
            sections: Optional list of section names (e.g. "Item 1A. Risk Factors"),
                      one per chunk. Defaults to "general" if not provided.
        """
        try:
            points = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                section = sections[idx] if sections else "general"
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding.tolist(),
                    payload={
                        "ticker": ticker,
                        "year": year,
                        "chunk_id": idx,
                        "text": chunk,
                        "section": section
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

    # ──────────────────────────────────────────────
    # System Knowledge Base methods
    # ──────────────────────────────────────────────

    def _ensure_system_kb_collection(self):
        """Create system_knowledge_base collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            names = [c.name for c in collections]
            if self.SYSTEM_KB_COLLECTION not in names:
                self.client.create_collection(
                    collection_name=self.SYSTEM_KB_COLLECTION,
                    vectors_config=VectorParams(
                        size=self.VECTOR_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            raise VectorStoreError(f"Failed to create system KB collection: {str(e)}")

    async def upsert_system_kb_vectors(
        self,
        document_id: str,
        filename: str,
        chunks: List[str],
        embeddings: List,
    ):
        """Store document chunks in the shared system_knowledge_base collection."""
        try:
            self._ensure_system_kb_collection()
            points = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_id}_chunk_{idx}"))
                points.append(PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        "document_id": document_id,
                        "filename": filename,
                        "chunk_id": idx,
                        "text": chunk,
                        "source": "system",
                    }
                ))

            batch_size = 100
            for i in range(0, len(points), batch_size):
                response = self.client.upsert(
                    collection_name=self.SYSTEM_KB_COLLECTION,
                    points=points[i:i + batch_size],
                    wait=True
                )
                if hasattr(response, 'status') and str(response.status) not in ('ok', 'UpdateStatus.Completed'):
                    raise VectorStoreError(f"Unexpected Response: {response.status}")

        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(f"Failed to upsert system KB vectors: {str(e)}")

    async def search_system_kb(
        self,
        query_embedding,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search the system knowledge base (all public documents)."""
        try:
            self._ensure_system_kb_collection()
            results = self.client.search(
                collection_name=self.SYSTEM_KB_COLLECTION,
                query_vector=query_embedding.tolist(),
                limit=top_k
            )
            return [
                {
                    "text": hit.payload.get("text", ""),
                    "score": hit.score,
                    "document_id": hit.payload.get("document_id"),
                    "filename": hit.payload.get("filename"),
                    "chunk_id": hit.payload.get("chunk_id"),
                    "source": "system",
                }
                for hit in results
            ]
        except Exception as e:
            raise VectorStoreError(f"Failed to search system KB: {str(e)}")

    async def scroll_all_texts(self, collection_name: str) -> List[Dict[str, Any]]:
        """
        Fetch all chunk texts and metadata from a collection for BM25 indexing.

        Args:
            collection_name: Name of the Qdrant collection to scroll

        Returns:
            List of {"text", "document_id", "filename", "chunk_id"} dicts
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            if collection_name not in collection_names:
                return []

            results = []
            offset = None
            while True:
                points, offset = self.client.scroll(
                    collection_name=collection_name,
                    limit=256,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False,
                )
                for point in points:
                    payload = point.payload or {}
                    results.append({
                        "text": payload.get("text", ""),
                        "document_id": payload.get("document_id"),
                        "filename": payload.get("filename"),
                        "chunk_id": payload.get("chunk_id"),
                    })
                if offset is None:
                    break

            return results
        except Exception as e:
            raise VectorStoreError(f"Failed to scroll collection: {str(e)}")
