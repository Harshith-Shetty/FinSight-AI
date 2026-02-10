"""
Multi-mode RAG service for hybrid and private chat modes.
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
from uuid import UUID

from app.services.embeddings import EmbeddingGenerator
from app.services.vector_store import QdrantVectorStore
from app.services.llm.groq_provider import GroqProvider
from app.models.database import ChatMode


class RAGService:
    """
    Retrieval-Augmented Generation service with multi-mode support.
    Supports both hybrid (system + user docs) and private (user docs only) modes.
    """
    
    def __init__(self):
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = QdrantVectorStore()
        self.llm_provider = GroqProvider()
    
    async def query_hybrid_mode(
        self,
        user_id: UUID,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search both system knowledge base and user documents.
        
        Args:
            user_id: User ID
            query: Search query
            top_k: Total number of results to return
        
        Returns:
            List of relevant chunks with scores and metadata
        """
        # Generate query embedding
        query_embedding = await self.embedding_gen.generate_embeddings([query])
        query_vector = query_embedding[0]  # numpy array
        
        # Search user documents (all results from user docs)
        user_k = top_k
        user_results = await self.vector_store.search_user_documents(
            user_id=str(user_id),
            query_embedding=query_vector,
            limit=user_k
        )
        
        # For now, return only user results
        # TODO: Add system knowledge base search when system KB is populated
        all_results = []
        
        for result in user_results:
            all_results.append({
                "text": result.get("text", ""),
                "score": result.get("score", 0.0),
                "source": "user",
                "document_id": result.get("document_id"),
                "metadata": result
            })
        
        # Sort by score descending
        all_results.sort(key=lambda x: x["score"], reverse=True)
        
        return all_results[:top_k]
    
    async def query_private_mode(
        self,
        user_id: UUID,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search only user's private documents.
        
        Args:
            user_id: User ID
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of relevant chunks from user documents
        """
        # Generate query embedding
        query_embedding = await self.embedding_gen.generate_embeddings([query])
        query_vector = query_embedding[0]  # numpy array
        
        # Search only user documents
        user_results = await self.vector_store.search_user_documents(
            user_id=str(user_id),
            query_embedding=query_vector,
            limit=top_k
        )
        
        results = []
        for result in user_results:
            results.append({
                "text": result.get("text", ""),
                "score": result.get("score", 0.0),
                "source": "user",
                "document_id": result.get("document_id"),
                "metadata": result
            })
        
        return results
    
    def build_rag_prompt(
        self,
        query: str,
        context: List[Dict[str, Any]],
        mode: ChatMode
    ) -> str:
        """
        Build RAG prompt with context.
        
        Args:
            query: User query
            context: Retrieved context chunks
            mode: Chat mode (hybrid or private)
        
        Returns:
            Formatted prompt for LLM
        """
        if not context:
            return f"""You are a helpful financial AI assistant. Answer the following question:

{query}

Note: No relevant documents were found. Provide a general answer based on your knowledge."""
        
        # Build context section
        context_text = "\n\n".join([
            f"[Source {i+1} - {chunk['source']}]: {chunk['text']}"
            for i, chunk in enumerate(context)
        ])
        
        mode_instruction = ""
        if mode == ChatMode.HYBRID:
            mode_instruction = "You have access to both system financial knowledge and user-uploaded documents."
        else:
            mode_instruction = "You have access to the user's private documents only."
        
        prompt = f"""You are a helpful financial AI assistant. {mode_instruction}

Use the following context to answer the question. If the context doesn't contain relevant information, say so clearly.

CONTEXT:
{context_text}

QUESTION:
{query}

ANSWER (be concise, accurate, and cite sources when possible):"""
        
        return prompt
    
    async def generate_response(
        self,
        user_id: UUID,
        query: str,
        mode: ChatMode,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Generate response using RAG (synchronous).
        
        Args:
            user_id: User ID
            query: User query
            mode: Chat mode (hybrid or private)
            top_k: Number of context chunks to retrieve
        
        Returns:
            Response with text and sources
        """
        # Retrieve context based on mode
        if mode == ChatMode.HYBRID:
            context = await self.query_hybrid_mode(user_id, query, top_k)
        else:
            context = await self.query_private_mode(user_id, query, top_k)
        
        # Build prompt
        prompt = self.build_rag_prompt(query, context, mode)
        
        # Generate response
        response_text = await self.llm_provider.generate(prompt)
        
        return {
            "text": response_text,
            "sources": context,
            "mode": mode.value
        }
    
    async def generate_response_stream(
        self,
        user_id: UUID,
        query: str,
        mode: ChatMode,
        top_k: int = 5
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate streaming response using RAG.
        
        Args:
            user_id: User ID
            query: User query
            mode: Chat mode (hybrid or private)
            top_k: Number of context chunks to retrieve
        
        Yields:
            Response chunks and metadata
        """
        # Retrieve context based on mode
        if mode == ChatMode.HYBRID:
            context = await self.query_hybrid_mode(user_id, query, top_k)
        else:
            context = await self.query_private_mode(user_id, query, top_k)
        
        # Build prompt
        prompt = self.build_rag_prompt(query, context, mode)
        
        # Stream response from LLM
        async for chunk in self.llm_provider.stream(prompt):
            yield {
                "type": "chunk",
                "content": chunk
            }
        
        # Send sources at the end
        yield {
            "type": "sources",
            "sources": context
        }
        
        yield {
            "type": "done"
        }
