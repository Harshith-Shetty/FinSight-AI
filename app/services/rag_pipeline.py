"""
RAG pipeline orchestration.
Coordinates data fetching, embedding, retrieval, and LLM synthesis.
"""

from typing import Dict, Any
import json

from app.services.data_ingestion import SECDataFetcher
from app.services.embeddings import EmbeddingGenerator
from app.services.vector_store import QdrantVectorStore
from app.services.llm.factory import get_llm_provider


class RAGPipeline:
    """
    Orchestrates the complete RAG workflow for financial analysis.
    """
    
    def __init__(self):
        """Initialize RAG pipeline components."""
        self.data_fetcher = SECDataFetcher()
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = QdrantVectorStore()
        self.llm_provider = get_llm_provider()
    
    async def analyze(
        self,
        ticker: str,
        focus_area: str,
        filing_year: int
    ) -> Dict[str, Any]:
        """
        Execute full RAG pipeline for financial analysis.
        
        Args:
            ticker: Stock ticker symbol
            focus_area: Analysis focus (e.g., "risk_factors")
            filing_year: Year of SEC filing
            
        Returns:
            Structured analysis results
        """
        # Step 1: Fetch SEC filing
        filing_text = await self.data_fetcher.fetch_10k(ticker, filing_year)
        
        # Step 2: Chunk document
        chunks = self.embedding_generator.chunk_text(filing_text)
        
        # Step 3: Generate embeddings
        embeddings = await self.embedding_generator.generate_embeddings(chunks)
        
        # Step 4: Store in Qdrant
        await self.vector_store.upsert_vectors(
            ticker=ticker,
            year=filing_year,
            chunks=chunks,
            embeddings=embeddings
        )
        
        # Step 5: Create query based on focus area
        query = self._build_query(ticker, focus_area)
        
        # Step 6: Generate query embedding
        query_embedding = await self.embedding_generator.generate_embeddings([query])
        
        # Step 7: Retrieve relevant chunks
        relevant_chunks = await self.vector_store.search(
            query_embedding=query_embedding[0],
            ticker=ticker,
            year=filing_year,
            top_k=5
        )
        
        # Step 8: Build context from retrieved chunks
        context = self._build_context(relevant_chunks)
        
        # Step 9: Generate LLM response
        llm_response = await self.llm_provider.generate(
            prompt=query,
            context=context,
            temperature=0.3,
            max_tokens=1000
        )
        
        # Step 10: Parse and return results
        return self._parse_llm_response(llm_response, ticker)
    
    def _build_query(self, ticker: str, focus_area: str) -> str:
        """Build query based on focus area."""
        focus_queries = {
            "risk_factors": f"What are the key risk factors for {ticker}?",
            "financials": f"Summarize the financial performance of {ticker}.",
            "general": f"Provide an overview of {ticker}'s business and operations."
        }
        return focus_queries.get(focus_area, focus_queries["general"])
    
    def _build_context(self, chunks: list) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []
        for idx, chunk in enumerate(chunks, 1):
            context_parts.append(f"[Excerpt {idx}]\n{chunk['text']}\n")
        return "\n".join(context_parts)
    
    def _parse_llm_response(self, response: str, ticker: str) -> Dict[str, Any]:
        """Parse LLM JSON response."""
        try:
            parsed = json.loads(response)
            # Ensure ticker is included
            parsed["ticker"] = ticker
            return parsed
        except json.JSONDecodeError:
            # Fallback if LLM doesn't return valid JSON
            return {
                "ticker": ticker,
                "summary": response,
                "key_risks": [],
                "sentiment_score": 0.0,
                "citations": []
            }
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.data_fetcher.close()
