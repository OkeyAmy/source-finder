"""
Chat memory management module for storing and retrieving chat history.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import os
from pathlib import Path
import uuid

from app.schemas.chat import Message, ChatSession

class ChatMemory:
    """In-memory store for chat sessions and messages."""
    
    def __init__(self):
        """Initialize the chat memory store."""
        self.sessions: Dict[str, ChatSession] = {}
        self.current_session_id = None
    
    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new chat session."""
        if not session_id:
            session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = ChatSession(
            session_id=session_id,
            messages=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Set as current session
        self.current_session_id = session_id
        
        return session_id
    
    def get_current_session(self) -> Optional[ChatSession]:
        """Get the current chat session."""
        if not self.current_session_id or self.current_session_id not in self.sessions:
            return None
        
        return self.sessions[self.current_session_id]
    
    def add_message(self, session_id: str, message: Message) -> bool:
        """Add a message to a chat session."""
        # Create session if it doesn't exist
        if session_id not in self.sessions:
            self.create_session(session_id)
        
        # Add message and update timestamp
        session = self.sessions[session_id]
        session.messages.append(message)
        session.updated_at = datetime.now().isoformat()
        
        # Update current session
        self.current_session_id = session_id
        
        return True
    
    def get_messages(self, session_id: str) -> List[Message]:
        """Get all messages for a chat session."""
        if session_id not in self.sessions:
            return []
        
        return self.sessions[session_id].messages
    
    def get_all_sessions(self) -> List[str]:
        """Get all session IDs."""
        return list(self.sessions.keys())
    
    def get_session_title(self, session_id: str) -> str:
        """Get the title for a chat session."""
        if session_id not in self.sessions:
            return "New Chat"
        
        # Use first user message as title, or default if none exists
        session = self.sessions[session_id]
        for message in session.messages:
            if message.role == "user":
                # Truncate if too long
                title = message.content
                if len(title) > 50:
                    title = title[:50] + "..."
                return title
        
        return "New Chat"
    
    def get_session_update_time(self, session_id: str) -> str:
        """Get the update time for a chat session."""
        if session_id not in self.sessions:
            return datetime.now().isoformat()
        
        return self.sessions[session_id].updated_at
    
    def clear_session(self, session_id: str) -> bool:
        """Clear all messages from a chat session."""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id].messages = []
        self.sessions[session_id].updated_at = datetime.now().isoformat()
        
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session."""
        if session_id not in self.sessions:
            return False
        
        del self.sessions[session_id]
        
        # Update current session if this was the current one
        if self.current_session_id == session_id:
            self.current_session_id = None
        
        return True
        
    def get_sources(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all sources from all messages in a session.
        
        Args:
            session_id: Optional session ID. If None, uses the current session.
            
        Returns:
            List of source dictionaries
        """
        # Use current session if no session_id provided
        if not session_id:
            if not self.current_session_id:
                return []
            session_id = self.current_session_id
        
        # Check if session exists
        if session_id not in self.sessions:
            return []
        
        # Extract sources from all messages
        sources = []
        for message in self.sessions[session_id].messages:
            if message.role == "assistant" and message.sources:
                sources.extend(message.sources)
        
        return sources
        
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all chat sessions.
        
        Returns:
            List of session summaries
        """
        sessions = []
        for session_id, session in self.sessions.items():
            last_message = ""
            if session.messages:
                last_message = session.messages[-1].content
            
            sessions.append({
                "session_id": session_id,
                "title": self.get_session_title(session_id),
                "last_message": last_message,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            })
        
        # Sort by update time, most recent first
        return sorted(sessions, key=lambda x: x["updated_at"], reverse=True) 