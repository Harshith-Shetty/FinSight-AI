"""
Document processing service for parsing PDF, TXT, and DOCX files.
"""

from typing import List
import os
from PyPDF2 import PdfReader
from docx import Document


class DocumentProcessor:
    """Service for parsing and processing different document formats."""
    
    @staticmethod
    def parse_pdf(file_path: str) -> str:
        """
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            reader = PdfReader(file_path)
            text = ""
            
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")
    
    @staticmethod
    def parse_txt(file_path: str) -> str:
        """
        Read text from TXT file.
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            File content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read().strip()
        except Exception as e:
            raise ValueError(f"Failed to parse TXT: {str(e)}")
    
    @staticmethod
    def parse_docx(file_path: str) -> str:
        """
        Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text content
        """
        try:
            doc = Document(file_path)
            text = ""
            
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        except Exception as e:
            raise ValueError(f"Failed to parse DOCX: {str(e)}")
    
    @staticmethod
    def parse_document(file_path: str, file_type: str) -> str:
        """
        Parse document based on file type.
        
        Args:
            file_path: Path to document
            file_type: File extension (pdf, txt, docx)
            
        Returns:
            Extracted text content
        """
        file_type = file_type.lower().replace('.', '')
        
        if file_type == 'pdf':
            return DocumentProcessor.parse_pdf(file_path)
        elif file_type in ('txt', 'md'):
            return DocumentProcessor.parse_txt(file_path)
        elif file_type == 'docx':
            return DocumentProcessor.parse_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Target chunk size in tokens (approximate)
            overlap: Number of tokens to overlap between chunks
            
        Returns:
            List of text chunks
        """
        # Simple word-based chunking (approximation)
        words = text.split()
        chunks = []
        
        i = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunks.append(' '.join(chunk_words))
            i += chunk_size - overlap
        
        return chunks
