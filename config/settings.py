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
    APP_VERSION: str = "0.6.0"  # Phase 6: LLM Integration Service

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
    COMPONENT_TYPES: list = ["SimpleComponent", "TableA", "ChartComponent"]  # Supported component types (Phase 4: added ChartComponent)

    # Phase 2 settings - Progressive component rendering
    MAX_COMPONENTS_PER_RESPONSE: int = 5  # Maximum components allowed per response
    COMPONENT_UPDATE_DELAY: float = 0.3  # Delay between component updates in seconds
    ENABLE_PROGRESSIVE_LOADING: bool = True  # Enable progressive component updates
    SIMULATE_PROCESSING_TIME: bool = True  # Simulate data loading delays (for demo)

    # Phase 3 settings - TableA component
    MAX_TABLE_ROWS: int = 20  # Maximum rows per table
    MAX_TABLES_PER_RESPONSE: int = 3  # Phase 5: Maximum tables per response
    TABLE_ROW_DELAY: float = 0.2  # Delay between row updates in seconds
    TABLE_COLUMNS_PRESET: dict = {
        "sales": ["Name", "Sales", "Region"],
        "users": ["Username", "Email", "Role", "Status"],
        "products": ["Product", "Category", "Price", "Stock"]
    }  # Predefined table schemas for demo

    # Phase 4 settings - Chart component
    MAX_CHART_POINTS: int = 50  # Maximum data points per chart
    MAX_CHARTS_PER_RESPONSE: int = 3  # Phase 5: Maximum charts per response
    CHART_POINT_DELAY: float = 0.2  # Delay between data point updates in seconds
    CHART_TYPES_PRESET: dict = {
        "sales_line": {
            "chart_type": "line",
            "title": "Sales Over Time",
            "x_axis": ["Jan", "Feb", "Mar", "Apr", "May"],
            "series": [{"label": "Sales", "values": [1000, 1200, 1800, 2100, 2400]}]
        },
        "revenue_bar": {
            "chart_type": "bar",
            "title": "Revenue by Region",
            "x_axis": ["US", "EU", "APAC", "LATAM"],
            "series": [{"label": "Revenue", "values": [45000, 38000, 52000, 31000]}]
        },
        "growth_line": {
            "chart_type": "line",
            "title": "User Growth",
            "x_axis": ["Week 1", "Week 2", "Week 3", "Week 4"],
            "series": [{"label": "Active Users", "values": [150, 230, 420, 680]}]
        },
        "performance_bar": {
            "chart_type": "bar",
            "title": "Performance Metrics",
            "x_axis": ["API Response", "DB Query", "Cache Hit", "Network"],
            "series": [{"label": "Latency (ms)", "values": [45, 12, 2, 78]}]
        }
    }  # Predefined chart configurations for demo

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
