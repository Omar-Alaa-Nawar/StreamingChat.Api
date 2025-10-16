"""
Pattern detection and routing for streaming service.

Centralizes pattern matching logic and delegates to appropriate
component handlers based on user message content.
"""

import asyncio
import re
from typing import AsyncGenerator, Dict

from .core import logger
from . import simple_component
from . import table_component
from . import chart_component
from .constants import (
    DELAYED_KEYWORDS, CARD_KEYWORDS, MULTI_KEYWORDS,
    TABLE_KEYWORDS, CHART_KEYWORDS, LOADING_KEYWORDS, STREAM_DELAY
)


# ============================================================================
# Pattern Type Definitions
# ============================================================================

class PatternType:
    """Pattern type constants for routing."""
    DELAYED_SINGLE_CARD = "delayed_single_card"
    SINGLE_CARD = "single_card"
    DELAYED_MULTI_CARDS = "delayed_multi_cards"
    NORMAL_MULTI_CARDS = "normal_multi_cards"
    INCREMENTAL_LOADING = "incremental_loading"
    TABLE_REQUEST = "table_request"
    CHART_REQUEST = "chart_request"
    DEFAULT_TEXT = "default_text"


def _detect_pattern_type(user_message_lower: str) -> str:
    """Detect which pattern type matches the user message."""
    if _is_delayed_single_card(user_message_lower):
        return PatternType.DELAYED_SINGLE_CARD
    
    if _is_single_card(user_message_lower):
        return PatternType.SINGLE_CARD
    
    if _is_delayed_multi_cards(user_message_lower):
        return PatternType.DELAYED_MULTI_CARDS
    
    if _is_normal_multi_cards(user_message_lower):
        return PatternType.NORMAL_MULTI_CARDS
    
    if _is_incremental_loading(user_message_lower):
        return PatternType.INCREMENTAL_LOADING
    
    if _is_table_request(user_message_lower):
        return PatternType.TABLE_REQUEST
    
    if _is_chart_request(user_message_lower):
        return PatternType.CHART_REQUEST
    
    return PatternType.DEFAULT_TEXT


async def _route_to_handler(
    pattern_type: str,
    user_message_lower: str,
    active_components: Dict[str, dict]
) -> AsyncGenerator[bytes, None]:
    """Route to appropriate handler based on pattern type."""
    # Simple patterns (no parameters needed)
    simple_patterns = {
        PatternType.DELAYED_SINGLE_CARD: lambda: simple_component.generate_card_with_delay(active_components),
        PatternType.SINGLE_CARD: lambda: simple_component.handle_single_card(active_components),
        PatternType.INCREMENTAL_LOADING: lambda: simple_component.handle_incremental_loading(active_components),
    }
    
    # Multi-card patterns (need card count)
    multi_card_patterns = {
        PatternType.DELAYED_MULTI_CARDS: simple_component.handle_delayed_cards,
        PatternType.NORMAL_MULTI_CARDS: simple_component.handle_normal_cards,
    }
    
    # Complex patterns (need full message)
    complex_patterns = {
        PatternType.TABLE_REQUEST: table_component.handle_tables,
        PatternType.CHART_REQUEST: chart_component.handle_charts,
    }
    
    if pattern_type in simple_patterns:
        async for chunk in simple_patterns[pattern_type]():
            yield chunk
    elif pattern_type in multi_card_patterns:
        num_cards = _extract_card_count(user_message_lower)
        async for chunk in multi_card_patterns[pattern_type](num_cards, active_components):
            yield chunk
    elif pattern_type in complex_patterns:
        async for chunk in complex_patterns[pattern_type](user_message_lower, active_components):
            yield chunk
    else:  # DEFAULT_TEXT
        async for chunk in _generate_default_response():
            yield chunk


async def generate_chunks(user_message: str) -> AsyncGenerator[bytes, None]:
    """
    Generate streaming response with progressive component updates.

    Phase 6 Implementation (NEW):
    - LLM-Driven component generation for intelligent queries
    - Uses AWS Bedrock (Claude 3.5 Haiku) for dynamic planning
    - Routes to LLM planner when AI/dashboard keywords detected

    Phase 3-5 Implementation:
    - Extends Phase 2 with TableA component support
    - Streams table rows progressively: skeleton → row-by-row → complete
    - Maintains backward compatibility with all Phase 2 patterns
    - Supports multiple component types: SimpleComponent, TableA, ChartComponent

    Phase 2.1 Fix:
    - Added delayed card update pattern (5-second delay)
    - Validates progressive component lifecycle with timing

    Flow:
    1. Check for LLM keywords → Route to LLM planner (Phase 6)
    2. Otherwise: Detect user intent from message (legacy pattern matching)
    3. Send empty component(s) as placeholder(s)
    4. Stream explanatory text while "loading"
    5. Update component(s) with actual data (incrementally for tables)
    6. Stream completion message

    Supported patterns:
    - LLM-driven component generation (Phase 6 NEW)
    - Single component with progressive load
    - Multiple components with staggered updates
    - Mixed text and components
    - Incremental data updates
    - Delayed card update (5-second delay) - Phase 2.1
    - TableA with progressive row streaming (Phase 3)
    - ChartComponent with progressive data streaming (Phase 4)

    Args:
        user_message: The user's input message

    Yields:
        bytes: UTF-8 encoded chunks (text or JSON components)

    Example Output (LLM Mode):
        User: "show me ai dashboard with sales trends"

        Stream:
        1. $$${"type":"SimpleComponent","id":"...","data":{"title":"Sales Dashboard"}}$$$
        2. $$${"type":"ChartComponent","id":"...","data":{"chart_type":"line",...}}$$$
        3. $$${"type":"TableA","id":"...","data":{"columns":[...],"rows":[...]}}$$$

    Example Output (Legacy TableA):
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

    # Phase 6: LLM-Driven Planning
    # ----------------------------------------------------------------------------
    # LLM Keyword Detection Pattern
    # This regex determines whether the user's message should be routed to the LLM planner.
    # Matches if any of the following keywords appear as whole words (case-insensitive):
    #   ai, llm, plan, analyze, dashboard, intelligent, smart, insight, insights, summary
    #
    # Example matches (will trigger LLM routing):
    #   "Show me an AI dashboard"
    #   "Can you analyze this data?"
    #   "Give me a summary of sales"
    #   "I want smart insights"
    #   "Generate a plan for Q2"
    #
    # Example non-matches (will NOT trigger LLM routing):
    #   "Show me sales table"
    #   "List all customers"
    #   "Display chart of revenue"
    #   "What is the total revenue?"
    # ----------------------------------------------------------------------------
    llm_keywords = re.search(
        r'\b(ai|llm|plan|analyze|dashboard|intelligent|smart|insights?|summary)\b',
        user_message_lower
    )

    if llm_keywords:
        logger.info("🧠 Phase 6: Routing to LLM Planner Service")
        try:
            from services.llm import llm_planner_service
            from .core import format_component

            # Generate layout using LLM
            layout = await llm_planner_service.generate_layout(user_message)

            # Stream components directly (no progressive loading for LLM mode)
            for component in layout["components"]:
                formatted = format_component(component)
                yield formatted.encode("utf-8")
                await asyncio.sleep(0.1)  # Small delay between components

            # Log success
            num_components = len(layout["components"])
            from_cache = layout.get("from_cache", False)
            processing_time = layout.get("processing_time_ms", 0)
            logger.info(
                f"✓ LLM generated {num_components} components "
                f"in {processing_time:.1f}ms (cached: {from_cache})"
            )
            return

        except ImportError:
            logger.warning("LLM service not available, falling back to pattern matching")
        except Exception as e:
            logger.error(f"LLM planning failed: {e}, falling back to pattern matching")

    # Legacy pattern matching (Phase 0-5)
    # Detect pattern and route to appropriate handler
    pattern_type = _detect_pattern_type(user_message_lower)
    async for chunk in _route_to_handler(pattern_type, user_message_lower, active_components):
        yield chunk


# ============================================================================
# Pattern Detection Helpers
# ============================================================================

def _is_delayed_single_card(message_lower: str) -> bool:
    """Check if user wants a single delayed/partial card."""
    has_delayed_keyword = any(kw in message_lower for kw in DELAYED_KEYWORDS)
    has_card_keyword = any(kw in message_lower for kw in ["card"])
    has_multi_keyword = any(kw in message_lower for kw in MULTI_KEYWORDS)
    
    return has_delayed_keyword and has_card_keyword and not has_multi_keyword


def _is_single_card(message_lower: str) -> bool:
    """Check if user wants a single card (not delayed, not multiple)."""
    has_card_keyword = "card" in message_lower
    has_multi_keyword = any(kw in message_lower for kw in MULTI_KEYWORDS)
    
    return has_card_keyword and not has_multi_keyword


def _is_delayed_multi_cards(message_lower: str) -> bool:
    """Check if user wants multiple delayed cards."""
    has_delayed_keyword = any(kw in message_lower for kw in DELAYED_KEYWORDS)
    has_card_keyword = re.search(r'\b(cards?|components?)\b', message_lower) is not None
    has_multi_keyword = any(kw in message_lower for kw in MULTI_KEYWORDS)
    
    return has_delayed_keyword and has_card_keyword and has_multi_keyword


def _is_normal_multi_cards(message_lower: str) -> bool:
    """Check if user wants multiple normal cards (not delayed, not table/chart)."""
    has_card_pattern = re.search(r'\b(cards?|components?)\b', message_lower) is not None
    has_multi_keyword = any(kw in message_lower for kw in MULTI_KEYWORDS)
    
    # Exclude table/chart keywords to avoid conflicts
    # Split into multiple simpler patterns for SonarQube
    has_table_keywords = bool(re.search(r'\b(tables?|sales|users?|products?)\b', message_lower))
    has_chart_keywords = bool(re.search(r'\b(charts?|lines?|bars?|graphs?|plots?)\b', message_lower))
    has_metric_keywords = bool(re.search(r'\b(trends?|revenue|growth|performance|metrics?)\b', message_lower))
    
    has_table_chart_keywords = has_table_keywords or has_chart_keywords or has_metric_keywords
    
    return (has_card_pattern or has_multi_keyword) and not has_table_chart_keywords


def _is_incremental_loading(message_lower: str) -> bool:
    """Check if user wants incremental loading demonstration."""
    return any(kw in message_lower for kw in LOADING_KEYWORDS)


def _is_table_request(message_lower: str) -> bool:
    """Check if user wants a table."""
    return re.search(r'\b(tables?|sales|users?|products?)\b', message_lower) is not None


def _is_chart_request(message_lower: str) -> bool:
    """Check if user wants a chart."""
    # Split into multiple simpler patterns for SonarQube
    has_chart_types = bool(re.search(r'\b(charts?|lines?|bars?|graphs?|plots?)\b', message_lower))
    has_chart_contexts = bool(re.search(r'\b(trends?|revenue|growth|performance|metrics?)\b', message_lower))
    return has_chart_types or has_chart_contexts


def _extract_card_count(message_lower: str) -> int:
    """Extract number of cards/components from user message."""
    if "three" in message_lower or "3" in message_lower:
        return 3
    elif "four" in message_lower or "4" in message_lower:
        return 4
    elif "five" in message_lower or "5" in message_lower:
        return 5
    else:
        return 2  # Default for "two", "multiple", "several"


async def _generate_default_response() -> AsyncGenerator[bytes, None]:
    """Generate default text-only response when no pattern matches."""
    logger.info("Pattern: Text-only response (no components)")
    
    from .constants import STREAM_DELAY
    
    response_text = (
        "This is a text-only response. "
        "Try asking for 'a card', 'two cards', 'show me loading states', 'show me a table', or 'show me a chart' "
        "to see Phase 4 progressive component rendering in action!"
    )
    
    words = response_text.split()
    for word in words:
        yield f"{word} ".encode("utf-8")
        await asyncio.sleep(STREAM_DELAY)


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
