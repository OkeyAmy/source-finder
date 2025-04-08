from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    """Model representing a reference source"""
    num: int
    title: str
    link: str
    source: str
    preview: Optional[str] = None
    images: Optional[List[str]] = []
    logo: Optional[str] = None


class QueryFilters(BaseModel):
    """Filters for specifying which sources to use in a query"""
    sources: Optional[List[str]] = Field(
        default=["Web", "News", "Twitter", "Academic", "Reddit"],
        description="Which sources to use in the search"
    )


class QueryRequest(BaseModel):
    """Request model for processing queries"""
    query: str
    filters: Optional[QueryFilters] = None


class ChatMessage(BaseModel):
    """Individual chat message model"""
    role: str = Field(..., description="Either 'user' or 'assistant'")
    content: str
    sources: Optional[List[SourceReference]] = []
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
    """Request model for chat interactions"""
    query: str
    messages: Optional[List[ChatMessage]] = []


class ChatSummary(BaseModel):
    """Summary of a chat session"""
    id: str
    title: str
    updatedAt: datetime


class ChatResponse(BaseModel):
    """Response model for chat listings"""
    chats: List[ChatSummary]


class SourceResponse(BaseModel):
    """Response model for source listings"""
    sources: List[SourceReference]


class QueryResult(BaseModel):
    """Result model for processed queries"""
    content: str
    sources: List[SourceReference]


class QueryResponse(BaseModel):
    """Response model for processed queries"""
    response: QueryResult 
