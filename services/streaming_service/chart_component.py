"""
ChartComponent creation and progressive data streaming handlers.

Handles all ChartComponent-related functionality including:
- Empty chart creation (Phase 4)
- Cumulative chart updates (Phase 4)
- Filled chart creation (Phase 4)
- Multi-chart support with same-type duplication (Phase 5.1)
"""

import asyncio
import re
from typing import AsyncGenerator, Dict
from datetime import datetime

from utils.id_generator import generate_uuid7
from .core import track_component, get_component_state, format_component, logger
from .constants import (
    STREAM_DELAY, CHART_POINT_DELAY, SIMULATE_PROCESSING_TIME,
    MAX_CHARTS_PER_RESPONSE, MAX_CHART_POINTS, CHART_TYPES_PRESET
)


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


def create_cumulative_chart_update(
    chart_id: str,
    new_values: list[float],
    series_label: str,
    active_components: Dict[str, dict]
) -> dict:
    """
    Append data points to an existing chart series with cumulative values (Phase 4).
    
    This adds new data points to an existing ChartComponent series.
    Backend MERGES values and sends CUMULATIVE array (not just new values).
    
    IMPORTANT: Unlike TableA rows (which only send new rows, with cumulative state tracked internally),
    ChartComponent updates send the FULL cumulative array, not just the increment. Frontend replaces the array completely.
    
    Args:
        chart_id: UUID for the chart component
        new_values: List of new data points to add
        series_label: Label for the data series
        active_components: Request-scoped component tracking dictionary
        
    Returns:
        dict: ChartComponent update with CUMULATIVE values array
        
    Example:
        >>> # Initial state: []
        >>> update1 = create_cumulative_chart_update("chart-1", [1000], "Sales", {})
        >>> # Returns: {"series": [{"label": "Sales", "values": [1000]}]}
        >>> 
        >>> update2 = create_cumulative_chart_update("chart-1", [1200], "Sales", {})
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


def _determine_chart_count(user_message_lower: str) -> int:
    """Extract number of charts from user message."""
    if "three" in user_message_lower or "3" in user_message_lower:
        return 3
    if any(kw in user_message_lower for kw in ["two", "2", "multiple", "several"]):
        return 2
    return 1


def _detect_bar_chart_presets(user_message_lower: str) -> list[str]:
    """Detect bar chart presets from user message."""
    if not re.search(r'\b(bar|revenue|performance)\b', user_message_lower):
        return []
    
    if "revenue" in user_message_lower:
        return ["revenue_bar"]
    if "performance" in user_message_lower:
        return ["performance_bar"]
    if "bar" in user_message_lower:
        return ["revenue_bar"]
    return []


def _detect_line_chart_presets(user_message_lower: str) -> list[str]:
    """Detect line chart presets from user message."""
    if not re.search(r'\b(line|trend|growth|sales)\b', user_message_lower):
        return []
    
    if "growth" in user_message_lower:
        return ["growth_line"]
    if "sales" in user_message_lower:
        return ["sales_line"]
    if "line" in user_message_lower or "trend" in user_message_lower:
        return ["sales_line"]
    return []


def _detect_chart_presets(user_message_lower: str) -> list[str]:
    """Detect which chart presets are mentioned in the message."""
    chart_presets = []
    chart_presets.extend(_detect_bar_chart_presets(user_message_lower))
    chart_presets.extend(_detect_line_chart_presets(user_message_lower))
    return chart_presets if chart_presets else ["sales_line"]


def _resolve_chart_presets(num_charts: int, detected_presets: list[str]) -> list[str]:
    """Resolve final chart presets based on count and detected presets."""
    # Detect if user wants multiple of the same type (Phase 5.1)
    same_type_requested = (num_charts > 1 and len(detected_presets) == 1)
    
    if same_type_requested:
        # Duplicate same preset (e.g., "two line charts")
        return detected_presets * num_charts
    
    if num_charts > len(detected_presets):
        # Fill with mixed presets
        all_presets = ["sales_line", "revenue_bar", "growth_line", "performance_bar"]
        result = detected_presets.copy()
        for preset in all_presets:
            if preset not in result:
                result.append(preset)
                if len(result) >= num_charts:
                    break
        return result[:num_charts]
    
    return detected_presets[:num_charts]


def _prepare_chart_data(chart_presets: list[str]) -> list[dict]:
    """Prepare data structures for all charts."""
    charts_data = []
    for chart_preset in chart_presets:
        # Get preset chart data
        preset_data = CHART_TYPES_PRESET.get(chart_preset, {
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
        all_values = all_values[:MAX_CHART_POINTS]
        
        charts_data.append({
            "preset": chart_preset,
            "chart_type": chart_type,
            "title": title,
            "x_axis": x_axis,
            "series_label": series_label,
            "values": all_values,
            "id": generate_uuid7()
        })
    return charts_data


async def _send_empty_charts(charts_data: list[dict], active_components: Dict[str, dict]) -> AsyncGenerator[bytes, None]:
    """Send empty chart skeletons."""
    for chart_info in charts_data:
        empty_chart = create_empty_chart(
            chart_info["id"],
            chart_info["chart_type"],
            chart_info["title"],
            chart_info["x_axis"],
            active_components
        )
        yield format_component(empty_chart).encode("utf-8")
        await asyncio.sleep(0.1)


async def _send_chart_loading_text(num_charts: int, charts_data: list[dict]) -> AsyncGenerator[bytes, None]:
    """Send loading text while processing charts."""
    yield "\n".encode("utf-8")
    
    if num_charts == 1:
        loading_text = f"Generating {charts_data[0]['chart_type']} chart"
    else:
        loading_text = f"Generating all {num_charts} charts"
    
    for word in loading_text.split():
        yield f"{word} ".encode("utf-8")
        await asyncio.sleep(STREAM_DELAY)
    
    if SIMULATE_PROCESSING_TIME:
        for _ in range(3):
            yield ".".encode("utf-8")
            await asyncio.sleep(0.3)
    
    yield "\n".encode("utf-8")


async def _stream_chart_points(charts_data: list[dict], active_components: Dict[str, dict]) -> AsyncGenerator[bytes, None]:
    """Stream data points progressively for all charts (interleaved)."""
    max_points = max(len(c["values"]) for c in charts_data)
    
    for point_idx in range(max_points):
        for chart_info in charts_data:
            if point_idx < len(chart_info["values"]):
                value = chart_info["values"][point_idx]
                data_update = create_cumulative_chart_update(
                    chart_info["id"],
                    [value],
                    chart_info["series_label"],
                    active_components
                )
                yield format_component(data_update).encode("utf-8")
                await asyncio.sleep(CHART_POINT_DELAY)
        
        # Stream progress text every few points
        if (point_idx + 1) % 2 == 0 and point_idx < max_points - 1:
            yield f"\nLoaded {point_idx + 1}/{max_points} points...\n".encode("utf-8")


async def _send_chart_completion_message(num_charts: int, charts_data: list[dict]) -> AsyncGenerator[bytes, None]:
    """Send completion message after all charts loaded."""
    total_points = sum(len(c["values"]) for c in charts_data)
    
    if num_charts == 1:
        yield f"\n✓ Chart completed with {len(charts_data[0]['values'])} data points!".encode("utf-8")
    else:
        yield f"\n✓ All {num_charts} charts completed with {total_points} total data points!".encode("utf-8")


async def handle_charts(user_message_lower: str, active_components: Dict[str, dict]) -> AsyncGenerator[bytes, None]:
    """
    Handle Pattern 5: ChartComponent with progressive data streaming (Phase 4 + Phase 5 Multi-Chart Support).
    
    Args:
        user_message_lower: Lowercase user message for pattern detection
        active_components: Request-scoped component tracking dictionary
        
    Yields:
        bytes: UTF-8 encoded chunks
    """
    logger.info("Pattern: ChartComponent with progressive data streaming (multi-chart support)")
    
    # Determine configuration from user message
    num_charts = _determine_chart_count(user_message_lower)
    detected_presets = _detect_chart_presets(user_message_lower)
    chart_presets = _resolve_chart_presets(num_charts, detected_presets)
    
    # Limit to max setting
    num_charts = min(len(chart_presets), MAX_CHARTS_PER_RESPONSE)
    chart_presets = chart_presets[:num_charts]
    
    # Prepare all charts data
    charts_data = _prepare_chart_data(chart_presets)
    
    # Stage 1: Send all empty charts first
    async for chunk in _send_empty_charts(charts_data, active_components):
        yield chunk
    
    # Stage 2: Stream loading text
    async for chunk in _send_chart_loading_text(num_charts, charts_data):
        yield chunk
    
    # Stage 3: Stream data points progressively
    async for chunk in _stream_chart_points(charts_data, active_components):
        yield chunk
    
    # Stage 4: Send completion message
    async for chunk in _send_chart_completion_message(num_charts, charts_data):
        yield chunk
    
    # Log completion
    for chart_info in charts_data:
        logger.info(f"Completed ChartComponent streaming: {chart_info['id']} ({chart_info['chart_type']}) with {len(chart_info['values'])} points")
