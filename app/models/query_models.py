"""
Query models for SourceFinder API.

This module defines the Pydantic models for query requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from app.verification import VerificationResult

class QueryRequest(BaseModel):
    """
    Model for query requests.
    
    This model defines the structure of query requests.
    """
    query: str = Field(..., description="The query to process")
    verify: bool = Field(False, description="Whether to verify the information")
    verification_method: Optional[str] = Field(
        None, 
        description="The verification method to use (cross_reference, fact_checking, source_credibility, temporal_analysis, stimulated_verification)"
    )

class SourceResponse(BaseModel):
    """
    Model for source responses.
    
    This model defines the structure of source responses.
    """
    id: str = Field(..., description="The source ID")
    title: str = Field(..., description="The source title")
    link: str = Field(..., description="The source link")
    snippet: str = Field(..., description="The source snippet")
    date: Optional[str] = Field(None, description="The source date")
    source_type: str = Field(..., description="The source type (web, news, twitter, reddit, academic)")

class QueryResponse(BaseModel):
    """
    Model for query responses.
    
    This model defines the structure of query responses.
    """
    response: str = Field(..., description="The response to the query")
    sources: List[SourceResponse] = Field(..., description="The sources used to generate the response")
    chat_id: str = Field(..., description="The chat ID")
    verification: Optional[VerificationResult] = Field(None, description="The verification result") 