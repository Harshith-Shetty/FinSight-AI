"""
Chat management service for creating and managing chat sessions.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import Chat, Message, ChatMode
from app.services.llm.groq_provider import GroqProvider


class ChatService:
    """Service for managing chat sessions."""
    
    def __init__(self):
        self.llm_provider = GroqProvider()
    
    async def create_chat(
        self,
        db: AsyncSession,
        user_id: UUID,
        mode: ChatMode,
        title: Optional[str] = None
    ) -> Chat:
        """
        Create a new chat session.
        
        Args:
            db: Database session
            user_id: User ID
            mode: Chat mode (hybrid or private)
            title: Optional chat title (will be auto-generated if None)
        
        Returns:
            Created chat object
        """
        chat = Chat(
            user_id=user_id,
            mode=mode,
            title=title or "New Chat"  # Will be updated after first message
        )
        
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        
        return chat
    
    async def get_user_chats(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50
    ) -> List[Chat]:
        """
        Get all chats for a user.
        
        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number of chats to return
        
        Returns:
            List of chat objects
        """
        result = await db.execute(
            select(Chat)
            .where(Chat.user_id == user_id, Chat.is_deleted == False)
            .order_by(Chat.updated_at.desc())
            .limit(limit)
        )
        
        return result.scalars().all()
    
    async def get_chat(
        self,
        db: AsyncSession,
        chat_id: UUID,
        user_id: UUID
    ) -> Optional[Chat]:
        """
        Get a specific chat by ID.
        
        Args:
            db: Database session
            chat_id: Chat ID
            user_id: User ID (for authorization)
        
        Returns:
            Chat object or None if not found
        """
        result = await db.execute(
            select(Chat)
            .where(Chat.id == chat_id, Chat.user_id == user_id, Chat.is_deleted == False)
        )
        
        return result.scalar_one_or_none()
    
    async def delete_chat(
        self,
        db: AsyncSession,
        chat_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a chat and all its messages.
        
        Args:
            db: Database session
            chat_id: Chat ID
            user_id: User ID (for authorization)
        
        Returns:
            True if deleted, False if not found
        """
        chat = await self.get_chat(db, chat_id, user_id)
        
        if not chat:
            return False
        
        chat.is_deleted = True
        await db.commit()
        
        return True
    
    async def generate_chat_title(self, first_message: str) -> str:
        """
        Generate a chat title from the first message using LLM.
        
        Args:
            first_message: First user message in the chat
        
        Returns:
            Generated title (max 50 chars)
        """
        prompt = f"""Generate a short, descriptive title (max 5 words) for a chat that starts with this message:

"{first_message}"

Return ONLY the title, nothing else."""
        
        try:
            title = await self.llm_provider.generate(prompt)
            # Clean and truncate
            title = title.strip().strip('"').strip("'")
            return title[:50]
        except Exception:
            # Fallback to truncated message
            return first_message[:50] + "..." if len(first_message) > 50 else first_message
    
    async def update_chat_title(
        self,
        db: AsyncSession,
        chat_id: UUID,
        title: str
    ):
        """
        Update chat title.
        
        Args:
            db: Database session
            chat_id: Chat ID
            title: New title
        """
        result = await db.execute(
            select(Chat).where(Chat.id == chat_id)
        )
        chat = result.scalar_one_or_none()
        
        if chat:
            chat.title = title
            await db.commit()
    
    async def get_chat_messages(
        self,
        db: AsyncSession,
        chat_id: UUID,
        user_id: UUID,
        limit: int = 100
    ) -> List[Message]:
        """
        Get all messages for a chat.
        
        Args:
            db: Database session
            chat_id: Chat ID
            user_id: User ID (for authorization)
            limit: Maximum number of messages
        
        Returns:
            List of messages
        """
        # Verify user owns the chat
        chat = await self.get_chat(db, chat_id, user_id)
        if not chat:
            return []
        
        result = await db.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        
        return result.scalars().all()
