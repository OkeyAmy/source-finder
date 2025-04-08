"""
Pydantic models for chat data.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class Message(BaseModel):
    """Chat message model."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    sources: Optional[List[Dict[str, Any]]] = None

class Source(BaseModel):
    """Source reference model."""
    title: str
    link: str
    source: str
    snippet: Optional[str] = None
    media: Optional[List[str]] = None
    logo: Optional[str] = None

class QueryRequest(BaseModel):
    """Request model for process-query endpoint."""
    query: str
    session_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = Field(
        None, 
        description="Filter settings for sources. Use 'Sources' key with a list of source types to include (e.g., 'Reddit', 'Twitter', 'Web', 'News', 'Academic')"
    )

class ResponseContent(BaseModel):
    """Response content model."""
    content: str
    sources: List[Dict[str, Any]]

class QueryResponse(BaseModel):
    """Response model for process-query endpoint."""
    response: ResponseContent

class ChatSummary(BaseModel):
    """Summary of a chat session."""
    title: str
    updatedAt: datetime

class ChatListResponse(BaseModel):
    """Response model for list of chats."""
    chats: List[ChatSummary]

class ChatSession(BaseModel):
    """Chat session model."""
    session_id: str
    messages: List[Message] = []
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class ChatRequest(BaseModel):
    """Request model for creating or updating a chat."""
    query: Optional[str] = None
    messages: Optional[List[Message]] = None 