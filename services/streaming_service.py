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
"""

import asyncio
import json
import uuid
import logging
import re
from typing import AsyncGenerator, Dict
from datetime import datetime, timezone
from config.settings import settings
from utils.id_generator import generate_uuid7
from schemas.component_schemas import ComponentData, SimpleComponentData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def track_component(component_id: str, data: dict, active_components: Dict[str, dict]):
    """
    Track component state during streaming.
    
    Args:
        component_id: UUID of the component
        data: Current data state of the component
        active_components: Request-scoped component tracking dictionary
    """
    active_components[component_id] = data
    logger.info(f"Tracking component: {component_id}")


def get_component_state(component_id: str, active_components: Dict[str, dict]) -> dict:
    """
    Get current state of tracked component.
    
    Args:
        component_id: UUID of the component
        active_components: Request-scoped component tracking dictionary
        
    Returns:
        dict: Component data or empty dict if not found
    """
    return active_components.get(component_id, {})


def create_empty_component(component_id: str, active_components: Dict[str, dict]) -> dict:
    """
    Create empty component placeholder (Phase 2).
    
    This creates a component with no data, used to render
    an immediate placeholder in the frontend.
    
    Args:
        component_id: UUID for the component
        active_components: Request-scoped component tracking dictionary
        
    Returns:
        dict: Empty component structure
        
    Example:
        >>> comp = create_empty_component("abc-123", {})
        >>> print(comp)
        {
            "type": "SimpleComponent",
            "id": "abc-123",
            "data": {}
        }
    """
    component = {
        "type": "SimpleComponent",
        "id": component_id,
        "data": {}
    }
    
    track_component(component_id, {}, active_components)
    logger.info(f"Created empty component: {component_id}")
    
    return component


def create_filled_component(
    component_id: str,
    title: str,
    description: str,
    value: int,
    active_components: Dict[str, dict]
) -> dict:
    """
    Create component with full data (Phase 2).
    
    This populates a component with actual data, used to update
    a previously created empty component.
    
    Args:
        component_id: UUID for the component (should match empty component)
        title: Component title
        description: Component description
        value: Numeric value
        active_components: Request-scoped component tracking dictionary
        
    Returns:
        dict: Filled component structure
        
    Example:
        >>> comp = create_filled_component("abc-123", "Card", "Data loaded", 100, {})
        >>> print(comp)
        {
            "type": "SimpleComponent",
            "id": "abc-123",
            "data": {
                "title": "Card",
                "description": "Data loaded",
                "value": 100,
                "timestamp": "2025-10-14T13:30:00.123456"
            }
        }
    """
    data = {
        "title": title,
        "description": description,
        "value": value,
        "timestamp": datetime.now().isoformat()
    }
    
    component = {
        "type": "SimpleComponent",
        "id": component_id,
        "data": data
    }
    
    track_component(component_id, data, active_components)
    logger.info(f"Filled component: {component_id} with data: {data}")
    
    return component


def create_partial_update(component_id: str, data: dict, active_components: Dict[str, dict]) -> dict:
    """
    Create partial data update for existing component (Phase 2).
    
    This allows incremental updates to a component's data.
    
    Args:
        component_id: UUID for the component
        data: Partial data to update
        active_components: Request-scoped component tracking dictionary
        
    Returns:
        dict: Component update structure
        
    Example:
        >>> update = create_partial_update("abc-123", {"title": "Loading..."}, {})
        >>> print(update)
        {
            "type": "SimpleComponent",
            "id": "abc-123",
            "data": {"title": "Loading..."}
        }
    """
    component = {
        "type": "SimpleComponent",
        "id": component_id,
        "data": data
    }
    
    # Merge with existing state
    existing_data = get_component_state(component_id, active_components)
    merged_data = {**existing_data, **data}
    track_component(component_id, merged_data, active_components)
    
    logger.info(f"Partial update for component {component_id}: {data}")
    
    return component


def validate_component_update(component_id: str, data: dict, active_components: Dict[str, dict]) -> bool:
    """
    Validate component update before sending (Phase 2).
    
    Args:
        component_id: UUID of the component
        data: Data to validate
        active_components: Request-scoped component tracking dictionary
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Check if component was initialized
    if component_id not in active_components:
        logger.warning(f"Update for unknown component: {component_id}")
        return False
    
    # Validate data structure
    if not isinstance(data, dict):
        logger.error(f"Invalid data type for component {component_id}")
        return False
    
    return True


# ============================================================================
# Phase 3: TableA Helper Functions
# ============================================================================

def create_empty_table(table_id: str, columns: list[str], active_components: Dict[str, dict]) -> dict:
    """
    Create empty table placeholder with columns only (Phase 3).
    
    This creates a TableA component with column headers but no rows,
    used to render an immediate skeleton table in the frontend.
    
    Args:
        table_id: UUID for the table component
        columns: List of column header names
        active_components: Request-scoped component tracking dictionary
        
    Returns:
        dict: Empty TableA component structure
        
    Example:
        >>> table = create_empty_table("table-1", ["Name", "Sales", "Region"], {})
        >>> print(table)
        {
            "type": "TableA",
            "id": "table-1",
            "data": {
                "columns": ["Name", "Sales", "Region"],
                "rows": []
            }
        }
    """
    component = {
        "type": "TableA",
        "id": table_id,
        "data": {
            "columns": columns,
            "rows": []
        }
    }
    
    track_component(table_id, {"columns": columns, "rows": []}, active_components)
    logger.info(f"Created empty table: {table_id} with columns: {columns}")
    
    return component


def create_table_row_update(table_id: str, new_rows: list[list], active_components: Dict[str, dict]) -> dict:
    """
    Create a row update for an existing table (Phase 3).
    
    This adds new rows to an existing TableA component.
    Backend will merge rows with existing state.
    
    Args:
        table_id: UUID for the table component
        new_rows: List of new rows to add (each row is a list of values)
        active_components: Request-scoped component tracking dictionary
        
    Returns:
        dict: TableA update structure with new rows
        
    Example:
        >>> update = create_table_row_update("table-1", [["Alice", 123, "US"]], {})
        >>> print(update)
        {
            "type": "TableA",
            "id": "table-1",
            "data": {
                "rows": [["Alice", 123, "US"]]
            }
        }
    """
    component = {
        "type": "TableA",
        "id": table_id,
        "data": {
            "rows": new_rows
        }
    }
    
    # Merge with existing state
    existing_data = get_component_state(table_id, active_components)
    existing_rows = existing_data.get("rows", [])
    merged_rows = existing_rows + new_rows
    
    merged_data = {
        **existing_data,
        "rows": merged_rows
    }
    track_component(table_id, merged_data, active_components)
    
    logger.info(f"Added {len(new_rows)} row(s) to table {table_id}. Total rows: {len(merged_rows)}")
    
    return component


def create_filled_table(
    table_id: str,
    columns: list[str],
    rows: list[list],
    total_rows: int = None,
    active_components: Dict[str, dict] = None
) -> dict:
    """
    Create complete table with all data (Phase 3).
    
    This creates a fully populated TableA component with columns and all rows.
    Used for single-shot table rendering without progressive updates.
    
    Args:
        table_id: UUID for the table component
        columns: List of column header names
        rows: List of all rows (each row is a list of values)
        total_rows: Optional total row count for progress tracking
        active_components: Request-scoped component tracking dictionary (optional for backwards compatibility)
        
    Returns:
        dict: Complete TableA component structure
        
    Example:
        >>> table = create_filled_table(
        ...     "table-1",
        ...     ["Name", "Sales"],
        ...     [["Alice", 100], ["Bob", 200]],
        ...     total_rows=2
        ... )
    """
    data = {
        "columns": columns,
        "rows": rows,
        "timestamp": datetime.now().isoformat()
    }
    
    if total_rows is not None:
        data["total_rows"] = total_rows
    
    component = {
        "type": "TableA",
        "id": table_id,
        "data": data
    }
    
    if active_components is not None:
        track_component(table_id, data, active_components)
    logger.info(f"Created filled table: {table_id} with {len(rows)} rows")
    
    return component


# ============================================================================
# End Phase 3 Functions
# ============================================================================


# ============================================================================
# Phase 4: ChartComponent Helper Functions
# ============================================================================

def create_empty_chart(
    chart_id: str,
    chart_type: str,
    title: str,
    x_axis: list[str],
    active_components: Dict[str, dict]
) -> dict:
    """
    Create empty chart placeholder with metadata but no data points (Phase 4).
    
    This creates a ChartComponent with chart type, title, and axis labels
    but no series data, used to render an immediate skeleton chart in the frontend.
    
    Args:
        chart_id: UUID for the chart component
        chart_type: Type of chart ("line" or "bar")
        title: Chart title
        x_axis: List of x-axis labels
        active_components: Request-scoped component tracking dictionary
        
    Returns:
        dict: Empty ChartComponent structure
        
    Example:
        >>> chart = create_empty_chart("chart-1", "line", "Sales Trend", ["Jan", "Feb"], {})
        >>> print(chart)
        {
            "type": "ChartComponent",
            "id": "chart-1",
            "data": {
                "chart_type": "line",
                "title": "Sales Trend",
                "x_axis": ["Jan", "Feb"],
                "series": []
            }
        }
    """
    component = {
        "type": "ChartComponent",
        "id": chart_id,
        "data": {
            "chart_type": chart_type,
            "title": title,
            "x_axis": x_axis,
            "series": []
        }
    }
    
    track_component(chart_id, {
        "chart_type": chart_type,
        "title": title,
        "x_axis": x_axis,
        "series": []
    }, active_components)
    logger.info(f"Created empty {chart_type} chart: {chart_id} with title: {title}")
    
    return component


def create_chart_data_update(
    chart_id: str,
    new_values: list[float],
    series_label: str,
    active_components: Dict[str, dict]
) -> dict:
    """
    Append data points to an existing chart series (Phase 4).
    
    This adds new data points to an existing ChartComponent series.
    Backend MERGES values and sends CUMULATIVE array (not just new values).
    
    IMPORTANT: Like TableA rows, this sends the FULL cumulative array,
    not just the increment. Frontend replaces the array completely.
    
    Args:
        chart_id: UUID for the chart component
        new_values: List of new data points to add
        series_label: Label for the data series
        active_components: Request-scoped component tracking dictionary
        
    Returns:
        dict: ChartComponent update with CUMULATIVE values array
        
    Example:
        >>> # Initial state: []
        >>> update1 = create_chart_data_update("chart-1", [1000], "Sales", {})
        >>> # Returns: {"series": [{"label": "Sales", "values": [1000]}]}
        >>> 
        >>> update2 = create_chart_data_update("chart-1", [1200], "Sales", {})
        >>> # Returns: {"series": [{"label": "Sales", "values": [1000, 1200]}]}  ← CUMULATIVE!
    """
    # Merge with existing state
    existing_data = get_component_state(chart_id, active_components)
    existing_series = existing_data.get("series", [])
    
    # Find or create series with matching label
    series_found = False
    merged_series = []
    cumulative_values = []
    
    for series in existing_series:
        if series.get("label") == series_label:
            # Merge values for matching series - CREATE CUMULATIVE ARRAY
            existing_values = series.get("values", [])
            cumulative_values = existing_values + new_values  # THIS IS THE CUMULATIVE ARRAY
            merged_series.append({"label": series_label, "values": cumulative_values})
            series_found = True
        else:
            merged_series.append(series)
    
    # If series doesn't exist yet, add it
    if not series_found:
        cumulative_values = new_values
        merged_series.append({"label": series_label, "values": cumulative_values})
    
    # Update tracked state with merged data
    merged_data = {
        **existing_data,
        "series": merged_series
    }
    track_component(chart_id, merged_data, active_components)
    
    total_points = sum(len(s.get("values", [])) for s in merged_series)
    logger.info(f"Added {len(new_values)} point(s) to chart {chart_id} series '{series_label}'. Total points: {total_points}")
    
    # CRITICAL: Return component with CUMULATIVE values (not just new_values)
    # This matches TableA behavior where backend sends cumulative rows
    component = {
        "type": "ChartComponent",
        "id": chart_id,
        "data": {
            "series": [{"label": series_label, "values": cumulative_values}]  # ← CUMULATIVE!
        }
    }
    
    return component


def create_filled_chart(
    chart_id: str,
    chart_data: dict,
    active_components: Dict[str, dict] = None
) -> dict:
    """
    Create complete chart with all data (Phase 4).
    
    This creates a fully populated ChartComponent with all metadata and data.
    Used for single-shot chart rendering without progressive updates.
    
    Args:
        chart_id: UUID for the chart component
        chart_data: Complete chart data including chart_type, title, x_axis, series, etc.
        active_components: Request-scoped component tracking dictionary (optional)
        
    Returns:
        dict: Complete ChartComponent structure
        
    Example:
        >>> chart = create_filled_chart(
        ...     "chart-1",
        ...     {
        ...         "chart_type": "line",
        ...         "title": "Sales",
        ...         "x_axis": ["Jan", "Feb"],
        ...         "series": [{"label": "Sales", "values": [1000, 1200]}],
        ...         "total_points": 2
        ...     }
        ... )
    """
    data = {
        **chart_data,
        "timestamp": datetime.now().isoformat()
    }
    
    component = {
        "type": "ChartComponent",
        "id": chart_id,
        "data": data
    }
    
    if active_components is not None:
        track_component(chart_id, data, active_components)
    
    total_points = sum(len(s.get("values", [])) for s in data.get("series", []))
    logger.info(f"Created filled {data.get('chart_type')} chart: {chart_id} with {total_points} total points")
    
    return component


# ============================================================================
# End Phase 4 Functions
# ============================================================================


def create_simple_component(
    title: str = "Sample Card",
    description: str = "This is a sample component",
    value: int = 100
) -> dict:
    """
    Create a SimpleComponent with data (Legacy - Phase 1).
    
    DEPRECATED: Use create_filled_component() for Phase 2.
    Kept for backwards compatibility. This function will be removed in version 3.0 (expected Q1 2026).

    Args:
        title: Component title/heading
        description: Component description text
        value: Optional numeric value

    Returns:
        dict: Component data structure ready for streaming
    """
    # Create component data payload
    component_data = SimpleComponentData(
        title=title,
        description=description,
        value=value,
        timestamp=datetime.now(timezone.utc).isoformat()
    )

    # Wrap in ComponentData structure
    component = ComponentData(
        type="SimpleComponent",
        id=generate_uuid7(),
        data=component_data.model_dump()
    )

    return component.model_dump()


async def generate_card_with_delay(active_components: Dict[str, dict]) -> AsyncGenerator[bytes, None]:
    """
    Generate a card with partial progressive update (Phase 2.1 Fix).
    
    This pattern demonstrates partial → complete progressive updates:
    1. Creates component with initial data (title + date + description)
    2. Waits 5 seconds (simulating data fetch/processing)
    3. Sends partial update with new fields (units + updated description)
    
    Flow:
        Initial Component (title+date+description) → 5s Delay → Partial Update (units+description)
    
    Frontend should merge updates:
        {title, date, description: "loading..."} → {title, date, description: "success!", units}
    
    Args:
        active_components: Request-scoped component tracking dictionary
    
    Yields:
        bytes: UTF-8 encoded chunks (JSON components only)
    
    Example Output:
        1. $$${"type":"SimpleComponent","id":"abc","data":{"title":"Card Title","date":"...","description":"Generating units... please wait."}}$$$
        2. [5-second pause]
        3. $$${"type":"SimpleComponent","id":"abc","data":{"description":"Units added successfully!","units":150}}$$$
    """
    logger.info("Pattern: Partial progressive update (title+date+description → units+description after 5s)")
    
    # Stage 1: Create component with initial data (title + date + description)
    component_id = generate_uuid7()
    initial_data = {
        "title": "Card Title",
        "date": datetime.now().isoformat(),
        "description": "Generating units... please wait."
    }
    
    initial_component = {
        "type": "SimpleComponent",
        "id": component_id,
        "data": initial_data
    }
    
    track_component(component_id, initial_data, active_components)
    component_json = json.dumps(initial_component, separators=(',', ':'))
    yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
    await asyncio.sleep(0.1)
    
    logger.info(f"Sent initial component with title+date+description: {component_id}")
    
    # Stage 2: Simulate 5-second delay (data loading/processing)
    logger.info(f"Starting 5-second delay for component: {component_id}")
    await asyncio.sleep(5.0)
    logger.info(f"Delay completed for component: {component_id}")
    
    # Stage 3: Send partial update with units and updated description
    partial_update = {
        "type": "SimpleComponent",
        "id": component_id,
        "data": {
            "description": "Units added successfully!",
            "units": 150
        }
    }
    
    # Update tracked state (merge with existing)
    existing_data = get_component_state(component_id, active_components)
    merged_data = {**existing_data, **partial_update["data"]}
    track_component(component_id, merged_data, active_components)
    
    component_json = json.dumps(partial_update, separators=(',', ':'))
    yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
    await asyncio.sleep(0.1)
    
    logger.info(f"Sent partial update (description+units) for component: {component_id}")
    
    logger.info(f"Completed partial progressive update for: {component_id}")


async def generate_chunks(user_message: str) -> AsyncGenerator[bytes, None]:
    """
    Generate streaming response with progressive component updates (Phase 3).

    Phase 3 Implementation:
    - Extends Phase 2 with TableA component support
    - Streams table rows progressively: skeleton → row-by-row → complete
    - Maintains backward compatibility with all Phase 2 patterns
    - Supports multiple component types: SimpleComponent, TableA

    Phase 2.1 Fix:
    - Added delayed card update pattern (5-second delay)
    - Validates progressive component lifecycle with timing

    Flow:
    1. Detect user intent from message
    2. Send empty component(s) as placeholder(s)
    3. Stream explanatory text while "loading"
    4. Update component(s) with actual data (incrementally for tables)
    5. Stream completion message

    Supported patterns:
    - Single component with progressive load
    - Multiple components with staggered updates
    - Mixed text and components
    - Incremental data updates
    - Delayed card update (5-second delay) - Phase 2.1
    - TableA with progressive row streaming (Phase 3 NEW)

    Args:
        user_message: The user's input message

    Yields:
        bytes: UTF-8 encoded chunks (text or JSON components)

    Example Output (TableA):
        User: "show me sales table"
        
        Stream:
        1. $$${"type":"TableA","id":"abc","data":{"columns":[...],"rows":[]}}$$$
        2. "Loading data..."
        3. $$${"type":"TableA","id":"abc","data":{"rows":[["Alice",100,"US"]]}}$$$
        4. $$${"type":"TableA","id":"abc","data":{"rows":[["Bob",200,"UK"]]}}$$$
        5. "✓ All rows loaded!"
    """
    # Create request-scoped component tracking dictionary
    active_components: Dict[str, dict] = {}
    
    user_message_lower = user_message.lower()

    # Pattern 0: Partial progressive update (Phase 2.1 Fix)
    # Triggered by "delayed card" or "partial card" (singular only, not multiple)
    if (("delayed" in user_message_lower or "partial" in user_message_lower) and "card" in user_message_lower and
        not any(kw in user_message_lower for kw in ["two", "2", "three", "3", "four", "4", "five", "5", "multiple", "several"])):
        async for chunk in generate_card_with_delay(active_components):
            yield chunk
        return
    
    # Pattern 1: Single component with progressive loading
    if "card" in user_message_lower and not any(kw in user_message_lower for kw in ["two", "2", "three", "3", "multiple", "several"]):
        logger.info("Pattern: Single component with progressive loading")
        
        # Stage 1: Send empty component (creates placeholder)
        component_id = generate_uuid7()
        empty_component = create_empty_component(component_id, active_components)
        component_json = json.dumps(empty_component, separators=(',', ':'))
        yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
        await asyncio.sleep(settings.STREAM_DELAY)
        
        # Stage 2: Stream text while "processing"
        loading_text = "Generating your card"
        for word in loading_text.split():
            yield f"{word} ".encode("utf-8")
            await asyncio.sleep(settings.STREAM_DELAY)
        
        # Simulate processing time
        if settings.SIMULATE_PROCESSING_TIME:
            for i in range(3):
                yield ".".encode("utf-8")
                await asyncio.sleep(0.3)
        
        yield " ".encode("utf-8")
        
        # Stage 3: Send component with full data
        filled_component = create_filled_component(
            component_id,
            title="Dynamic Card",
            description="Data loaded successfully from the backend",
            value=150,
            active_components=active_components
        )
        component_json = json.dumps(filled_component, separators=(',', ':'))
        yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
        await asyncio.sleep(settings.STREAM_DELAY)
        
        # Stage 4: Completion message
        yield " All set!".encode("utf-8")
        
        logger.info(f"Completed single component: {component_id}")
    
    # Pattern 2: Multi-SimpleComponent with DELAYED updates (Phase 5.2)
    # Triggered ONLY by "delayed cards" with count (e.g., "two delayed cards")
    elif (("delayed" in user_message_lower or "partial" in user_message_lower) and 
          re.search(r'\b(cards?|components?)\b', user_message_lower) and
          any(kw in user_message_lower for kw in ["two", "2", "three", "3", "four", "4", "five", "5", "multiple", "several"])):
        logger.info("Pattern: Progressive SimpleComponent (multi-card support with delayed updates)")
        
        # Determine number of delayed cards to create
        num_cards = 2  # Default for "two", "multiple", "several"
        if "three" in user_message_lower or "3" in user_message_lower:
            num_cards = 3
        elif "four" in user_message_lower or "4" in user_message_lower:
            num_cards = 4
        elif "five" in user_message_lower or "5" in user_message_lower:
            num_cards = 5
        
        # Limit to max
        num_cards = min(num_cards, getattr(settings, "MAX_COMPONENTS_PER_RESPONSE", 5))
        
        # Stage 1: Send all cards with initial data (title + date + description "loading...")
        cards = []
        for i in range(num_cards):
            cid = generate_uuid7()
            cards.append(cid)
            
            initial_data = {
                "title": f"Delayed Card #{i+1}",
                "date": datetime.now().isoformat(),
                "description": "Generating units... please wait."
            }
            
            initial_component = {
                "type": "SimpleComponent",
                "id": cid,
                "data": initial_data
            }
            
            track_component(cid, initial_data, active_components)
            component_json = json.dumps(initial_component, separators=(',', ':'))
            yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
            await asyncio.sleep(0.05)  # Quick succession
            
            logger.info(f"Sent initial delayed card with title+date+description: {cid}")
        
        # Stage 2: Simulate delay (data loading/processing)
        delay_seconds = 3.0  # 3 seconds for multiple cards (faster than single card's 5s)
        yield f"\nProcessing {num_cards} delayed card{'s' if num_cards > 1 else ''}".encode("utf-8")
        
        if settings.SIMULATE_PROCESSING_TIME:
            for i in range(3):
                yield ".".encode("utf-8")
                await asyncio.sleep(1.0)  # Total 3 seconds
        else:
            await asyncio.sleep(delay_seconds)
        
        yield "\n".encode("utf-8")
        logger.info(f"Delay completed for all {num_cards} cards")
        
        # Stage 3: Send partial updates with units for all cards (interleaved)
        for idx, cid in enumerate(cards):
            partial_update = {
                "type": "SimpleComponent",
                "id": cid,
                "data": {
                    "description": "Units added successfully!",
                    "units": (idx + 1) * 50  # Different unit values per card
                }
            }
            
            # Update tracked state (merge with existing)
            existing_data = get_component_state(cid, active_components)
            merged_data = {**existing_data, **partial_update["data"]}
            track_component(cid, merged_data, active_components)
            
            component_json = json.dumps(partial_update, separators=(',', ':'))
            yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
            await asyncio.sleep(0.1)
            
            logger.info(f"Sent partial update (description+units) for card: {cid}")
        
        # Stage 4: Completion message
        yield f"\n✓ All {num_cards} delayed card{'s' if num_cards > 1 else ''} completed!\n".encode("utf-8")
        
        logger.info(f"Completed {num_cards} progressive delayed cards with partial updates")
    
    # Pattern 2b: Multi-SimpleComponent (Normal cards without delay) - Legacy behavior
    # NOTE: Exclude table/chart keywords to avoid conflicts with Patterns 4 & 5
    elif (re.search(r'\b(cards?|components?)\b', user_message_lower) or 
          (any(kw in user_message_lower for kw in ["two", "2", "three", "3", "multiple", "several"]) and
           not re.search(r'\b(tables?|charts?|sales|users?|products?|lines?|bars?|graphs?|plots?|trends?|revenue|growth|performance|metrics?)\b', user_message_lower))):
        logger.info("Pattern: Multiple components with progressive updates (normal cards)")
        
        # Determine number of components
        num_components = 2
        if "three" in user_message_lower or "3" in user_message_lower:
            num_components = 3
        elif "four" in user_message_lower or "4" in user_message_lower:
            num_components = 4
        elif "five" in user_message_lower or "5" in user_message_lower:
            num_components = 5
        
        # Limit to max
        num_components = min(num_components, settings.MAX_COMPONENTS_PER_RESPONSE)
        
        # Stage 1: Send all empty components first
        component_ids = []
        for i in range(num_components):
            comp_id = generate_uuid7()
            component_ids.append(comp_id)
            
            empty = create_empty_component(comp_id, active_components)
            component_json = json.dumps(empty, separators=(',', ':'))
            yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
            await asyncio.sleep(0.1)  # Quick succession
        
        # Stage 2: Stream text while "loading"
        loading_text = f"Loading data for all {num_components} cards"
        for word in loading_text.split():
            yield f"{word} ".encode("utf-8")
            await asyncio.sleep(settings.STREAM_DELAY)
        
        # Simulate processing
        if settings.SIMULATE_PROCESSING_TIME:
            for i in range(3):
                yield ".".encode("utf-8")
                await asyncio.sleep(0.3)
        
        yield " ".encode("utf-8")
        
        # Stage 3: Update each component with data (staggered)
        for i, comp_id in enumerate(component_ids):
            filled = create_filled_component(
                comp_id,
                title=f"Card {i+1}",
                description=f"This is card number {i+1} with unique data",
                value=(i+1) * 100,
                active_components=active_components
            )
            component_json = json.dumps(filled, separators=(',', ':'))
            yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
            await asyncio.sleep(settings.COMPONENT_UPDATE_DELAY)
        
        # Stage 4: Completion
        yield " Complete!".encode("utf-8")
        
        logger.info(f"Completed {num_components} components")
    
    # Pattern 3: Incremental updates (loading states)
    elif "loading" in user_message_lower or "incremental" in user_message_lower:
        logger.info("Pattern: Incremental component updates")
        
        component_id = generate_uuid7()
        
        # Stage 1: Empty component
        empty = create_empty_component(component_id, active_components)
        component_json = json.dumps(empty, separators=(',', ':'))
        yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
        await asyncio.sleep(0.2)
        
        yield "Watch the card load incrementally... ".encode("utf-8")
        await asyncio.sleep(0.3)
        
        # Stage 2: Update with title only
        partial1 = create_partial_update(component_id, {"title": "Loading..."}, active_components)
        component_json = json.dumps(partial1, separators=(',', ':'))
        yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
        await asyncio.sleep(0.5)
        
        # Stage 3: Update with title + description
        partial2 = create_partial_update(component_id, {
            "title": "Progressive Card",
            "description": "Description loaded..."
        }, active_components)
        component_json = json.dumps(partial2, separators=(',', ':'))
        yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
        await asyncio.sleep(0.5)
        
        # Stage 4: Complete data
        filled = create_filled_component(
            component_id,
            title="Progressive Card",
            description="All data loaded successfully!",
            value=100,
            active_components=active_components
        )
        component_json = json.dumps(filled, separators=(',', ':'))
        yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
        await asyncio.sleep(0.2)
        
        yield " Done with incremental loading!".encode("utf-8")
        
        logger.info(f"Completed incremental updates for: {component_id}")
    
    # Pattern 4: TableA with progressive row streaming (Phase 3 + Phase 5 Multi-Table Support)
    elif re.search(r'\b(tables?|sales|users?|products?)\b', user_message_lower):
        logger.info("Pattern: TableA with progressive row streaming (multi-table support)")
        
        # Determine number of tables (default: 1)
        num_tables = 1
        table_types = []
        
        # Check for multiple table keywords
        if any(kw in user_message_lower for kw in ["two", "2", "multiple", "several"]):
            num_tables = 2
        elif "three" in user_message_lower or "3" in user_message_lower:
            num_tables = 3
        
        # Detect specific table types mentioned
        if re.search(r'\bsales?\b', user_message_lower):
            table_types.append("sales")
        if re.search(r'\busers?\b', user_message_lower):
            table_types.append("users")
        if re.search(r'\bproducts?\b', user_message_lower):
            table_types.append("products")
        
        # If no specific types mentioned, use default
        if not table_types:
            table_types = ["sales"]
        
        # Detect if user wants multiple of the same type (Phase 5.1)
        same_type_requested = (num_tables > 1 and len(table_types) == 1)
        
        # If user explicitly said e.g. "two sales tables" or "three users tables"
        if same_type_requested:
            table_types = table_types * num_tables  # duplicate same type
        # Else fallback to mixed types as before
        elif num_tables > len(table_types):
            all_types = ["sales", "users", "products"]
            for t in all_types:
                if t not in table_types:
                    table_types.append(t)
                    if len(table_types) >= num_tables:
                        break
        
        # Limit to requested number
        table_types = table_types[:num_tables]
        num_tables = len(table_types)
        
        # Limit to max setting
        num_tables = min(num_tables, getattr(settings, 'MAX_TABLES_PER_RESPONSE', 3))
        table_types = table_types[:num_tables]
        
        # Prepare all tables data
        tables_data = []
        for table_type in table_types:
            columns = settings.TABLE_COLUMNS_PRESET.get(table_type, ["Column 1", "Column 2", "Column 3"])
            
            # Generate sample data based on table type
            if table_type == "sales":
                sample_rows = [
                    ["Alice Johnson", 12500, "North America"],
                    ["Bob Smith", 23400, "Europe"],
                    ["Carlos Rodriguez", 34500, "Latin America"],
                    ["Diana Chen", 18900, "Asia Pacific"],
                    ["Ethan Brown", 29200, "North America"]
                ]
            elif table_type == "users":
                sample_rows = [
                    ["alice_j", "alice@example.com", "Admin", "Active"],
                    ["bob_smith", "bob@example.com", "User", "Active"],
                    ["carlos_r", "carlos@example.com", "Manager", "Active"],
                    ["diana_c", "diana@example.com", "User", "Inactive"],
                    ["ethan_b", "ethan@example.com", "User", "Active"]
                ]
            else:  # products
                sample_rows = [
                    ["Laptop Pro", "Electronics", 1299.99, 45],
                    ["Desk Chair", "Furniture", 249.99, 120],
                    ["Coffee Maker", "Appliances", 89.99, 78],
                    ["Monitor 27\"", "Electronics", 399.99, 32],
                    ["Standing Desk", "Furniture", 549.99, 15]
                ]
            
            # Limit rows based on settings
            sample_rows = sample_rows[:settings.MAX_TABLE_ROWS]
            
            tables_data.append({
                "type": table_type,
                "columns": columns,
                "rows": sample_rows,
                "id": generate_uuid7()
            })
        
        # Stage 1: Send all empty tables first
        for table_info in tables_data:
            empty_table = create_empty_table(table_info["id"], table_info["columns"], active_components)
            component_json = json.dumps(empty_table, separators=(',', ':'))
            yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
            await asyncio.sleep(0.1)  # Quick succession for skeletons
        
        # Stage 2: Stream text while "loading"
        yield "\n".encode("utf-8")
        if num_tables == 1:
            loading_text = f"Here's your {table_types[0]} table. Loading data"
        else:
            loading_text = f"Loading data for all {num_tables} tables"
        
        for word in loading_text.split():
            yield f"{word} ".encode("utf-8")
            await asyncio.sleep(settings.STREAM_DELAY)
        
        # Simulate processing with dots
        if settings.SIMULATE_PROCESSING_TIME:
            for i in range(3):
                yield ".".encode("utf-8")
                await asyncio.sleep(0.3)
        
        yield "\n".encode("utf-8")
        
        # Stage 3: Stream rows progressively for each table (interleaved for multi-table)
        max_rows = max(len(t["rows"]) for t in tables_data)
        
        for row_idx in range(max_rows):
            for table_info in tables_data:
                if row_idx < len(table_info["rows"]):
                    row = table_info["rows"][row_idx]
                    row_update = create_table_row_update(table_info["id"], [row], active_components)
                    component_json = json.dumps(row_update, separators=(',', ':'))
                    yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
                    
                    # Add delay between rows for progressive effect
                    await asyncio.sleep(settings.TABLE_ROW_DELAY)
            
            # Optional: Stream progress text every few rows
            if (row_idx + 1) % 2 == 0 and row_idx < max_rows - 1:
                yield f"Loaded {row_idx + 1} rows... ".encode("utf-8")
        
        # Stage 4: Completion message
        total_rows = sum(len(t["rows"]) for t in tables_data)
        if num_tables == 1:
            yield f"\n✓ All {len(tables_data[0]['rows'])} rows loaded successfully!".encode("utf-8")
        else:
            yield f"\n✓ All {num_tables} tables loaded with {total_rows} total rows!".encode("utf-8")
        
        for table_info in tables_data:
            logger.info(f"Completed TableA streaming: {table_info['id']} ({table_info['type']}) with {len(table_info['rows'])} rows")
    
    # Pattern 5: ChartComponent with progressive data streaming (Phase 4 + Phase 5 Multi-Chart Support)
    elif re.search(r'\b(charts?|lines?|bars?|graphs?|plots?|trends?|revenue|growth|performance|metrics?)\b', user_message_lower):
        logger.info("Pattern: ChartComponent with progressive data streaming (multi-chart support)")
        
        # Determine number of charts (default: 1)
        num_charts = 1
        chart_presets = []
        
        # Check for multiple chart keywords
        if any(kw in user_message_lower for kw in ["two", "2", "multiple", "several"]):
            num_charts = 2
        elif "three" in user_message_lower or "3" in user_message_lower:
            num_charts = 3
        
        # Detect specific chart presets mentioned
        if re.search(r'\b(bar|revenue|performance)\b', user_message_lower):
            if "revenue" in user_message_lower:
                chart_presets.append("revenue_bar")
            if "performance" in user_message_lower:
                chart_presets.append("performance_bar")
            if "bar" in user_message_lower and not chart_presets:
                chart_presets.append("revenue_bar")
        
        if re.search(r'\b(line|trend|growth|sales)\b', user_message_lower):
            if "growth" in user_message_lower:
                chart_presets.append("growth_line")
            if "sales" in user_message_lower:
                chart_presets.append("sales_line")
            if ("line" in user_message_lower or "trend" in user_message_lower) and not chart_presets:
                chart_presets.append("sales_line")
        
        # If no specific presets mentioned, use default
        if not chart_presets:
            chart_presets = ["sales_line"]
        
        # Detect if user wants multiple of the same type (Phase 5.1)
        same_type_requested = (num_charts > 1 and len(chart_presets) == 1)
        
        # If user explicitly said e.g. "two line charts" or "three bar charts"
        if same_type_requested:
            chart_presets = chart_presets * num_charts  # duplicate same preset
        # Else fallback to mixed as before
        elif num_charts > len(chart_presets):
            all_presets = ["sales_line", "revenue_bar", "growth_line", "performance_bar"]
            for preset in all_presets:
                if preset not in chart_presets:
                    chart_presets.append(preset)
                    if len(chart_presets) >= num_charts:
                        break
        
        # Limit to requested number
        chart_presets = chart_presets[:num_charts]
        num_charts = len(chart_presets)
        
        # Limit to max setting
        num_charts = min(num_charts, getattr(settings, 'MAX_CHARTS_PER_RESPONSE', 3))
        chart_presets = chart_presets[:num_charts]
        
        # Prepare all charts data
        charts_data = []
        for chart_preset in chart_presets:
            # Get preset chart data
            preset_data = settings.CHART_TYPES_PRESET.get(chart_preset, {
                "chart_type": "line",
                "title": "Sample Chart",
                "x_axis": ["A", "B", "C"],
                "series": [{"label": "Data", "values": [10, 20, 30]}]
            })
            
            chart_type = preset_data["chart_type"]
            title = preset_data["title"]
            x_axis = preset_data["x_axis"]
            series_data = preset_data["series"][0]  # Get first series
            series_label = series_data["label"]
            all_values = series_data["values"]
            
            # Limit points based on settings
            all_values = all_values[:settings.MAX_CHART_POINTS]
            
            charts_data.append({
                "preset": chart_preset,
                "chart_type": chart_type,
                "title": title,
                "x_axis": x_axis,
                "series_label": series_label,
                "values": all_values,
                "id": generate_uuid7()
            })
        
        # Stage 1: Send all empty charts first
        for chart_info in charts_data:
            empty_chart = create_empty_chart(
                chart_info["id"],
                chart_info["chart_type"],
                chart_info["title"],
                chart_info["x_axis"],
                active_components
            )
            component_json = json.dumps(empty_chart, separators=(',', ':'))
            yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
            await asyncio.sleep(0.1)  # Quick succession for skeletons
        
        # Stage 2: Stream text while "loading"
        yield "\n".encode("utf-8")
        if num_charts == 1:
            loading_text = f"Generating {charts_data[0]['chart_type']} chart"
        else:
            loading_text = f"Generating all {num_charts} charts"
        
        for word in loading_text.split():
            yield f"{word} ".encode("utf-8")
            await asyncio.sleep(settings.STREAM_DELAY)
        
        # Simulate processing with dots
        if settings.SIMULATE_PROCESSING_TIME:
            for i in range(3):
                yield ".".encode("utf-8")
                await asyncio.sleep(0.3)
        
        yield "\n".encode("utf-8")
        
        # Stage 3: Stream data points progressively for each chart (interleaved for multi-chart)
        max_points = max(len(c["values"]) for c in charts_data)
        
        for point_idx in range(max_points):
            for chart_info in charts_data:
                if point_idx < len(chart_info["values"]):
                    value = chart_info["values"][point_idx]
                    data_update = create_chart_data_update(
                        chart_info["id"],
                        [value],
                        chart_info["series_label"],
                        active_components
                    )
                    component_json = json.dumps(data_update, separators=(',', ':'))
                    yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
                    
                    # Add delay between points for progressive effect
                    await asyncio.sleep(settings.CHART_POINT_DELAY)
            
            # Optional: Stream progress text every few points
            if (point_idx + 1) % 2 == 0 and point_idx < max_points - 1:
                yield f"Loaded {point_idx + 1}/{max_points} points... ".encode("utf-8")
        
        # Stage 4: Completion message
        total_points = sum(len(c["values"]) for c in charts_data)
        if num_charts == 1:
            yield f"\n✓ Chart completed with {len(charts_data[0]['values'])} data points!".encode("utf-8")
        else:
            yield f"\n✓ All {num_charts} charts completed with {total_points} total data points!".encode("utf-8")
        
        for chart_info in charts_data:
            logger.info(f"Completed ChartComponent streaming: {chart_info['id']} ({chart_info['chart_type']}) with {len(chart_info['values'])} points")
    
    # Pattern 6: Default text-only response
    else:
        logger.info("Pattern: Text-only response (no components)")
        
        response_text = (
            "This is a text-only response. "
            "Try asking for 'a card', 'two cards', 'show me loading states', 'show me a table', or 'show me a chart' "
            "to see Phase 4 progressive component rendering in action!"
        )
        
        words = response_text.split()
        for word in words:
            yield f"{word} ".encode("utf-8")
            await asyncio.sleep(settings.STREAM_DELAY)


async def generate_llm_stream(user_message: str) -> AsyncGenerator[bytes, None]:
    """
    Future: Generate streaming response from actual LLM.

    This function will be implemented when integrating with LangChain.
    It will invoke the LLM chain and stream the response back to the client.

    Future Implementation:
    - Real LLM will decide when to generate components
    - LLM will provide component parameters
    - Streaming will be based on actual token generation
    - Progressive component updates will be LLM-driven

    Args:
        user_message: The user's input message

    Yields:
        bytes: UTF-8 encoded text chunks from the LLM
    """
    # Placeholder for future LLM integration
    # When implemented, this will:
    # 1. Invoke LangChain streaming chain
    # 2. Process streaming tokens
    # 3. Parse special component markers from LLM
    # 4. Yield formatted chunks back to client

    raise NotImplementedError("LLM integration coming in future phase")


# Helper function for component validation
def validate_component(component: dict) -> bool:
    """
    Validate a component dictionary structure.

    Checks:
    - Has required fields (type, id, data)
    - Type is in allowed list
    - ID is valid UUID7 format
    - Data is a dictionary (can be empty for Phase 2)

    Args:
        component: Component dictionary to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        # Check required fields
        if not all(key in component for key in ["type", "id", "data"]):
            return False

        # Check type is allowed
        if component["type"] not in settings.COMPONENT_TYPES:
            return False

        # Check ID format (robust UUID validation)
        if not isinstance(component["id"], str):
            return False
        try:
            uuid.UUID(component["id"])
        except (ValueError, AttributeError):
            return False

        # Check data is dict (Phase 2: can be empty {})
        if not isinstance(component["data"], dict):
            return False

        return True

    except Exception:
        return False
