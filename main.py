"""
StreamForge Backend API

Enterprise FastAPI application for streaming chat functionality.
This is the main entry point for the StreamForge backend service.

Architecture:
- Routers: API endpoint definitions
- Services: Business logic and streaming functionality
- Chains: LangChain integration (future)
- Config: Centralized configuration management

Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from routers import chat


# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Streaming chat API with real-time SSE responses",
)

# Configure CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)


@app.get("/")
async def root():
    """
    Root endpoint providing API information.

    Returns:
        dict: API metadata and status
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "endpoints": {
            "chat": "/chat",
            "health": "/chat/health",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }


@app.get("/health")
async def health_check():
    """
    Global health check endpoint.

    Returns:
        dict: Overall service health status
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Run application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",  # Use string format to enable reload
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
