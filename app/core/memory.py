"""
Memory module for chat history management.
"""
from typing import List, Dict, Optional
import uuid
from datetime import datetime
from app.schemas.chat import Message, ChatSession

class ChatMemory:
    """
    Manages chat history and sessions.
    Provides methods to store, retrieve, and manage chat messages.
    """
    
    def __init__(self):
        """Initialize the chat memory store."""
        self.sessions: Dict[str, ChatSession] = {}
    
    def create_chat_session(self, session_id: Optional[str] = None) -> ChatSession:
        """
        Create a new chat session.
        
        Args:
            session_id: Optional session ID. If not provided, a new UUID will be generated.
            
        Returns:
            The newly created chat session.
        """
        if not session_id:
            session_id = str(uuid.uuid4())
            
        now = datetime.now()
        session = ChatSession(
            session_id=session_id,
            messages=[],
            created_at=now,
            updated_at=now,
            title="New Chat"  # Default title
        )
        
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """
        Get a chat session by ID.
        
        Args:
            session_id: The session ID to retrieve.
            
        Returns:
            The chat session if found, None otherwise.
        """
        return self.sessions.get(session_id)
    
    def add_message(self, session_id: str, message: Message) -> bool:
        """
        Add a message to a chat session.
        
        Args:
            session_id: The session ID to add the message to.
            message: The message to add.
            
        Returns:
            True if successful, False if session not found.
        """
        session = self.get_session(session_id)
        if not session:
            return False
            
        # Ensure timestamp is set
        if not message.timestamp:
            message.timestamp = datetime.now()
            
        session.messages.append(message)
        session.updated_at = datetime.now()
        
        # Update session title based on first user message if title is default
        if session.title == "New Chat" and message.role == "user" and len(session.messages) <= 1:
            # Truncate long titles
            session.title = (message.content[:30] + "...") if len(message.content) > 30 else message.content
            
        return True
    
    def get_chat_history(self, session_id: str) -> List[Message]:
        """
        Get all messages for a chat session.
        
        Args:
            session_id: The session ID to retrieve messages for.
            
        Returns:
            List of messages, empty list if session not found.
        """
        session = self.get_session(session_id)
        if not session:
            return []
        return session.messages
    
    def list_sessions(self) -> List[ChatSession]:
        """
        List all chat sessions.
        
        Returns:
            List of all chat sessions.
        """
        return list(self.sessions.values())
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a chat session.
        
        Args:
            session_id: The session ID to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def update_session_title(self, session_id: str, title: str) -> bool:
        """
        Update the title of a chat session.
        
        Args:
            session_id: The session ID to update.
            title: The new title.
            
        Returns:
            True if updated, False if session not found.
        """
        session = self.get_session(session_id)
        if not session:
            return False
            
        session.title = title
        session.updated_at = datetime.now()
        return True 