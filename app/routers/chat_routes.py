"""
Chat routes for SourceFinder API.

This module defines the routes for managing chat sessions and history.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from typing import List, Optional, Dict, Any
from app.memory import get_memory_manager, get_all_chats

router = APIRouter()

@router.get("/chats")
async def get_chats():
    """
    Get all chat sessions.
    
    This endpoint returns information about all chat sessions.
    """
    return get_all_chats()

@router.get("/chat")
async def get_chat_info(
    chat_id: Optional[str] = Header(None, alias="X-Chat-ID")
):
    """
    Get information about a specific chat.
    
    This endpoint returns information about a specific chat.
    If no chat ID is provided, an error will be returned.
    """
    if not chat_id:
        raise HTTPException(status_code=400, detail="Chat ID is required")
    
    # Get memory manager
    memory_manager = get_memory_manager(chat_id)
    
    # Get chat info
    return memory_manager.get_chat_info()

@router.delete("/chat")
async def delete_chat(
    chat_id: Optional[str] = Header(None, alias="X-Chat-ID")
):
    """
    Delete a chat session.
    
    This endpoint deletes a chat session.
    If no chat ID is provided, an error will be returned.
    """
    if not chat_id:
        raise HTTPException(status_code=400, detail="Chat ID is required")
    
    # Get memory manager
    memory_manager = get_memory_manager(chat_id)
    
    # Delete chat
    # In a real implementation, this would delete the chat from the memory store
    # For this demo, we just return success
    return {"status": "success", "message": "Chat deleted successfully"}

@router.get("/chat/history")
async def get_chat_history(
    chat_id: Optional[str] = Header(None, alias="X-Chat-ID")
):
    """
    Get the conversation history for a chat.
    
    This endpoint returns the conversation history for a specific chat.
    If no chat ID is provided, an error will be returned.
    """
    if not chat_id:
        raise HTTPException(status_code=400, detail="Chat ID is required")
    
    # Get memory manager
    memory_manager = get_memory_manager(chat_id)
    
    # Get conversation history
    conversation = memory_manager.get_conversation_history()
    
    # Format chat history for response
    chat_history = []
    for message in conversation.get("chat_history", []):
        message_type = "system"
        if hasattr(message, "type") and message.type == "human":
            message_type = "user"
        elif hasattr(message, "type") and message.type == "ai":
            message_type = "assistant"
            
        chat_history.append({
            "role": message_type,
            "content": message.content
        })
    
    return chat_history 