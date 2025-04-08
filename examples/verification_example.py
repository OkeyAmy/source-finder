"""
Example script demonstrating the verification features of the SourceFinder API.

This script shows how to use the API to verify information across multiple sources.
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API endpoint
API_URL = "http://localhost:8000"

def process_query_with_verification(query, verification_method="stimulated_verification"):
    """
    Process a query with verification.
    
    Args:
        query: The query to process
        verification_method: The verification method to use
        
    Returns:
        The API response
    """
    # Prepare request
    url = f"{API_URL}/api/process-query"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "query": query,
        "verify": True,
        "verification_method": verification_method
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

def print_verification_result(result):
    """
    Print the verification result in a readable format.
    
    Args:
        result: The API response
    """
    if not result or "verification" not in result:
        print("No verification result available")
        return
    
    verification = result["verification"]
    
    print("\n=== Verification Result ===")
    print(f"Verified: {'Yes' if verification['is_verified'] else 'No'}")
    print(f"Confidence Score: {verification['confidence_score']:.2f}")
    print(f"Verification Method: {verification['verification_method']}")
    
    print("\nSupporting Sources:")
    for source_id in verification["supporting_sources"]:
        source = next((s for s in result["sources"] if s["id"] == source_id), None)
        if source:
            print(f"- {source['title']} ({source['source_type']})")
    
    print("\nConflicting Sources:")
    for source_id in verification["conflicting_sources"]:
        source = next((s for s in result["sources"] if s["id"] == source_id), None)
        if source:
            print(f"- {source['title']} ({source['source_type']})")
    
    print("\nVerification Details:")
    for key, value in verification["verification_details"].items():
        if isinstance(value, float):
            print(f"- {key}: {value:.2f}")
        else:
            print(f"- {key}: {value}")

def main():
    """Main function."""
    # Example queries
    queries = [
        "What are the latest developments in renewable energy?",
        "What is the current state of climate change?",
        "What are the health benefits of intermittent fasting?"
    ]
    
    # Verification methods
    verification_methods = [
        "cross_reference",
        "fact_checking",
        "source_credibility",
        "temporal_analysis",
        "stimulated_verification"
    ]
    
    # Process each query with each verification method
    for query in queries:
        print(f"\n\n=== Query: {query} ===")
        
        for method in verification_methods:
            print(f"\n--- Verification Method: {method} ---")
            result = process_query_with_verification(query, method)
            
            if result:
                print("\nResponse:")
                print(result["response"])
                print_verification_result(result)
            else:
                print("Failed to process query")

if __name__ == "__main__":
    main() 