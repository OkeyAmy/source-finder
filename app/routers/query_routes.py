"""
Query routes for SourceFinder API.

This module defines the routes for processing queries and retrieving sources.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List, Optional, Dict, Any
from app.models.query_models import QueryRequest, QueryResponse, SourceResponse
from app.source_finder import SourceFinder
from app.memory import get_memory_manager
from app.verification import SourceVerifier

router = APIRouter()
source_finder = SourceFinder()
source_verifier = SourceVerifier()

@router.post("/process-query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    chat_id: Optional[str] = Header(None, alias="X-Chat-ID")
):
    """
    Process a query and return a response with sources.
    
    This endpoint takes a query and returns a response with sources.
    If a chat ID is provided, the query will be processed in the context of that chat.
    If no chat ID is provided, a new chat will be created.
    """
    # Get memory manager
    memory_manager = get_memory_manager(chat_id)
    
    # Process query
    response, sources = source_finder.process_query(request.query, memory_manager)
    
    # Verify information if requested
    verification_result = None
    if request.verify:
        verification_result = source_verifier.verify_information(
            response, 
            sources,
            method=request.verification_method or "stimulated_verification"
        )
    
    # Return response
    return QueryResponse(
        response=response,
        sources=sources,
        chat_id=memory_manager.chat_id,
        verification=verification_result
    )

@router.get("/sources", response_model=List[SourceResponse])
async def get_sources(
    chat_id: Optional[str] = Header(None, alias="X-Chat-ID")
):
    """
    Get all sources used in the current chat session.
    
    This endpoint returns all sources used in the current chat session.
    If no chat ID is provided, an empty list will be returned.
    """
    # Get memory manager
    memory_manager = get_memory_manager(chat_id)
    
    # Get sources from memory
    sources = memory_manager.get_sources()
    
    # Return sources
    return sources 