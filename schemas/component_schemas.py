"""
Component schemas for structured data streaming.

Defines Pydantic models for JSON components that can be streamed
alongside text in the chat response. Components are rendered as
React components on the frontend.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime


class ComponentData(BaseModel):
    """
    Base component data structure for streaming.

    All components streamed to frontend follow this structure:
    - type: Component type identifier (e.g., "SimpleComponent")
    - id: Unique UUID7 identifier for the component
    - data: Component-specific payload (flexible dict)

    This structure is wrapped with $$ delimiters when streamed:
    $${"type":"SimpleComponent","id":"...","data":{...}}$$
    """
    type: str = Field(..., description="Component type identifier")
    id: str = Field(..., description="Unique UUID7 identifier")
    data: Dict[str, Any] = Field(..., description="Component-specific data payload")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "SimpleComponent",
                "id": "01932e4f-a4c2-7890-b123-456789abcdef",
                "data": {
                    "title": "Sample Card",
                    "description": "This is a sample component",
                    "value": 100
                }
            }
        }


class SimpleComponentData(BaseModel):
    """
    Data payload for SimpleComponent.

    SimpleComponent is a basic card-like component with:
    - title: Main heading
    - description: Detailed text
    - value: Numeric value (optional)
    - timestamp: ISO 8601 timestamp of creation
    """
    title: str = Field(..., description="Component title/heading")
    description: str = Field(..., description="Component description text")
    value: Optional[int] = Field(None, description="Optional numeric value")
    timestamp: Optional[str] = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="ISO 8601 timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Sample Card",
                "description": "This is a sample component with some data",
                "value": 100,
                "timestamp": "2025-10-14T12:34:56.789Z"
            }
        }


# Future component types (Phase 2+)

class ChartComponentData(BaseModel):
    """
    Future: Data payload for chart components.

    Will support:
    - chartType: "bar", "line", "pie", etc.
    - data: Array of data points
    - labels: Axis labels
    - options: Chart configuration
    """
    pass


class TableComponentData(BaseModel):
    """
    Future: Data payload for table components.

    Will support:
    - columns: Column definitions
    - rows: Array of row data
    - pagination: Pagination settings
    """
    pass


class FormComponentData(BaseModel):
    """
    Future: Data payload for interactive form components.

    Will support:
    - fields: Form field definitions
    - submitUrl: Where to send form data
    - validation: Validation rules
    """
    pass
