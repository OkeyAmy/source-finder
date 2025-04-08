from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.chat import ChatSession, Message, QueryRequest, QueryResponse
from app.memory.chat_memory import ChatMemoryManager
from app.core.source_finder import SourceFinder

router = APIRouter(prefix="/api/chats", tags=["chats"])
memory_manager = ChatMemoryManager()
source_finder = SourceFinder()

@router.post("/sessions", response_model=ChatSession)
async def create_session() -> ChatSession:
    """Create a new chat session.
    
    Returns:
        ChatSession: The newly created chat session.
    """
    return memory_manager.create_session()

@router.get("/sessions", response_model=List[ChatSession])
async def list_sessions() -> List[ChatSession]:
    """List all chat sessions.
    
    Returns:
        List[ChatSession]: List of all chat sessions.
    """
    return memory_manager.list_sessions()

@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(session_id: str) -> ChatSession:
    """Get a chat session by ID.
    
    Args:
        session_id: The ID of the session to retrieve.
        
    Returns:
        ChatSession: The chat session.
        
    Raises:
        HTTPException: If the session is not found.
    """
    session = memory_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete a chat session.
    
    Args:
        session_id: The ID of the session to delete.
        
    Returns:
        dict: A message indicating the session was deleted.
        
    Raises:
        HTTPException: If the session is not found.
    """
    if not memory_manager.delete_session(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted successfully"}

@router.post("/sessions/{session_id}/query", response_model=QueryResponse)
async def process_query(session_id: str, request: QueryRequest) -> QueryResponse:
    """Process a query in a chat session.
    
    Args:
        session_id: The ID of the session to process the query in.
        request: The query request.
        
    Returns:
        QueryResponse: The response to the query.
        
    Raises:
        HTTPException: If the session is not found.
    """
    session = memory_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Add user message to session
    user_message = Message(
        role="user",
        content=request.query,
        timestamp=request.timestamp
    )
    memory_manager.add_message(session_id, user_message)
    
    # Process query and get response
    response, sources = source_finder.process_query(request.query)
    
    # Add assistant message to session
    assistant_message = Message(
        role="assistant",
        content=response,
        sources=sources,
        timestamp=request.timestamp
    )
    memory_manager.add_message(session_id, assistant_message)
    
    return QueryResponse(
        response=response,
        sources=sources
    ) 