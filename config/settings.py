"""
Configuration settings for StreamForge backend.
Centralized configuration management for the application.
"""

from typing import Optional


class Settings:
    """
    Application settings and configuration.

    This class manages all configuration for the StreamForge backend.
    Future: Will include LLM configurations (API keys, model settings, etc.)
    """

    # Application settings
    APP_NAME: str = "StreamForge API"
    APP_VERSION: str = "0.2.0"  # Phase 1: Component streaming support

    # CORS settings
    CORS_ORIGINS: list = [
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "*"  # Allow all origins for development
    ]

    # Server settings
    HOST: str = "127.0.0.1"  # Changed from 0.0.0.0 due to Windows port restrictions
    PORT: int = 8001  # Changed from 8000 due to port permission issues

    # Streaming settings
    STREAM_DELAY: float = 0.1  # Delay between chunks in seconds

    # Component streaming settings (Phase 1)
    ENABLE_COMPONENTS: bool = True  # Enable JSON component streaming
    COMPONENT_DELIMITER: str = "$$$"  # Delimiter for JSON components (Phase 2: changed to $$$)
    COMPONENT_TYPES: list = ["SimpleComponent"]  # Supported component types

    # Phase 2 settings - Progressive component rendering
    MAX_COMPONENTS_PER_RESPONSE: int = 5  # Maximum components allowed per response
    COMPONENT_UPDATE_DELAY: float = 0.3  # Delay between component updates in seconds
    ENABLE_PROGRESSIVE_LOADING: bool = True  # Enable progressive component updates
    SIMULATE_PROCESSING_TIME: bool = True  # Simulate data loading delays (for demo)

    # Future LLM configuration placeholders
    # These will be populated when integrating with LangChain
    LLM_MODEL: Optional[str] = None  # e.g., "gpt-4", "claude-3", etc.
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000
    LLM_API_KEY: Optional[str] = None

    # Future vector store configuration
    VECTOR_STORE_TYPE: Optional[str] = None  # e.g., "pinecone", "chroma"

    # Future RAG configuration
    ENABLE_RAG: bool = False
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200


# Global settings instance
settings = Settings()
