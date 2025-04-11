"""
SourceFinder module for finding and verifying information from multiple sources.
"""

import os
import re
import time
import json
import arxiv
import asyncio
import aiohttp
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
from typing import Dict, Any, List, AsyncGenerator, Tuple, Optional
from bs4 import BeautifulSoup
from google import genai
from google.genai.types import GenerateContentConfig, Tool, HarmCategory, HarmBlockThreshold, SafetySetting
import tweepy
import asyncpraw
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
MODEL_ID = "models/gemini-2.0-flash"
SAFETY_SETTINGS = [
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
    ),
]

class SourceFinder:
    """Service for processing queries and finding relevant sources."""
    
    def __init__(self):
        """Initialize the source finder with necessary components."""
        self.genai_client = None
        self.genai_configured = False
        self.source_references = []
        self.search_times = {}
        self.session = None  # Persistent aiohttp session
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
        
        # Define the prompt template
        template = """You are a helpful AI assistant that provides accurate information and cites sources.
        
        Current conversation:
        {chat_history}
        
        Human: {input}
        Assistant: Let me help you with that. I'll provide information and cite relevant sources.
        
        Response:"""
        
        prompt = PromptTemplate(
            input_variables=["chat_history", "input"],
            template=template
        )
        
        # Initialize the conversation chain
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if api_key:
            try:
                # Use the proper LangChain integration for Google Generative AI
                llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-pro",
                    google_api_key=api_key,
                    temperature=0.2,
                    convert_system_message_to_human=True
                )
                
                # Fix the chain creation using the correct pattern
                from langchain.chains.conversation.base import ConversationChain
                
                self.chain = ConversationChain(
                    llm=llm,
                    memory=self.memory,
                    prompt=prompt,
                    verbose=True
                )
                
                self.genai_configured = True
                print("✅ LangChain with GenAI configured successfully")
            except Exception as e:
                print(f"❌ Error configuring LangChain with Gen AI: {e}")
                self.genai_configured = False
        else:
            print("❌ GOOGLE_AI_API_KEY missing")
            self.genai_configured = False
        
        # Configure Google Gen AI for direct API calls
        if api_key:
            try:
                self.genai_client = genai.Client(api_key=api_key)
                print("✅ GenAI API configured successfully")
            except Exception as e:
                print(f"❌ Error configuring Gen AI: {e}")
        
        # Initialize APIs
        self._init_twitter()
        self._init_reddit()
    
    def _init_twitter(self):
        """Initialize Twitter API client"""
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        if bearer_token:
            try:
                self.twitter = tweepy.Client(bearer_token=bearer_token, wait_on_rate_limit=False)
                print("✅ Twitter API configured successfully")
            except Exception as e:
                print(f"❌ Twitter error: {e}")
                self.twitter = None
        else:
            print("❌ TWITTER_BEARER_TOKEN missing")
            self.twitter = None
    
    def _init_reddit(self):
        """Initialize Reddit API client"""
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "SourceFinder/1.0")
        
        if client_id and client_secret:
            try:
                self.reddit = asyncpraw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent
                )
                print("✅ Reddit API configured successfully")
            except Exception as e:
                print(f"❌ Reddit error: {e}")
                self.reddit = None
        else:
            print("❌ Reddit credentials missing")
            self.reddit = None
    
    async def create_session(self):
        """Create persistent aiohttp session"""
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"User-Agent": "SourceFinder/1.0"}
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session if open"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def get_sources(self, query: str, source_filters: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get sources for a query from multiple platforms.
        
        Args:
            query: The user's query string
            source_filters: Optional list of source types to include
            
        Returns:
            Dictionary of sources by platform
        """
        try:
            # Generate platform-specific queries
            platform_queries = await self._read_query(query)
            
            # Filter sources if specified
            if source_filters:
                platform_queries = {k: v for k, v in platform_queries.items() if k in source_filters}
            
            # Get sources from all platforms
            sources = await self.get_all_sources(platform_queries)
            
            return sources
        except Exception as e:
            print(f"Error getting sources: {str(e)}")
            return {}
    
    async def generate_answer(self, query: str, sources: Dict[str, List[Dict[str, Any]]], chat_history: Optional[str] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Generate an answer based on sources and chat history.
        
        Args:
            query: The user's query string
            sources: Dictionary of sources by platform
            chat_history: Optional chat history for context
            
        Returns:
            Tuple containing:
            - answer: The generated answer
            - references: List of source references
        """
        try:
            # Format sources for the LLM
            formatted_sources = await self._format_sources(sources)
            
            # Generate response
            response = ""
            references = []
            
            if self.genai_configured:
                # Use the conversation chain for response generation
                response = self.chain.predict(input=query)
                
                # Extract references from the response
                references = self._extract_references(response, sources)
            else:
                response = "I apologize, but the AI service is not configured properly."
            
            return response, references
        except Exception as e:
            print(f"Error generating answer: {str(e)}")
            return "I apologize, but I encountered an error generating an answer.", []
    
    def _extract_references(self, response: str, sources: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Extract references from the response and sources.
        
        Args:
            response: The generated response
            sources: Dictionary of sources by platform
            
        Returns:
            List of source references
        """
        references = []
        
        # Extract URLs from the response
        urls = re.findall(r'https?://\S+', response)
        
        # Find matching sources
        for platform, platform_sources in sources.items():
            for source in platform_sources:
                if source.get('link') in urls:
                    references.append({
                        'num': len(references) + 1,
                        'title': source.get('title', 'Unknown Source'),
                        'link': source.get('link', ''),
                        'source': platform,
                        'preview': source.get('snippet', ''),
                        'images': source.get('media', []),
                        'logo': source.get('logo', '')
                    })
        
        return references
    
    async def _read_query(self, query: str) -> Dict[str, str]:
        """
        Process query and generate optimized platform-specific searches.
        
        Args:
            query: The user's query string
            
        Returns:
            Dictionary of platform-specific queries
        """
        if not self.genai_configured:
            # Fallback if GenAI not configured
            return {
                "Reddit": query,
                "Twitter": query,
                "Searpi": query,
                "NewsAPI": query,
                "Arxiv": query
            }

        # Extract URLs from query for direct inspection
        urls = re.findall(r'https?://\S+', query)
        text_parts = [query]

        # Load summary content from URLs to enhance query context
        for url in urls[:3]:  # Limit to first 3 URLs to avoid overloading
            try:
                content = await asyncio.wait_for(self._load_url_content(url), timeout=20)
                if content.get('content') and not content.get('error'):
                    # Add a shortened version of the content
                    summary = content['content'][:1500]
                    text_parts.append(f"URL CONTENT SUMMARY ({url}):\n{summary}")
            except asyncio.TimeoutError:
                continue

        combined_query = "\n".join(text_parts)

        system_instruction = """
        Convert this text into focused, specific search queries for different platforms.
        Each query should capture the essential information need while being formatted appropriately for the platform.
        For news queries, focus on factual elements and recent developments.
        For academic queries, focus on technical terms and concepts.
        For social media queries, include relevant hashtags and trending terms if applicable.
        if the user query can't be rewritten to any sources style just return back the query of the user or sth that will be close to the user query without deviating
        
        Respond ONLY with valid JSON:
        {
            "Reddit": "reddit query relevant to user query",
            "Twitter": "twitter query with relevant hashtags if appropriate",
            "Searpi": "web search query with key terms",
            "NewsAPI": "news focused query with publication timeframe if relevant",
            "Arxiv": "academic query with field-specific terminology"
        }
        """

        try:
            response = self.genai_client.models.generate_content(
                model=MODEL_ID,
                config=GenerateContentConfig(
                    temperature=0,
                    safety_settings=SAFETY_SETTINGS,
                    system_instruction=system_instruction,
                    tools=[Tool(google_search={})]
                ),
                contents=[{"role": "user", "parts": [{"text": combined_query}]}]
            )
            
            # Extract and parse JSON from response with robust error handling
            try:
                json_str = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_str:
                    query_dict = json.loads(json_str.group())
                    print("✅ Generated platform-specific queries successfully")
                    return query_dict
            except (json.JSONDecodeError, AttributeError) as e:
                print(f"❌ Error parsing query JSON: {str(e)}")
                
            # Fallback to basic query if parsing fails
            return {
                "Reddit": query,
                "Twitter": query,
                "Searpi": query,
                "NewsAPI": query,
                "Arxiv": query
            }
            
        except Exception as e:
            print(f"❌ Query generation error: {str(e)}")
            return {
                "Reddit": query,
                "Twitter": query,
                "Searpi": query,
                "NewsAPI": query,
                "Arxiv": query
            }
    
    async def _load_url_content(self, url: str) -> Dict[str, Any]:
        """
        Load content from a URL.
        
        Args:
            url: The URL to load
            
        Returns:
            Dictionary containing the loaded content
        """
        result = {
            "content": "",
            "citations": [],
            "media": [],
            "is_media_source": False,
            "title": "",
            "error": None
        }

        if not url or not isinstance(url, str) or not url.startswith(('http://', 'https://')):
            result["error"] = f"Invalid URL: {url}"
            return result

        try:
            # Extract domain for logging
            domain = urlparse(url).netloc
            print(f"📄 Loading content from {domain}...")
            
            # Create session if needed
            session = await self.create_session()
            
            # Load content based on URL type
            if url.endswith(".pdf"):
                # Handle PDF files
                result["content"] = f"PDF content from {domain}"
                result["title"] = f"PDF Document from {domain}"
            elif url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')):
                # Handle image files
                result["media"].append(url)
                result["is_media_source"] = True
                result["title"] = f"Image from {domain}"
                result["content"] = f"Image from {domain}"
            else:
                # Handle web pages
                async with session.get(url, timeout=15) as response:
                    if response.status != 200:
                        result["error"] = f"HTTP {response.status}"
                        return result
                    
                    # Parse HTML
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title
                    title_tag = soup.find('title')
                    result["title"] = title_tag.text if title_tag else f"Content from {domain}"
                    
                    # Extract content
                    main_content = soup.find('main') or soup.find('article') or soup.find('body')
                    if main_content:
                        result["content"] = main_content.get_text(separator='\n', strip=True)[:10000]
                    else:
                        result["content"] = soup.get_text(separator='\n', strip=True)[:10000]
                    
                    # Extract images
                    for img in soup.find_all('img')[:5]:
                        src = img.get('src')
                        if src and not src.startswith('data:'):
                            absolute_url = urljoin(url, src)
                            result["media"].append(absolute_url)
            
            # Extract citations/links from content
            result["citations"] = re.findall(r'https?://[^\s)\]>\'\"]+', result["content"])[:7]

        except Exception as e:
            result["error"] = f"URL loading failed: {str(e)}"
        
        return result
    
    async def _format_sources(self, sources: dict) -> str:
        """
        Format sources for the LLM.
        
        Args:
            sources: Dictionary of sources by platform
            
        Returns:
            Formatted string of sources
        """
        self.source_references = []
        formatted = []
        
        for source_type, results in sources.items():
            if not results:
                continue
                
            formatted.append(f"\n## {source_type.upper()} SOURCES\n")
            
            for idx, res in enumerate(results[:10], 1):
                ref_num = len(self.source_references) + 1
                
                # Ensure all required fields are present
                source_entry = {
                    "num": ref_num,
                    "title": res.get('title', f"{source_type} source {idx}"),
                    "link": res.get('link', ''),
                    "source": source_type,
                    "preview": res.get('snippet', ''),
                    "images": res.get('media', []),
                    "logo": res.get('logo', '')
                }
                
                # Add to source references list
                self.source_references.append(source_entry)
                
                entry = [
                    f"### [Source {ref_num}] {res.get('title', f'{source_type} source {idx}')}",
                    f"**Source Type:** {source_type}",
                    f"**URL:** {res.get('link', '')}",
                    f"**Preview:**\n{res.get('snippet', '')[:1000]}"
                ]
                
                if res.get('media'):
                    # Convert all image entries to strings
                    media_strs = [img if isinstance(img, str) else img.get('url', '') for img in res.get('media', [])[:3]]
                    entry.append(f"**Media:** {', '.join(media_strs)}")
                
                formatted.append("\n".join(entry) + "\n" + "-"*50 + "\n")
        
        # Debug output
        print(f"Formatted {len(self.source_references)} source references")
        if self.source_references:
            for i, ref in enumerate(self.source_references[:3]):
                print(f"Source {i+1}: {ref['title']} ({ref['source']})")
        
        return "\n".join(formatted)
    
    async def _format_sources_with_media(self) -> str:
        """Format media-rich sources for analysis"""
        media_sources = []
        for ref in self.source_references:
            if ref.get('media') or ref.get('images'):
                media_list = ref.get('media', []) or ref.get('images', [])
                media_entry = [
                    f"Source {ref['num']}: {ref['title']}",
                    f"Media URLs:"
                ]
                
                # Handle different media formats
                for media_item in media_list[:3]:
                    if isinstance(media_item, str):
                        media_entry.append(f"- {media_item}")
                    elif isinstance(media_item, dict) and 'url' in media_item:
                        media_entry.append(f"- {media_item['url']}")
                
                # Add preview context if available
                preview = ref.get('preview', '')
                if preview:
                    media_entry.append(f"Context: {preview[:500]}")
                
                media_sources.append("\n".join(media_entry))
        
        return "\n\n".join(media_sources)
    
    async def get_all_sources(self, platform_queries: dict) -> dict:
        """
        Conduct parallel searches with dynamic resource allocation.
        
        Args:
            platform_queries: Dictionary of platform-specific queries
            
        Returns:
            Dictionary of sources by platform
        """
        print(f"\n🌐 Starting multi-platform research operation")
        
        search_tasks = [
            ("1/5 Web", self.search_serp, platform_queries.get("Searpi", ""), 12),
            ("2/5 News", self.search_news, platform_queries.get("NewsAPI", ""), 7, 15),
            ("3/5 Twitter", self.search_twitter, platform_queries.get("Twitter", ""), 15),
            ("4/5 Academic", self.search_arxiv, platform_queries.get("Arxiv", ""), 10),
            ("5/5 Reddit", self.search_reddit, platform_queries.get("Reddit", ""), 10)
        ]

        # Execute all searches with individual timeouts
        tasks = [self._tracked_search(func, name, *args, max_retries=2, timeout=25) 
                for name, func, *args in search_tasks]
        
        web_results, news_results, twitter_results, arxiv_results, reddit_results = await asyncio.gather(*tasks)
        
        # Process direct URL sources
        url_sources = await self._process_urls_in_query(platform_queries)
        self.source_references.extend(url_sources)

        return {
            "Web": web_results,
            "News": news_results,
            "Twitter": twitter_results,
            "Academic": arxiv_results,
            "Reddit": reddit_results,
            "URLs": url_sources
        }
    
    async def _process_urls_in_query(self, platform_queries):
        """
        Process direct URLs found in original query.
        
        Args:
            platform_queries: Dictionary of platform-specific queries
            
        Returns:
            List of URL sources
        """
        url_results = []
        urls = re.findall(r'https?://\S+', platform_queries.get("Searpi", ""))
        
        for url in urls[:3]:  # Limit to first 3 URLs
            content = await self._load_url_content(url)
            if not content.get("error"):
                url_results.append({
                    "title": f"Direct Source - {urlparse(url).netloc}",
                    "link": url,
                    "media": content["media"],
                    "snippet": content['content'][:500],
                    "source": "Direct URL"
                })
        return url_results
    
    async def _tracked_search(self, search_func, source_name, *args, **kwargs):
        """
        Managed search with timing, error handling and retry logic.
        
        Args:
            search_func: The search function to call
            source_name: Name of the source
            *args: Arguments to pass to the search function
            **kwargs: Keyword arguments to pass to the search function
            
        Returns:
            List of search results
        """
        max_retries = kwargs.pop('max_retries', 2)
        timeout = kwargs.pop('timeout', 30)
        
        start = time.time()
        print(f"🔍 [{source_name}] Starting search...")
        
        for attempt in range(max_retries + 1):
            try:
                results = await asyncio.wait_for(search_func(*args, **kwargs), timeout=timeout)
                elapsed = time.time() - start
                
                # Store timing metrics
                self.search_times[source_name] = {
                    'elapsed': elapsed,
                    'timestamp': datetime.now().isoformat(),
                    'success': True,
                    'results_count': len(results) if results else 0
                }
                
                print(f"✅ [{source_name}] Found {len(results)} results ({elapsed:.1f}s)")
                return results
                
            except asyncio.TimeoutError:
                elapsed = time.time() - start
                if attempt < max_retries:
                    print(f"⏱️ [{source_name}] Timed out after {timeout}s, retrying ({attempt+1}/{max_retries})...")
                else:
                    print(f"⏰ [{source_name}] Timed out after {timeout}s, giving up")
                    
                    # Store failure metrics
                    self.search_times[source_name] = {
                        'elapsed': elapsed,
                        'timestamp': datetime.now().isoformat(),
                        'success': False,
                        'error': 'Timeout'
                    }
                    return []
                    
            except Exception as e:
                elapsed = time.time() - start
                if attempt < max_retries:
                    print(f"❌ [{source_name}] Failed ({elapsed:.1f}s): {str(e)}, retrying ({attempt+1}/{max_retries})...")
                else:
                    print(f"❌ [{source_name}] Failed ({elapsed:.1f}s): {str(e)}, giving up")
                    
                    # Store failure metrics
                    self.search_times[source_name] = {
                        'elapsed': elapsed,
                        'timestamp': datetime.now().isoformat(),
                        'success': False,
                        'error': str(e)
                    }
                    return []
    
    async def search_serp(self, query: str, num_results: int = 10) -> list:
        """
        Search using SerpAPI.
        
        Args:
            query: The search query
            num_results: Number of results to return
            
        Returns:
            List of search results
        """
        api_key = os.getenv("SERP_API_KEY")
        if not api_key:
            print("❌ SERP_API_KEY missing")
            return []

        params = {
            "api_key": api_key,
            "q": query,
            "num": num_results,
            "output": "json",
            "gl": "us",  # Country code (US by default)
            "hl": "en"   # Language code
        }

        try:
            session = await self.create_session()
            async with session.get("https://serpapi.com/search", params=params, timeout=15) as r:
                if r.status != 200:
                    print(f"❌ SERPAPI error: HTTP {r.status}")
                    return []
                    
                try:
                    data = await r.json()
                except json.JSONDecodeError:
                    print("❌ SERPAPI returned invalid JSON")
                    return []
                    
                if data.get("error"):
                    print(f"❌ SERPAPI error: {data['error']}")
                    return []
                
                results = []
                
                # Process organic results
                for res in data.get("organic_results", []):
                    snippet = res.get("snippet", "")
                    if not snippet and res.get("rich_snippet"):
                        # Try to extract text from rich snippets
                        rich = res.get("rich_snippet", {})
                        if rich.get("top", {}).get("detected_extensions"):
                            snippet = " ".join(rich["top"]["detected_extensions"].values())
                    
                    # Handle images in snippets        
                    cleaned_snippet = self.handle_images(snippet)
                    
                    results.append({
                        "title": res.get("title", ""),
                        "link": res.get("link", ""),
                        "snippet": cleaned_snippet,
                        "source": "SERP",
                        "position": res.get("position", 0)
                    })
                
                # Also include knowledge graph if available
                if data.get("knowledge_graph"):
                    kg = data["knowledge_graph"]
                    description = kg.get("description", "")
                    results.append({
                        "title": kg.get("title", "Knowledge Panel"),
                        "link": kg.get("website", ""),
                        "snippet": self.handle_images(description),
                        "source": "Knowledge Graph"
                    })
                    
                return results
                
        except Exception as e:
            print(f"❌ SERP error: {e}")
            return []
    
    async def search_news(self, query: str, days_back: int = 30, page_size: int = 10) -> list:
        """
        Search NewsAPI.
        
        Args:
            query: The search query
            days_back: Number of days to look back
            page_size: Number of results to return
            
        Returns:
            List of search results
        """
        api_key = os.getenv("NEWS_API_KEY")
        if not api_key:
            print("❌ NEWS_API_KEY missing")
            return []

        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        params = {
            "apiKey": api_key,
            "q": query,
            "from": from_date,
            "language": "en",
            "sortBy": "relevancy",
            "pageSize": page_size
        }

        try:
            session = await self.create_session()
            async with session.get("https://newsapi.org/v2/everything", params=params, timeout=10) as r:
                if r.status != 200:
                    error_text = await r.text()
                    print(f"❌ NewsAPI error: HTTP {r.status} - {error_text[:100]}")
                    
                    # Try headlines endpoint as fallback
                    print("⚠️ Trying top headlines as fallback...")
                    headline_params = {
                        "apiKey": api_key,
                        "q": query,
                        "language": "en",
                        "pageSize": page_size
                    }
                    
                    async with session.get("https://newsapi.org/v2/top-headlines", params=headline_params, timeout=10) as hr:
                        if hr.status != 200:
                            return []
                        data = await hr.json()
                else:
                    data = await r.json()
                
                if data.get("status") != "ok":
                    print(f"❌ NewsAPI returned error: {data.get('message', 'Unknown error')}")
                    return []
                
                results = []
                for article in data.get("articles", []):
                    # Format date nicely
                    pub_date = article.get("publishedAt", "")
                    if pub_date:
                        try:
                            dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                            formatted_date = dt.strftime("%b %d, %Y")
                        except ValueError:
                            formatted_date = pub_date
                    else:
                        formatted_date = ""
                    
                    # Process description and content
                    description = article.get("description", "")
                    content = article.get("content", "")
                    
                    # Use content if description is too short
                    if description and len(description) < 30 and content:
                        snippet = content[:150]
                    else:
                        snippet = description
                    
                    results.append({
                        "title": article.get("title", ""),
                        "link": article.get("url", ""),
                        "snippet": self.handle_images(snippet),
                        "source": article.get("source", {}).get("name", "NewsAPI"),
                        "published_at": formatted_date,
                        "author": article.get("author", "")
                    })
                
                return results
                
        except Exception as e:
            print(f"❌ NewsAPI error: {e}")
            return []
    
    async def search_twitter(self, query: str, count: int = 10) -> list:
        """
        Search Twitter.
        
        Args:
            query: The search query
            count: Number of results to return
            
        Returns:
            List of search results
        """
        if not self.twitter:
            return []

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.twitter.search_recent_tweets(
                    query,
                    max_results=count,
                    tweet_fields=["created_at", "public_metrics", "author_id"],
                    expansions=["author_id"],
                    user_fields=["username"]
                )
            )

            processed = []
            users = {u.id: u for u in response.includes.get('users', [])}
            for tweet in response.data:
                user = users.get(tweet.author_id)
                processed.append({
                    "title": f"Tweet by @{user.username}" if user else "Twitter Post",
                    "link": f"https://twitter.com/user/status/{tweet.id}",
                    "snippet": self.handle_images(tweet.text),
                    "source": "Twitter",
                    "created_at": tweet.created_at.isoformat()
                })
            return processed
        except Exception as e:
            print(f"Twitter error: {str(e)}")
            return []
    
    async def search_arxiv(self, query: str, max_records: int = 10) -> list:
        """
        Search arXiv.
        
        Args:
            query: The search query
            max_records: Maximum number of records to return
            
        Returns:
            List of search results
        """
        try:
            client = arxiv.Client()
            search = arxiv.Search(query=query, max_results=max_records)
            # Use async wrapper for synchronous client
            results = await asyncio.to_thread(client.results, search)
            return [{
                "title": result.title,
                "link": result.entry_id,
                "snippet": f"{result.summary[:150]}...",
                "source": "Arxiv"
            } for result in results]
        except Exception as e:
            print(f"Arxiv error: {e}")
            return []
    
    async def search_reddit(self, query: str, limit: int = 10) -> list:
        """
        Search Reddit.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            
        Returns:
            List of search results
        """
        if not self.reddit:
            return []

        try:
            results = []
            subreddit = await self.reddit.subreddit("all")
            async for post in subreddit.search(query, limit=limit, sort="relevance"):
                media = []
                if hasattr(post, 'media_metadata'):
                    for item in post.media_metadata.values():
                        if item.get('s'):
                            media.append(item['s']['u'])
                
                results.append({
                    "title": post.title,
                    "link": f"https://reddit.com{post.permalink}",
                    "snippet": post.selftext[:500] + ('...' if len(post.selftext) > 500 else ''),
                    "source": "Reddit",
                    "score": post.score,
                    "flair": post.link_flair_text,
                    "media": media[:3],
                    "created_utc": post.created_utc
                })
            return results
            
        except Exception as e:
            print(f"❌ Reddit error: {e}")
            return []
    
    def handle_images(self, content: str) -> str:
        """
        Replace image URLs with placeholders.
        
        Args:
            content: The content to process
            
        Returns:
            Processed content with image placeholders
        """
        if not content:
            return ""
            
        # Handle more image URL patterns
        patterns = [
            r'(?:https?://\S+?\.(?:jpg|jpeg|png|gif|webp|svg))',
            r'(?:data:image/[a-z]+;base64,[a-zA-Z0-9+/=]+)',
            r'(?:src=[\'\"]https?://\S+?\.(?:jpg|jpeg|png|gif|webp|svg)[\'\"])'
        ]
        
        processed = content
        for pattern in patterns:
            processed = re.sub(pattern, "[IMAGE]", processed)
            
        return processed

    async def process_query(self, query: str, chat_history=None, filters=None) -> tuple:
        """
        Process a user query and return response with sources.
        
        Args:
            query: The user query to process
            chat_history: Optional chat history for conversation context
            filters: Optional list of source types to include (e.g., ["Reddit", "Twitter"])
            
        Returns:
            Tuple of (response_text, sources)
        """
        try:
            # Reset source references for this query
            self.source_references = []
            
            # Track the user's filter preferences
            selected_sources = None
            
            # Generate platform-specific queries
            platform_queries = await self._read_query(query)
            
            # Apply source filters if provided
            if filters and isinstance(filters, list):
                # Save the original filter list for final filtering
                selected_sources = filters
                
                # Filter the platform queries to only include selected sources
                filtered_queries = {}
                source_mapping = {
                    "Reddit": "Reddit",
                    "Twitter": "Twitter", 
                    "Web": "Searpi",
                    "News": "NewsAPI",
                    "Academic": "Arxiv"
                }
                
                # Create reverse mapping for later filtering
                reverse_mapping = {v: k for k, v in source_mapping.items()}
                
                for source in filters:
                    if source in source_mapping and source_mapping[source] in platform_queries:
                        filtered_queries[source_mapping[source]] = platform_queries[source_mapping[source]]
                
                # If we have valid filters, use them; otherwise use all sources
                if filtered_queries:
                    platform_queries = filtered_queries
            
            # Get sources from all platforms
            sources = await self.get_all_sources(platform_queries)
            
            # Generate response using chat history for context
            response_text = ""
            async for chunk in self.generate_response(query, sources, chat_history):
                response_text += chunk
            
            # Debug info for source references
            print(f"Source references count: {len(self.source_references)}")
            if self.source_references:
                print(f"First source reference: {self.source_references[0]}")
            
            # Filter source_references if needed
            if selected_sources:
                # Create a new filtered list based on user selections
                filtered_references = []
                
                # Map source types to match filter names
                source_type_mapping = {
                    "SERP": "Web",
                    "Web": "Web",
                    "Knowledge Graph": "Web",
                    "NewsAPI": "News",
                    "News": "News",
                    "Twitter": "Twitter",
                    "Arxiv": "Academic",
                    "Academic": "Academic",
                    "Reddit": "Reddit",
                    "Direct URL": "Web"
                }
                
                # Only include sources that were specified in the filters
                for ref in self.source_references:
                    source_type = ref.get("source", "")
                    normalized_type = source_type_mapping.get(source_type, source_type)
                    
                    if normalized_type in selected_sources:
                        filtered_references.append(ref)
                
                return response_text, filtered_references
            
            # Make a deep copy of source_references to avoid issues with reference sharing
            import copy
            result_sources = copy.deepcopy(self.source_references)
            
            return response_text, result_sources
        except Exception as e:
            print(f"Error in process_query: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return f"I apologize, but I encountered an error while processing your query: {str(e)}", []

    async def generate_response(self, query: str, sources: dict, chat_history=None) -> AsyncGenerator[str, None]:
        """
        Generate streaming analysis with media verification and conversation history.
        
        Args:
            query: The user query
            sources: Dictionary of sources by platform
            chat_history: Optional chat history for context
            
        Returns:
            AsyncGenerator yielding response chunks
        """
        if not self.genai_configured:
            yield "❌ AI service unavailable - check API configuration"
            return

        formatted_sources = await self._format_sources(sources)
        media_analysis = await self._format_sources_with_media()
        
        # Format chat history for context if available
        conversation_context = ""
        if chat_history and len(chat_history) > 0:
            conversation_context = "**Previous Conversation**\n"
            for msg in chat_history:
                if hasattr(msg, 'role') and hasattr(msg, 'content'):
                    if msg.role == "user":
                        conversation_context += f"User: {msg.content}\n"
                    elif msg.role == "assistant":
                        conversation_context += f"Assistant: {msg.content}\n"
            conversation_context += "\n"

        system_instruction = """**Research Analysis Protocol**
1. Cross-reference all sources for consensus/conflicts
2. Validate media against source context
3. Highlight statistical significance
4. Note temporal relevance
5. Rate source credibility
6. Maintain neutral academic tone
7. Analyze all provided sources thoroughly
8. Structure response with these sections:
- 📌 Executive Summary (3-5 bullet points)
- 🔍 Key Findings (numbered list with citations [1][2])
- ⚖️ Controversies/Debates
- ❓ Unanswered Questions
- 📚 Recommended Further Research
9. Use markdown formatting with **bold** and italics
10. Always cite sources using [number] notation
11. Highlight statistics with ✅
12. Mention conflicting viewpoints with ⚠️
13. Reference previous conversation context if provided
"""

        typing_task = asyncio.create_task(self._async_typing("Analyzing multi-source evidence..."))

        try:
            loop = asyncio.get_event_loop()
            
            # Wrap the synchronous generator in an async iterator
            response_stream = await loop.run_in_executor(
                None,
                lambda: self.genai_client.models.generate_content_stream(
                    model=MODEL_ID,
                    config=GenerateContentConfig(
                        temperature=0.2,
                        tools=[Tool(google_search={})],
                        safety_settings=SAFETY_SETTINGS,
                        system_instruction=system_instruction
                    ),
                    contents=[{
                        "role": "user",
                        "parts": [{
                            "text": f"""**Research Request**
Query: {query}

{conversation_context}
**Aggregated Sources**
{formatted_sources}

**Media Analysis Context**
{media_analysis}

**Analysis Guidelines**
- Verify image/video timestamps against claims
- Check for source domain reputation
- Compare academic vs social media perspectives
- Highlight significant statistical outliers"""
                        }]
                    }]
                )
            )

            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass

            # Stream response
            full_response = ""
            for chunk in response_stream:
                if hasattr(chunk, 'text'):
                    full_response += chunk.text
                    yield chunk.text
            
            # Add source gallery if we have sources
         #   if self.source_references:
             #   source_gallery = "\n\n## 📚 Source Gallery\n" + "\n".join(
               #     f"{ref['num']}. **[{ref['source']}] {ref['title']}**\n{ref['link']}"
              #      for ref in self.source_references
           #     )
           #     yield source_gallery
        #    else:
                # Log warning if no sources were found
        #        print("⚠️ No sources to add to the gallery")

        except Exception as e:
            error_message = f"❌ Analysis generation failed: {str(e)}"
            print(error_message)
            import traceback
            print(traceback.format_exc())
            yield error_message

    async def _async_typing(self, message: str):
        """
        Animated progress indicator.
        
        Args:
            message: Message to display during animation
        """
        symbols = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
        start_time = time.time()
        while time.time() - start_time < 15:  # Max 15s animation
            for symbol in symbols:
                print(f"\r{symbol} {message}", end="", flush=True)
                await asyncio.sleep(0.2)
        print("\r" + " "*(len(message)+2) + "\r", end="") 
