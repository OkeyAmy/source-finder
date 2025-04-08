# SourceFinder API

A powerful API that searches and aggregates information from various sources including Reddit, Twitter, Web, News, and Academic sources. This API uses LangChain and Google's Gemini model to process queries and return relevant responses with cited sources.

## Table of Contents

- [API Overview](#api-overview)
- [Endpoint Reference](#endpoint-reference)
  - [Process Query](#process-query)
  - [Get Sources](#get-sources)
  - [Manage Chats](#manage-chats)
  - [Get Current Session](#get-current-session)
  - [API Info](#api-info)
- [Deployment Guide](#deployment-guide)
  - [Deploying on Render](#deploying-on-render)
  - [Setting up Playwright](#setting-up-playwright)
- [Environment Variables](#environment-variables)

## API Overview

The SourceFinder API allows you to query multiple information sources simultaneously and receive a consolidated response with citations. It maintains chat history for context and allows filtering sources to customize your information retrieval.

## Endpoint Reference

### Process Query

**POST `/api/process-query`**

Process a user query and return a response with sources.

**Request:**

```json
{
  "query": "string",
  "session_id": "string (optional)",
  "filters": {
    "Sources": ["Reddit", "Twitter", "Web", "News", "Academic"]
  }
}
```

**Parameters:**
- `query`: The user's question or request
- `session_id`: (Optional) Session ID for maintaining conversation context
- `filters`: (Optional) Source filter configuration
  - `Sources`: Array of sources to include (options: "Reddit", "Twitter", "Web", "News", "Academic")

**Response:**

```json
{
  "response": {
    "content": "string",
    "sources": [
      {
        "num": 1,
        "title": "Source Title",
        "link": "https://source-url.com",
        "source": "Web",
        "preview": "Preview text of source content...",
        "images": ["https://image-url.com/image.jpg"],
        "logo": "https://favicon-url.com/favicon.ico"
      }
    ]
  }
}
```

**Example:**

```bash
curl -X POST "http://localhost:8000/api/process-query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Latest developments in AI",
    "filters": {
      "Sources": ["Academic", "News"]
    }
  }'
```

### Get Sources

**GET `/api/sources`**

Retrieve all sources used in the current session or a specific session.

**Parameters:**
- `session_id`: (Optional query parameter) Session ID to retrieve sources from

**Response:**

```json
{
  "sources": [
    {
      "num": 1,
      "title": "Source Title",
      "link": "https://source-url.com",
      "source": "Web",
      "preview": "Preview text of source content...",
      "images": ["https://image-url.com/image.jpg"],
      "logo": "https://favicon-url.com/favicon.ico"
    }
  ]
}
```

**Example:**

```bash
# Get sources for the current session
curl "http://localhost:8000/api/sources"

# Get sources for a specific session
curl "http://localhost:8000/api/sources?session_id=123e4567-e89b-12d3-a456-426614174000"
```

### Manage Chats

**GET `/api/chats`**

List all chat sessions.

**Response:**

```json
{
  "chats": [
    {
      "title": "Chat title (derived from first message)",
      "updatedAt": "2023-07-01T10:30:45.123Z"
    }
  ]
}
```

**POST `/api/chats`**

Create a new chat session or add to an existing chat.

**Request:**

```json
{
  "query": "string (optional)",
  "messages": [
    {
      "role": "user | assistant",
      "content": "string",
      "sources": [] 
    }
  ]
}
```

**Parameters:**
- `refresh`: Boolean query parameter (default: false) - Set to true to force creation of a new session

**Response:**
Same as the GET `/api/chats` response, returning an updated list of all chats.

**Example:**

```bash
# Create new chat session
curl -X POST "http://localhost:8000/api/chats" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about quantum computing"
  }'

# Force create a new session (refresh)
curl -X POST "http://localhost:8000/api/chats?refresh=true" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Tell me about quantum computing"
  }'
```

### Get Current Session

**GET `/api/current-session`**

Get information about the currently active session.

**Response:**

```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Session title",
  "updated_at": "2023-07-01T10:30:45.123Z"
}
```

Or if no active session:

```json
{
  "session_id": null,
  "message": "No active session"
}
```

### API Info

**GET `/`**

Get basic information about the API.

**Response:**

```json
{
  "name": "SourceFinder API",
  "version": "1.0.0",
  "description": "API for finding and processing information from various sources",
  "documentation": "/docs"
}
```

**GET `/health`**

Health check endpoint.

**Response:**

```json
{
  "status": "healthy"
}
```

## Deployment Guide

### Deploying on Render

To deploy this API on Render:

1. Sign up for a [Render account](https://render.com/)
2. Create a new Web Service and connect to your GitHub repository
3. Configure your service with the following settings:

   - **Build Command**: `pip install -r requirements.txt && playwright install --with-deps`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables**: Set all [required environment variables](#environment-variables)

4. Select an appropriate instance type (at least 1GB RAM recommended)
5. Set the region and click "Create Web Service"

### Setting up Playwright

For Playwright to work properly on Render, you need to:

1. Ensure you install Playwright with dependencies in your build command:
   ```
   playwright install --with-deps
   ```

2. Add the following to your `requirements.txt`:
   ```
   playwright>=1.30.0
   ```

3. Create a `render-build.sh` script in your repository:
   ```bash
   #!/usr/bin/env bash
   # Install Playwright system dependencies
   apt-get update
   apt-get install -y libgtk-3-0 libdbus-glib-1-2 libxt6 libxaw7 libnss3 libnspr4 libpcre3 libasound2 libxdamage1 libgbm1 libxfixes3
   
   # Install Playwright browsers
   python -m playwright install chromium
   ```

4. Update your Render build command to run this script:
   ```
   chmod +x render-build.sh && ./render-build.sh && pip install -r requirements.txt
   ```

## Environment Variables

This application requires the following environment variables:

- `GOOGLE_AI_API_KEY`: Google Generative AI API key
- `REDDIT_CLIENT_ID`: Reddit API client ID
- `REDDIT_CLIENT_SECRET`: Reddit API client secret
- `REDDIT_USER_AGENT`: Custom user agent for Reddit API
- `TWITTER_BEARER_TOKEN`: Twitter API bearer token
- `NEWS_API_KEY`: NewsAPI.org API key
- `SERP_API_KEY`: SerpAPI key for web searches

## Development

To run the API locally:

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Install Playwright browsers: `playwright install`
4. Set up environment variables in a `.env` file
5. Run the application: `python run.py`
6. Access the API at `http://localhost:8000` 