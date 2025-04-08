"""
Main FastAPI application module.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import router
from app.services.source_finder import SourceFinder
from app.memory.chat_memory import ChatMemory

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Initialize services on startup
    app.state.source_finder = SourceFinder()
    app.state.chat_memory = ChatMemory()
    
    # Make services available globally
    app.router.source_finder = app.state.source_finder
    app.router.chat_memory = app.state.chat_memory
    
    print("✅ API services initialized successfully")
    
    yield
    
    # Cleanup on shutdown
    if hasattr(app.state.source_finder, 'close_session'):
        try:
            await app.state.source_finder.close_session()
            print("✅ Resources cleaned up on shutdown")
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

# Create FastAPI application
app = FastAPI(
    title="SourceFinder API",
    description="API for finding and processing information from various sources",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

@app.get("/")
async def root():
    """
    Root endpoint that returns API information.
    """
    return {
        "name": "SourceFinder API",
        "version": "1.0.0",
        "description": "API for finding and processing information from various sources",
        "documentation": "/docs"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    This endpoint returns the health status of the API.
    """
    return {"status": "healthy"}