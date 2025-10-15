"""
Component schemas for structured data streaming.

Defines Pydantic models for JSON components that can be streamed
alongside text in the chat response. Components are rendered as
React components on the frontend.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, Literal
from datetime import datetime, timezone


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
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
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
    Data payload for Line/Bar Charts (Phase 4).

    ChartComponent supports progressive data visualization with:
    - chart_type: "line" or "bar"
    - title: Chart title/heading
    - x_axis: Array of x-axis labels
    - y_axis: Optional array of y-axis values (for reference)
    - series: Array of data series objects with label and values
    - total_points: Optional total data points count (for progress tracking)

    Progressive loading pattern:
    1. Send empty chart with metadata: {"chart_type": "line", "title": "...", "x_axis": [...], "series": []}
    2. Stream data progressively: {"series": [{"label": "Sales", "values": [1000]}]}
    3. Frontend merges series values: values = [...existing.values, ...new.values]
    4. Final state shows complete chart with all data points

    Example:
        Initial: {"chart_type": "line", "title": "Sales", "x_axis": ["Jan", "Feb"], "series": []}
        Update 1: {"series": [{"label": "Sales", "values": [1000]}]}
        Update 2: {"series": [{"label": "Sales", "values": [1000, 1200]}]}
        Final: {"chart_type": "line", "x_axis": [...], "series": [{"label": "Sales", "values": [1000, 1200]}]}
    """
    chart_type: Literal["line", "bar"] = Field(..., description="Type of chart: line or bar")
    title: str = Field(..., description="Chart title")
    x_axis: list[str] = Field(default_factory=list, description="Array of x-axis labels")
    y_axis: Optional[list[float]] = Field(None, description="Optional y-axis values for reference")
    series: list[dict] = Field(default_factory=list, description="Array of data series with label and values")
    total_points: Optional[int] = Field(None, description="Expected total data points (for progress tracking)")
    timestamp: Optional[str] = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        description="ISO 8601 timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "chart_type": "line",
                "title": "Monthly Sales",
                "x_axis": ["Jan", "Feb", "Mar", "Apr"],
                "series": [
                    {"label": "Sales", "values": [1000, 1200, 1800, 2100]}
                ],
                "total_points": 4,
                "timestamp": "2025-10-15T12:34:56.789Z"
            }
        }


class TableAComponentData(BaseModel):
    """
    Data payload for TableA component (Phase 3).

    TableA is a progressive, row-by-row streaming table component with:
    - columns: Array of column headers (strings)
    - rows: Array of row data (each row is an array of values)

    Progressive loading pattern:
    1. Send empty table with columns: {"columns": ["Name", "Sales"], "rows": []}
    2. Stream rows incrementally: {"rows": [["Alice", 100]]}
    3. Backend merges rows: rows = [...existing.rows, ...new.rows]
    4. Final state shows complete table with all data

    Example:
        Initial: {"columns": ["Name", "Sales", "Region"], "rows": []}
        Update 1: {"rows": [["Alice", 123, "US"]]}
        Update 2: {"rows": [["Bob", 234, "UK"]]}
        Final merged: {"columns": [...], "rows": [["Alice", 123, "US"], ["Bob", 234, "UK"]]}
    """
    columns: list[str] = Field(default_factory=list, description="Array of column header names")
    rows: list[list[Any]] = Field(default_factory=list, description="Array of row data arrays")
    total_rows: Optional[int] = Field(None, description="Expected total row count (for progress tracking)")
    timestamp: Optional[str] = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        description="ISO 8601 timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "columns": ["Name", "Sales", "Region"],
                "rows": [
                    ["Alice", 123, "US"],
                    ["Bob", 234, "UK"],
                    ["Carlos", 345, "DE"]
                ],
                "total_rows": 3,
                "timestamp": "2025-10-15T12:34:56.789Z"
            }
        }


class FormComponentData(BaseModel):
    """
    Future: Data payload for interactive form components.

    Will support:
    - fields: Form field definitions
    - submitUrl: Where to send form data
    - validation: Validation rules
    """
    pass
