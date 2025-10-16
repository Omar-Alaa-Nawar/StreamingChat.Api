"""
Streaming service for handling real-time text and component streaming.

This service provides the core streaming functionality for the StreamForge backend.

Phase 2: Progressive component rendering with multiple component support.
- Stream components in stages: empty → text → data update
- Support multiple components (1-5) per response
- Components identified by UUID for update matching
- Backwards compatible with Phase 1

Components are wrapped with $$$ delimiters:
$$${"type":"SimpleComponent","id":"uuid","data":{...}}$$$

Modular Architecture (v0.6.0):
- core.py: Shared utilities (tracking, validation)
- constants.py: Configuration and pattern keywords
- simple_component.py: SimpleComponent handlers
- table_component.py: TableA handlers
- chart_component.py: ChartComponent handlers
- patterns.py: Pattern detection and routing
"""

# Public API exports for backward compatibility
from .patterns import generate_chunks, generate_llm_stream
from .core import validate_component

# Export all component creation functions for direct import
from .simple_component import (
    create_empty_component,
    create_filled_component,
    create_partial_update,
    create_simple_component,  # Legacy Phase 1
)

from .table_component import (
    create_empty_table,
    create_table_row_update,
    create_filled_table,
)

from .chart_component import (
    create_empty_chart,
    create_cumulative_chart_update,
    create_filled_chart,
)

# Export core utilities
from .core import (
    track_component,
    get_component_state,
    validate_component_update,
)

__all__ = [
    # Main streaming functions
    "generate_chunks",
    "generate_llm_stream",
    
    # Validation
    "validate_component",
    
    # SimpleComponent
    "create_empty_component",
    "create_filled_component",
    "create_partial_update",
    "create_simple_component",
    
    # TableA
    "create_empty_table",
    "create_table_row_update",
    "create_filled_table",
    
    # ChartComponent
    "create_empty_chart",
    "create_cumulative_chart_update",
    "create_filled_chart",
    
    # Core utilities
    "track_component",
    "get_component_state",
    "validate_component_update",
]

__version__ = "0.6.0"
