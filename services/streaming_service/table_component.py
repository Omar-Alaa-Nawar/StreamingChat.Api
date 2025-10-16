"""
TableA component creation and progressive row streaming handlers.

Handles all TableA-related functionality including:
- Empty table creation (Phase 3)
- Progressive row updates (Phase 3)
- Filled table creation (Phase 3)
- Multi-table support with same-type duplication (Phase 5.1)
"""

import asyncio
import re
from typing import AsyncGenerator, Dict
from datetime import datetime

from utils.id_generator import generate_uuid7
from .core import track_component, get_component_state, format_component, logger
from .constants import (
    STREAM_DELAY, TABLE_ROW_DELAY, SIMULATE_PROCESSING_TIME,
    MAX_TABLES_PER_RESPONSE, MAX_TABLE_ROWS, TABLE_COLUMNS_PRESET
)


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
    # Merge with existing state
    existing_data = get_component_state(table_id, active_components)
    existing_rows = existing_data.get("rows", [])
    existing_columns = existing_data.get("columns", [])
    merged_rows = existing_rows + new_rows
    
    merged_data = {
        "columns": existing_columns,
        "rows": merged_rows
    }
    track_component(table_id, merged_data, active_components)
    
    logger.info(f"Added {len(new_rows)} row(s) to table {table_id}. Total rows: {len(merged_rows)}")
    
    # Include columns in the update so tests can identify table type
    component = {
        "type": "TableA",
        "id": table_id,
        "data": {
            "columns": existing_columns,
            "rows": new_rows
        }
    }
    
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


def get_sample_rows_for_table_type(table_type: str) -> list[list]:
    """
    Get sample data rows based on table type.
    
    Args:
        table_type: Type of table ("sales", "users", "products")
        
    Returns:
        list[list]: Sample rows for the table type
    """
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
    return sample_rows[:MAX_TABLE_ROWS]


def _determine_table_count(user_message_lower: str) -> int:
    """Extract number of tables from user message."""
    if "three" in user_message_lower or "3" in user_message_lower:
        return 3
    if any(kw in user_message_lower for kw in ["two", "2", "multiple", "several"]):
        return 2
    return 1


def _detect_table_types(user_message_lower: str) -> list[str]:
    """Detect which table types are mentioned in the message."""
    table_types = []
    if re.search(r'\bsales?\b', user_message_lower):
        table_types.append("sales")
    if re.search(r'\busers?\b', user_message_lower):
        table_types.append("users")
    if re.search(r'\bproducts?\b', user_message_lower):
        table_types.append("products")
    return table_types if table_types else ["sales"]


def _resolve_table_types(num_tables: int, detected_types: list[str]) -> list[str]:
    """Resolve final table types based on count and detected types."""
    # Detect if user wants multiple of the same type (Phase 5.1)
    same_type_requested = (num_tables > 1 and len(detected_types) == 1)
    
    if same_type_requested:
        # Duplicate same type (e.g., "two sales tables")
        return detected_types * num_tables
    
    if num_tables > len(detected_types):
        # Fill with mixed types
        all_types = ["sales", "users", "products"]
        result = detected_types.copy()
        for table_type in all_types:
            if table_type not in result:
                result.append(table_type)
                if len(result) >= num_tables:
                    break
        return result[:num_tables]
    
    return detected_types[:num_tables]


def _prepare_table_data(table_types: list[str]) -> list[dict]:
    """Prepare initial table data structures."""
    tables_data = []
    for table_type in table_types:
        columns = TABLE_COLUMNS_PRESET.get(table_type, ["Column 1", "Column 2", "Column 3"])
        sample_rows = get_sample_rows_for_table_type(table_type)
        
        tables_data.append({
            "id": generate_uuid7(),
            "type": table_type,
            "columns": columns,
            "rows": sample_rows
        })
    return tables_data


async def _send_empty_tables(tables_data: list[dict], active_components: Dict[str, dict]) -> AsyncGenerator[bytes, None]:
    """Send empty table skeletons."""
    for table_info in tables_data:
        empty_table = create_empty_table(table_info["id"], table_info["columns"], active_components)
        yield format_component(empty_table).encode("utf-8")
        await asyncio.sleep(0.1)


async def _send_loading_text(num_tables: int, table_types: list[str]) -> AsyncGenerator[bytes, None]:
    """Send loading text while processing."""
    yield "\n".encode("utf-8")
    if num_tables == 1:
        loading_text = f"Here's your {table_types[0]} table. Loading data"
    else:
        loading_text = f"Loading data for all {num_tables} tables"
    
    for word in loading_text.split():
        yield f"{word} ".encode("utf-8")
        await asyncio.sleep(STREAM_DELAY)
    
    if SIMULATE_PROCESSING_TIME:
        for _ in range(3):
            yield ".".encode("utf-8")
            await asyncio.sleep(0.3)
    
    yield "\n".encode("utf-8")


async def _stream_table_rows(tables_data: list[dict], active_components: Dict[str, dict]) -> AsyncGenerator[bytes, None]:
    """Stream rows progressively for all tables (interleaved)."""
    max_rows = max(len(t["rows"]) for t in tables_data)
    
    for row_idx in range(max_rows):
        for table_info in tables_data:
            if row_idx < len(table_info["rows"]):
                row = table_info["rows"][row_idx]
                row_update = create_table_row_update(table_info["id"], [row], active_components)
                yield format_component(row_update).encode("utf-8")
                await asyncio.sleep(TABLE_ROW_DELAY)
        
        # Stream progress text every few rounds
        if (row_idx + 1) % 2 == 0 and row_idx < max_rows - 1:
            total_rows_loaded = sum(min(row_idx + 1, len(t["rows"])) for t in tables_data)
            yield f"Loaded {total_rows_loaded} rows... ".encode("utf-8")


async def _send_completion_message(num_tables: int, tables_data: list[dict]) -> AsyncGenerator[bytes, None]:
    """Send completion message."""
    total_rows = sum(len(t["rows"]) for t in tables_data)
    if num_tables == 1:
        yield f"\n✓ All {len(tables_data[0]['rows'])} rows loaded successfully!".encode("utf-8")
    else:
        yield f"\n✓ All {num_tables} tables loaded with {total_rows} total rows!".encode("utf-8")


async def handle_tables(user_message_lower: str, active_components: Dict[str, dict]) -> AsyncGenerator[bytes, None]:
    """
    Handle Pattern 4: TableA with progressive row streaming (Phase 3 + Phase 5 Multi-Table Support).
    
    Args:
        user_message_lower: Lowercase user message for pattern detection
        active_components: Request-scoped component tracking dictionary
        
    Yields:
        bytes: UTF-8 encoded chunks
    """
    logger.info("Pattern: TableA with progressive row streaming (multi-table support)")
    
    # Determine configuration from user message
    num_tables = _determine_table_count(user_message_lower)
    detected_types = _detect_table_types(user_message_lower)
    table_types = _resolve_table_types(num_tables, detected_types)
    
    # Limit to max setting
    num_tables = min(len(table_types), MAX_TABLES_PER_RESPONSE)
    table_types = table_types[:num_tables]
    
    # Prepare all tables data
    tables_data = _prepare_table_data(table_types)
    
    # Stage 1: Send all empty tables first
    async for chunk in _send_empty_tables(tables_data, active_components):
        yield chunk
    
    # Stage 2: Stream loading text
    async for chunk in _send_loading_text(num_tables, table_types):
        yield chunk
    
    # Stage 3: Stream rows progressively
    async for chunk in _stream_table_rows(tables_data, active_components):
        yield chunk
    
    # Stage 4: Send completion message
    async for chunk in _send_completion_message(num_tables, tables_data):
        yield chunk
    
    # Log completion
    for table_info in tables_data:
        logger.info(f"Completed TableA streaming: {table_info['id']} ({table_info['type']}) with {len(table_info['rows'])} rows")
