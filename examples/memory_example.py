"""
Example script demonstrating the memory functionality of the SourceFinder API.

This script shows how the API maintains conversation context between requests.
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API endpoint
API_URL = "http://localhost:8000"

def process_query(query: str, chat_id: str = None) -> dict:
    """
    Process a query and return the response.
    
    Args:
        query: The query to process
        chat_id: The chat ID to use (optional)
        
    Returns:
        The API response
    """
    # Prepare request
    url = f"{API_URL}/api/process-query"
    headers = {
        "Content-Type": "application/json"
    }
    
    # Add chat ID to headers if provided
    if chat_id:
        headers["X-Chat-ID"] = chat_id
    
    # Prepare data
    data = {
        "query": query,
        "verify": True
    }
    
    # Send request
    response = requests.post(url, headers=headers, json=data)
    
    # Parse response
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def get_chat_history(chat_id: str) -> list:
    """
    Get the conversation history for a chat.
    
    Args:
        chat_id: The chat ID to use
        
    Returns:
        The chat history
    """
    # Prepare request
    url = f"{API_URL}/api/chat/history"
    headers = {
        "X-Chat-ID": chat_id
    }
    
    # Send request
    response = requests.get(url, headers=headers)
    
    # Parse response
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

def main():
    """Main function."""
    print("=== SourceFinder API Memory Example ===")
    print("\nThis example demonstrates how the API maintains conversation context between requests.")
    
    # First query - no chat ID provided, API will create a new chat
    print("\n== First Query (New Chat) ==")
    query = "What are the latest developments in renewable energy?"
    result = process_query(query)
    
    if not result:
        print("Failed to process query")
        return
    
    # Extract chat ID from response
    chat_id = result["chat_id"]
    print(f"Chat ID: {chat_id}")
    print("\nResponse:")
    print(result["response"])
    
    # Second query in the same chat - context from first query is maintained
    print("\n== Second Query (Follow-up) ==")
    query = "Can you tell me more about solar energy specifically?"
    result = process_query(query, chat_id)
    
    if not result:
        print("Failed to process query")
        return
    
    print("\nResponse:")
    print(result["response"])
    
    # Third query with a reference to previous conversation
    print("\n== Third Query (With Reference) ==")
    query = "How does this compare to wind energy that you mentioned earlier?"
    result = process_query(query, chat_id)
    
    if not result:
        print("Failed to process query")
        return
    
    print("\nResponse:")
    print(result["response"])
    
    # Get chat history
    print("\n== Chat History ==")
    history = get_chat_history(chat_id)
    
    if not history:
        print("Failed to get chat history")
        return
    
    print(f"Message Count: {len(history)}")
    print("\nConversation:")
    for message in history:
        print(f"\n{message['role'].upper()}: {message['content']}")

if __name__ == "__main__":
    main() 