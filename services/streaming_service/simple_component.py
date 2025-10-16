"""
SimpleComponent creation and progressive update handlers.

Handles all SimpleComponent-related functionality including:
- Empty component creation (Phase 2)
- Filled component creation (Phase 2)
- Partial updates (Phase 2)
- Delayed card pattern (Phase 2.1)
- Multi-card support with delayed updates (Phase 5.2)
- Legacy Phase 1 support
"""

import asyncio
import json
from typing import AsyncGenerator, Dict
from datetime import datetime, timezone

from utils.id_generator import generate_uuid7
from schemas.component_schemas import ComponentData, SimpleComponentData
from .core import track_component, get_component_state, format_component, logger
from .constants import (
    STREAM_DELAY, COMPONENT_UPDATE_DELAY, 
    SIMULATE_PROCESSING_TIME, MAX_COMPONENTS_PER_RESPONSE
)


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
    yield format_component(initial_component).encode("utf-8")
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
    
    yield format_component(partial_update).encode("utf-8")
    await asyncio.sleep(0.1)
    
    logger.info(f"Sent partial update (description+units) for component: {component_id}")
    logger.info(f"Completed partial progressive update for: {component_id}")


async def handle_single_card(active_components: Dict[str, dict]) -> AsyncGenerator[bytes, None]:
    """
    Handle Pattern 1: Single component with progressive loading.
    
    Args:
        active_components: Request-scoped component tracking dictionary
        
    Yields:
        bytes: UTF-8 encoded chunks
    """
    logger.info("Pattern: Single component with progressive loading")
    
    # Stage 1: Send empty component (creates placeholder)
    component_id = generate_uuid7()
    empty_component = create_empty_component(component_id, active_components)
    yield format_component(empty_component).encode("utf-8")
    await asyncio.sleep(STREAM_DELAY)
    
    # Stage 2: Stream text while "processing"
    loading_text = "Generating your card"
    for word in loading_text.split():
        yield f"{word} ".encode("utf-8")
        await asyncio.sleep(STREAM_DELAY)
    
    # Simulate processing time
    if SIMULATE_PROCESSING_TIME:
        for _ in range(3):
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
    yield format_component(filled_component).encode("utf-8")
    await asyncio.sleep(STREAM_DELAY)
    
    # Stage 4: Completion message
    yield " All set!".encode("utf-8")
    
    logger.info(f"Completed single component: {component_id}")


async def handle_delayed_cards(num_cards: int, active_components: Dict[str, dict]) -> AsyncGenerator[bytes, None]:
    """
    Handle Pattern 2: Multi-SimpleComponent with DELAYED updates (Phase 5.2).
    
    Args:
        num_cards: Number of delayed cards to create
        active_components: Request-scoped component tracking dictionary
        
    Yields:
        bytes: UTF-8 encoded chunks
    """
    logger.info("Pattern: Progressive SimpleComponent (multi-card support with delayed updates)")
    
    # Limit to max
    num_cards = min(num_cards, MAX_COMPONENTS_PER_RESPONSE)
    
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
        yield format_component(initial_component).encode("utf-8")
        await asyncio.sleep(0.05)  # Quick succession
        
        logger.info(f"Sent initial delayed card with title+date+description: {cid}")
    
    # Stage 2: Simulate delay (data loading/processing)
    delay_seconds = 3.0  # 3 seconds for multiple cards (faster than single card's 5s)
    yield f"\nProcessing {num_cards} delayed card{'s' if num_cards > 1 else ''}".encode("utf-8")
    
    if SIMULATE_PROCESSING_TIME:
        for _ in range(3):
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
        
        yield format_component(partial_update).encode("utf-8")
        await asyncio.sleep(0.1)
        
        logger.info(f"Sent partial update (description+units) for card: {cid}")
    
    # Stage 4: Completion message
    yield f"\n✓ All {num_cards} delayed card{'s' if num_cards > 1 else ''} completed!\n".encode("utf-8")
    
    logger.info(f"Completed {num_cards} progressive delayed cards with partial updates")


async def handle_normal_cards(num_components: int, active_components: Dict[str, dict]) -> AsyncGenerator[bytes, None]:
    """
    Handle Pattern 2b: Multi-SimpleComponent (Normal cards without delay) - Legacy behavior.
    
    Args:
        num_components: Number of cards to create
        active_components: Request-scoped component tracking dictionary
        
    Yields:
        bytes: UTF-8 encoded chunks
    """
    logger.info("Pattern: Multiple components with progressive updates (normal cards)")
    
    # Limit to max
    num_components = min(num_components, MAX_COMPONENTS_PER_RESPONSE)
    
    # Stage 1: Send all empty components first
    component_ids = []
    for i in range(num_components):
        comp_id = generate_uuid7()
        component_ids.append(comp_id)
        
        empty = create_empty_component(comp_id, active_components)
        yield format_component(empty).encode("utf-8")
        await asyncio.sleep(0.1)  # Quick succession
    
    # Stage 2: Stream text while "loading"
    loading_text = f"Loading data for all {num_components} cards"
    for word in loading_text.split():
        yield f"{word} ".encode("utf-8")
        await asyncio.sleep(STREAM_DELAY)
    
    # Simulate processing
    if SIMULATE_PROCESSING_TIME:
        for _ in range(3):
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
        yield format_component(filled).encode("utf-8")
        await asyncio.sleep(COMPONENT_UPDATE_DELAY)
    
    # Stage 4: Completion
    yield " Complete!".encode("utf-8")
    
    logger.info(f"Completed {num_components} components")


async def handle_incremental_loading(active_components: Dict[str, dict]) -> AsyncGenerator[bytes, None]:
    """
    Handle Pattern 3: Incremental updates (loading states).
    
    Args:
        active_components: Request-scoped component tracking dictionary
        
    Yields:
        bytes: UTF-8 encoded chunks
    """
    logger.info("Pattern: Incremental component updates")
    
    component_id = generate_uuid7()
    
    # Stage 1: Empty component
    empty = create_empty_component(component_id, active_components)
    yield format_component(empty).encode("utf-8")
    await asyncio.sleep(0.2)
    
    yield "Watch the card load incrementally... ".encode("utf-8")
    await asyncio.sleep(0.3)
    
    # Stage 2: Update with title only
    partial1 = create_partial_update(component_id, {"title": "Loading..."}, active_components)
    yield format_component(partial1).encode("utf-8")
    await asyncio.sleep(0.5)
    
    # Stage 3: Update with title + description
    partial2 = create_partial_update(component_id, {
        "title": "Progressive Card",
        "description": "Description loaded..."
    }, active_components)
    yield format_component(partial2).encode("utf-8")
    await asyncio.sleep(0.5)
    
    # Stage 4: Complete data
    filled = create_filled_component(
        component_id,
        title="Progressive Card",
        description="All data loaded successfully!",
        value=100,
        active_components=active_components
    )
    yield format_component(filled).encode("utf-8")
    await asyncio.sleep(0.2)
    
    yield " Done with incremental loading!".encode("utf-8")
    
    logger.info(f"Completed incremental updates for: {component_id}")
