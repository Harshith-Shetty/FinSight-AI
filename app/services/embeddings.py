"""
Embedding generation using sentence-transformers.
"""

from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np


class EmbeddingGenerator:
    """
    Generates embeddings for text chunks using sentence-transformers.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding model.
        
        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2)
                       This model produces 384-dimensional embeddings
        """
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # all-MiniLM-L6-v2 dimension
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Input text to chunk
            chunk_size: Number of tokens per chunk
            overlap: Number of overlapping tokens between chunks
            
        Returns:
            List of text chunks
        """
        # Simple word-based chunking (in production, use proper tokenization)
        words = text.split()
        chunks = []

        # Guard against a non-positive stride (overlap >= chunk_size) raising/ looping
        step = max(1, chunk_size - overlap)

        for i in range(0, len(words), step):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)

        return chunks
    
    async def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings
            
        Returns:
            Numpy array of embeddings (shape: [len(texts), 384])
        """
        # sentence-transformers is CPU-bound, but we can batch process
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        return embeddings
