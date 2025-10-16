"""
Constants and configuration for streaming service.

Centralizes all pattern keywords, regex patterns, and shared settings
used across streaming modules.
"""

from config.settings import settings

# Component delimiter for wrapping components
COMPONENT_DELIMITER = settings.COMPONENT_DELIMITER

# Pattern detection keywords
MULTI_KEYWORDS = ["two", "2", "three", "3", "four", "4", "five", "5", "multiple", "several"]
TABLE_KEYWORDS = ["table", "tables", "sales", "users", "products"]
CHART_KEYWORDS = ["chart", "charts", "line", "bar", "graph", "plot", "trend", "revenue", "growth", "performance", "metrics"]
DELAYED_KEYWORDS = ["delayed", "partial"]
CARD_KEYWORDS = ["card", "cards", "component", "components"]
LOADING_KEYWORDS = ["loading", "incremental"]

# Max components per response
MAX_COMPONENTS_PER_RESPONSE = getattr(settings, "MAX_COMPONENTS_PER_RESPONSE", 5)
MAX_TABLES_PER_RESPONSE = getattr(settings, "MAX_TABLES_PER_RESPONSE", 3)
MAX_CHARTS_PER_RESPONSE = getattr(settings, "MAX_CHARTS_PER_RESPONSE", 3)

# Streaming delays
STREAM_DELAY = settings.STREAM_DELAY
COMPONENT_UPDATE_DELAY = settings.COMPONENT_UPDATE_DELAY
TABLE_ROW_DELAY = getattr(settings, "TABLE_ROW_DELAY", 0.2)
CHART_POINT_DELAY = getattr(settings, "CHART_POINT_DELAY", 0.2)

# Simulation settings
SIMULATE_PROCESSING_TIME = settings.SIMULATE_PROCESSING_TIME

# Data limits
MAX_TABLE_ROWS = settings.MAX_TABLE_ROWS
MAX_CHART_POINTS = settings.MAX_CHART_POINTS

# Presets
TABLE_COLUMNS_PRESET = settings.TABLE_COLUMNS_PRESET
CHART_TYPES_PRESET = settings.CHART_TYPES_PRESET
COMPONENT_TYPES = settings.COMPONENT_TYPES
