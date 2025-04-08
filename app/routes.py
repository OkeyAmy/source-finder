"""
API routes for the SourceFinder application.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from app.services.source_finder import SourceFinder
from app.schemas.chat import Message, QueryRequest, QueryResponse, ChatSession
from app.memory.chat_memory import ChatMemory
import uuid
from datetime import datetime

router = APIRouter()
source_finder = SourceFinder()
chat_memory = ChatMemory()

class SourcesRequest(BaseModel):
    session_id: str

class SourcesResponse(BaseModel):
    sources: List[Dict[str, Any]]

class ChatsRequest(BaseModel):
    query: Optional[str] = None
    messages: Optional[List[Message]] = None

class ChatsResponse(BaseModel):
    chats: List[Dict[str, Any]]

@router.post("/api/process-query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a user query and return a response with sources."""
    try:
        # Get session info - use provided session_id or current session, only create new if neither exists
        session_id = request.session_id
        if not session_id:
            # Try to get current session instead of creating a new one
            current_session = chat_memory.get_current_session()
            if current_session:
                session_id = current_session.session_id
                print(f"Using existing session: {session_id}")
            else:
                # Only create a new session if no session exists at all
                session_id = str(uuid.uuid4())
                print(f"Creating new session: {session_id}")
        
        # Get chat history for context if available
        chat_history = chat_memory.get_messages(session_id)
        
        # Extract source filters if provided
        source_filters = None
        if request.filters and "Sources" in request.filters:
            source_filters = request.filters["Sources"]
            # Validate source filters
            if isinstance(source_filters, list):
                # Filter is already a list, which is what we want
                pass
            elif isinstance(source_filters, str):
                # Convert single string to a list with one item
                source_filters = [source_filters]
            else:
                # Invalid format, log warning and don't apply filtering
                print(f"⚠️ Invalid Sources filter format: {type(source_filters)}")
                source_filters = None
            
            # Log the filters being applied
            if source_filters:
                print(f"🔍 Applying source filters: {source_filters}")
        
        try:
            # Process the query with the source finder
            response_text, sources = await source_finder.process_query(
                request.query, 
                chat_history=chat_history, 
                filters=source_filters
            )
        except Exception as source_error:
            # Handle source finder errors gracefully
            print(f"Error in source finder: {str(source_error)}")
            response_text = "I apologize, but I encountered an error while processing your query. Please try again or contact support if the issue persists."
            sources = []
        
        # Create a new message record
        user_message = Message(
            role="user",
            content=request.query,
            timestamp=datetime.now().isoformat()
        )
        
        assistant_message = Message(
            role="assistant",
            content=response_text,
            sources=sources,
            timestamp=datetime.now().isoformat()
        )
        
        # Save messages to chat memory
        chat_memory.add_message(session_id, user_message)
        chat_memory.add_message(session_id, assistant_message)
        
        # Return the response
        return QueryResponse(
            response={
                "content": response_text,
                "sources": sources
            }
        )
    except Exception as e:
        print(f"API error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.get("/api/sources", response_model=SourcesResponse)
async def get_sources(session_id: Optional[str] = Query(None)):
    """Get all sources for the current chat session."""
    try:
        # Use current session if available and no session_id provided
        if not session_id:
            # Try to get the current session ID from chat_memory
            current_session = chat_memory.get_current_session()
            if current_session:
                session_id = current_session.session_id
            else:
                # Return empty sources if no session available
                print("⚠️ No session ID provided and no current session available")
                return SourcesResponse(sources=[])
            
        # Get all messages for the session
        messages = chat_memory.get_messages(session_id)
        
        # Extract all sources from assistant messages
        all_sources = []
        for message in messages:
            if message.role == "assistant" and message.sources:
                all_sources.extend(message.sources)
        
        print(f"✅ Found {len(all_sources)} sources for session {session_id}")
        return SourcesResponse(sources=all_sources)
    except Exception as e:
        print(f"❌ Error retrieving sources: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving sources: {str(e)}")

@router.post("/api/chats", response_model=ChatsResponse)
async def create_chat(request: ChatsRequest, refresh: bool = Query(False)):
    """Create a new chat or add to an existing chat."""
    try:
        # Generate a new session ID only if refresh is True or no current session exists
        if refresh:
            # Force creation of a new session
            session_id = str(uuid.uuid4())
            print(f"Creating new session (refresh requested): {session_id}")
        else:
            # Check if there's a current session
            current_session = chat_memory.get_current_session()
            if current_session:
                # Use existing session
                session_id = current_session.session_id
                print(f"Using existing session: {session_id}")
            else:
                # Create new session only if none exists
                session_id = str(uuid.uuid4())
                print(f"Creating new session (none exists): {session_id}")
        
        # If we have a query and messages, create a new chat
        if request.query:
            # Create user message
            user_message = Message(
                role="user",
                content=request.query,
                timestamp=datetime.now().isoformat()
            )
            chat_memory.add_message(session_id, user_message)
            
            # Process with source finder
            try:
                response_text, sources = await source_finder.process_query(
                    request.query,
                    chat_history=request.messages
                )
                
                # Create assistant message
                assistant_message = Message(
                    role="assistant",
                    content=response_text,
                    sources=sources,
                    timestamp=datetime.now().isoformat()
                )
                chat_memory.add_message(session_id, assistant_message)
            except Exception as e:
                print(f"Error processing query: {str(e)}")
                # Still create the chat even if processing failed
                pass
        
        # If we have messages, add them to the chat
        if request.messages:
            for message in request.messages:
                chat_memory.add_message(session_id, message)
        
        # Return list of all chats
        return await list_chats()
    except Exception as e:
        print(f"Error creating chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating chat: {str(e)}")

@router.get("/api/chats", response_model=ChatsResponse)
async def list_chats():
    """List all chat sessions."""
    try:
        # Get all chat sessions
        sessions = chat_memory.get_all_sessions()
        
        # Format the response
        chats = []
        for session_id in sessions:
            chats.append({
                "title": chat_memory.get_session_title(session_id),
                "updatedAt": chat_memory.get_session_update_time(session_id)
            })
        
        return ChatsResponse(chats=chats)
    except Exception as e:
        print(f"Error listing chats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing chats: {str(e)}")

@router.get("/api/current-session")
async def get_current_session():
    """Get the current session ID."""
    try:
        current_session = chat_memory.get_current_session()
        if current_session:
            return {
                "session_id": current_session.session_id,
                "title": chat_memory.get_session_title(current_session.session_id),
                "updated_at": current_session.updated_at
            }
        else:
            return {"session_id": None, "message": "No active session"}
    except Exception as e:
        print(f"❌ Error getting current session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting current session: {str(e)}") 