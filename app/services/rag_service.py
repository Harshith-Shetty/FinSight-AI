"""
Multi-mode RAG service for hybrid and private chat modes.
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
from uuid import UUID

from app.services.embeddings import EmbeddingGenerator
from app.services.vector_store import QdrantVectorStore
from app.services.reranker import Reranker
from app.services.bm25_index import BM25Index
from app.services.llm.groq_provider import GroqProvider
from app.models.database import ChatMode
from app.core.config import settings
from app.services.citations import build_citations


SYSTEM_KB_COLLECTION = "system_knowledge_base"


class RAGService:
    """
    Retrieval-Augmented Generation service with multi-mode support.
    Supports both hybrid (system + user docs) and private (user docs only) modes.

    Retrieval pipeline per query:
      1. (optional) rewrite the query into a standalone form using conversation history
      2. fetch a wide candidate set via dense vector search (+ BM25 for system KB)
      3. rerank candidates with a cross-encoder
      4. gate on rerank score — drop low-confidence context entirely
    """

    def __init__(self):
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = QdrantVectorStore()
        self.llm_provider = GroqProvider()
        self.reranker = Reranker()
        self.bm25_index = BM25Index()
        self._system_kb_indexed = False

    async def _ensure_system_kb_bm25_index(self) -> None:
        """Lazily build the BM25 index for the system knowledge base (once per service instance)."""
        if self._system_kb_indexed:
            return
        try:
            points = await self.vector_store.scroll_all_texts(SYSTEM_KB_COLLECTION)
            self.bm25_index.build(SYSTEM_KB_COLLECTION, points)
        except Exception:
            pass
        finally:
            self._system_kb_indexed = True

    async def query_hybrid_mode(
        self,
        user_id: UUID,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search both system knowledge base and user documents, then rerank and gate.

        Args:
            user_id: User ID
            query: Search query
            top_k: Number of results to return after reranking

        Returns:
            List of relevant chunks with scores and metadata
        """
        retrieval_top_k = max(top_k * 4, settings.RAG_MIN_RETRIEVAL_K)

        # Generate query embedding
        query_embedding = await self.embedding_gen.generate_embeddings([query])
        query_vector = query_embedding[0]  # numpy array

        # Search user documents
        user_results = await self.vector_store.search_user_documents(
            user_id=str(user_id),
            query_embedding=query_vector,
            top_k=retrieval_top_k
        )

        # Search system knowledge base (dense)
        system_results = await self.vector_store.search_system_kb(
            query_embedding=query_vector,
            top_k=retrieval_top_k
        )

        all_results = []
        seen_keys = set()

        for result in user_results:
            all_results.append({
                "text": result.get("text", ""),
                "score": result.get("score", 0.0),
                "source": "user",
                "document_id": result.get("document_id"),
                "metadata": result
            })
        for result in system_results:
            seen_keys.add(("system", result.get("document_id"), result.get("chunk_id")))
            all_results.append({
                "text": result.get("text", ""),
                "score": result.get("score", 0.0),
                "source": "system",
                "document_id": result.get("document_id"),
                "metadata": result
            })

        # Hybrid search: augment with BM25 candidates from the system KB.
        # The cross-encoder reranks the combined set on one scale, so no
        # score normalization/fusion between BM25 and cosine is needed —
        # BM25 contributes recall, the reranker decides final ranking.
        await self._ensure_system_kb_bm25_index()
        bm25_results = self.bm25_index.search(SYSTEM_KB_COLLECTION, query, top_k=retrieval_top_k)
        for result in bm25_results:
            key = ("system", result.get("document_id"), result.get("chunk_id"))
            if key in seen_keys or not result.get("text"):
                continue
            seen_keys.add(key)
            all_results.append({
                "text": result.get("text", ""),
                "score": result.get("bm25_score", 0.0),
                "source": "system",
                "document_id": result.get("document_id"),
                "metadata": result
            })

        return self._rerank_and_gate(query, all_results, top_k)

    async def query_private_mode(
        self,
        user_id: UUID,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search only user's private documents, then rerank and gate.

        Args:
            user_id: User ID
            query: Search query
            top_k: Number of results to return after reranking

        Returns:
            List of relevant chunks from user documents
        """
        retrieval_top_k = max(top_k * 4, settings.RAG_MIN_RETRIEVAL_K)

        # Generate query embedding
        query_embedding = await self.embedding_gen.generate_embeddings([query])
        query_vector = query_embedding[0]  # numpy array

        # Search only user documents
        user_results = await self.vector_store.search_user_documents(
            user_id=str(user_id),
            query_embedding=query_vector,
            top_k=retrieval_top_k
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

        return self._rerank_and_gate(query, results, top_k)

    def _rerank_and_gate(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates with the cross-encoder and drop low-confidence context.

        Returns an empty list if no candidates pass the relevance threshold,
        which signals build_rag_prompt to fall back to the "no context" prompt.
        """
        if not candidates:
            return []

        reranked = self.reranker.rerank(query, candidates, top_k=top_k)
        context = [c for c in reranked if c["rerank_score"] >= settings.RAG_MIN_RERANK_SCORE]

        if len(context) < settings.RAG_MIN_CONTEXT_CHUNKS:
            return []

        return context

    async def rewrite_query(
        self,
        query: str,
        history: List[Dict[str, str]]
    ) -> tuple[str, int]:
        """
        Rewrite a follow-up query into a standalone search query using conversation history.

        Skips rewriting (returns the original query unchanged, 0 tokens) when
        rewriting is disabled, there's not enough history, or the query already
        looks long/specific enough to be standalone.

        Args:
            query: The user's latest message
            history: Recent prior messages as [{"role": "user"/"assistant", "content": ...}, ...]

        Returns:
            Tuple of (search query, tokens used by the rewrite call)
        """
        if not settings.RAG_QUERY_REWRITE_ENABLED:
            return query, 0
        if len(history) < settings.RAG_QUERY_REWRITE_MIN_HISTORY:
            return query, 0
        if len(query.split()) > 8:
            return query, 0

        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content'][:200]}" for m in history
        )

        rewrite_prompt = f"""Given the conversation history and a follow-up question, rewrite the follow-up into a standalone question that includes all necessary context (e.g. company names, tickers, time periods) mentioned earlier. If the follow-up is already standalone, return it unchanged. Return ONLY the rewritten question, no explanation.

CONVERSATION HISTORY:
{history_text}

FOLLOW-UP QUESTION: {query}

STANDALONE QUESTION:"""

        try:
            rewritten, tokens_used = await self.llm_provider.generate(
                rewrite_prompt, temperature=0.0, max_tokens=100
            )
        except Exception:
            return query, 0

        rewritten = rewritten.strip().strip('"').strip("'")

        if not rewritten or len(rewritten) > len(query) * 5:
            return query, 0

        return rewritten, tokens_used

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
            if mode == ChatMode.PRIVATE:
                no_context_note = "No relevant information was found in your uploaded documents."
            else:
                no_context_note = "No relevant documents were found."

            return f"""You are a helpful financial AI assistant. Answer the following question:

{query}

Note: {no_context_note} Provide a general answer based on your knowledge, and make clear that it is not based on the user's documents."""

        # Build context section
        context_text = "\n\n".join([
            f"[Source {chunk['citation_id']} - {chunk['filename']} - {chunk['source']}]: {chunk['text']}"
            for chunk in build_citations(context)
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

Use numbered citations [1], [2], etc. immediately after document-supported claims.
Numbers must match the Source numbers above. Never invent sources or page numbers.
Clearly distinguish general knowledge from document-supported statements.

ANSWER (be concise and accurate):"""

        return prompt

    async def generate_response(
        self,
        user_id: UUID,
        query: str,
        mode: ChatMode,
        top_k: int = 5,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate response using RAG (synchronous).

        Args:
            user_id: User ID
            query: User query
            mode: Chat mode (hybrid or private)
            top_k: Number of context chunks to retrieve
            history: Recent prior messages, used to rewrite follow-up queries

        Returns:
            Response with text and sources
        """
        rewrite_tokens = 0
        search_query = query
        if history:
            search_query, rewrite_tokens = await self.rewrite_query(query, history)

        # Retrieve context based on mode
        if mode == ChatMode.HYBRID:
            context = await self.query_hybrid_mode(user_id, search_query, top_k)
        else:
            context = await self.query_private_mode(user_id, search_query, top_k)

        # Build prompt (uses the original query, not the rewritten search query)
        prompt = self.build_rag_prompt(query, context, mode)

        # Generate response
        response_text, tokens_used = await self.llm_provider.generate(prompt)

        return {
            "text": response_text,
            "sources": build_citations(context),
            "mode": mode.value,
            "tokens_used": tokens_used + rewrite_tokens,
            "search_query": search_query,
        }

    async def generate_response_stream(
        self,
        user_id: UUID,
        query: str,
        mode: ChatMode,
        top_k: int = 5,
        history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate streaming response using RAG.

        Args:
            user_id: User ID
            query: User query
            mode: Chat mode (hybrid or private)
            top_k: Number of context chunks to retrieve
            history: Recent prior messages, used to rewrite follow-up queries

        Yields:
            Response chunks and metadata
        """
        rewrite_tokens = 0
        search_query = query
        if history:
            search_query, rewrite_tokens = await self.rewrite_query(query, history)

        # Retrieve context based on mode
        if mode == ChatMode.HYBRID:
            context = await self.query_hybrid_mode(user_id, search_query, top_k)
        else:
            context = await self.query_private_mode(user_id, search_query, top_k)

        # Build prompt (uses the original query, not the rewritten search query)
        prompt = self.build_rag_prompt(query, context, mode)

        # Send stable references first so citations work while text streams.
        yield {"type": "sources", "sources": build_citations(context)}

        # Stream response from LLM — last yielded item is __TOKENS__:N sentinel
        total_tokens = 0
        async for chunk in self.llm_provider.stream(prompt):
            if chunk.startswith("__TOKENS__:"):
                try:
                    total_tokens = int(chunk.split(":", 1)[1])
                except ValueError:
                    pass
                continue  # Don't forward sentinel to caller
            yield {
                "type": "chunk",
                "content": chunk
            }

        yield {
            "type": "done",
            "tokens_used": total_tokens + rewrite_tokens,
        }
