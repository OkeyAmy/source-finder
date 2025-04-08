"""
Models package for SourceFinder API.

This package contains the Pydantic models used by the SourceFinder API.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SourceReference(BaseModel):
    """
    Model for source references.
    
    This model defines the structure of source references.
    """
    id: str = Field(..., description="The source ID")
    title: str = Field(..., description="The source title")
    link: str = Field(..., description="The source link")
    snippet: str = Field(..., description="The source snippet")
    source_type: str = Field(..., description="The source type")

class ChatMessage(BaseModel):
    """
    Model for chat messages.
    
    This model defines the structure of chat messages.
    """
    role: str = Field(..., description="The message role (user, assistant, system)")
    content: str = Field(..., description="The message content")
    sources: Optional[List[SourceReference]] = Field(None, description="The sources used in the message")

class ChatSummary(BaseModel):
    """
    Model for chat summaries.
    
    This model defines the structure of chat summaries.
    """
    id: str = Field(..., description="The chat ID")
    created_at: str = Field(..., description="The chat creation timestamp")
    updated_at: str = Field(..., description="The chat update timestamp")
    message_count: int = Field(..., description="The number of messages in the chat") 