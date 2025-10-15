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
from typing import AsyncGenerator, Dict
from datetime import datetime, timezone
from config.settings import settings
from utils.id_generator import generate_uuid7
from schemas.component_schemas import ComponentData, SimpleComponentData

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Track components in current response (Phase 2)
active_components: Dict[str, dict] = {}


def track_component(component_id: str, data: dict):
    """
    Track component state during streaming.
    
    Args:
        component_id: UUID of the component
        data: Current data state of the component
    """
    active_components[component_id] = data
    logger.info(f"Tracking component: {component_id}")


def get_component_state(component_id: str) -> dict:
    """
    Get current state of tracked component.
    
    Args:
        component_id: UUID of the component
        
    Returns:
        dict: Component data or empty dict if not found
    """
    return active_components.get(component_id, {})


def create_empty_component(component_id: str) -> dict:
    """
    Create empty component placeholder (Phase 2).
    
    This creates a component with no data, used to render
    an immediate placeholder in the frontend.
    
    Args:
        component_id: UUID for the component
        
    Returns:
        dict: Empty component structure
        
    Example:
        >>> comp = create_empty_component("abc-123")
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
    
    track_component(component_id, {})
    logger.info(f"Created empty component: {component_id}")
    
    return component


def create_filled_component(
    component_id: str,
    title: str,
    description: str,
    value: int
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
        
    Returns:
        dict: Filled component structure
        
    Example:
        >>> comp = create_filled_component("abc-123", "Card", "Data loaded", 100)
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
    
    track_component(component_id, data)
    logger.info(f"Filled component: {component_id} with data: {data}")
    
    return component


def create_partial_update(component_id: str, data: dict) -> dict:
    """
    Create partial data update for existing component (Phase 2).
    
    This allows incremental updates to a component's data.
    
    Args:
        component_id: UUID for the component
        data: Partial data to update
        
    Returns:
        dict: Component update structure
        
    Example:
        >>> update = create_partial_update("abc-123", {"title": "Loading..."})
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
    existing_data = get_component_state(component_id)
    merged_data = {**existing_data, **data}
    track_component(component_id, merged_data)
    
    logger.info(f"Partial update for component {component_id}: {data}")
    
    return component


def validate_component_update(component_id: str, data: dict) -> bool:
    """
    Validate component update before sending (Phase 2).
    
    Args:
        component_id: UUID of the component
        data: Data to validate
        
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



def create_simple_component(
    title: str = "Sample Card",
    description: str = "This is a sample component",
    value: int = 100
) -> dict:
    """
    Create a SimpleComponent with data (Legacy - Phase 1).
    
    DEPRECATED: Use create_filled_component() for Phase 2.
    Kept for backwards compatibility.

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


async def generate_card_with_delay() -> AsyncGenerator[bytes, None]:
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
    
    track_component(component_id, initial_data)
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
    existing_data = get_component_state(component_id)
    merged_data = {**existing_data, **partial_update["data"]}
    track_component(component_id, merged_data)
    
    component_json = json.dumps(partial_update, separators=(',', ':'))
    yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
    await asyncio.sleep(0.1)
    
    logger.info(f"Sent partial update (description+units) for component: {component_id}")
    
    logger.info(f"Completed partial progressive update for: {component_id}")


async def generate_chunks(user_message: str) -> AsyncGenerator[bytes, None]:
    """
    Generate streaming response with progressive component updates (Phase 2).

    Phase 2 Implementation:
    - Streams components in stages: empty → text → data
    - Supports multiple components (1-5) per response
    - Components matched by ID for updates
    - Simulates real-world data loading patterns

    Phase 2.1 Fix:
    - Added delayed card update pattern (5-second delay)
    - Validates progressive component lifecycle with timing

    Flow:
    1. Detect user intent from message
    2. Send empty component(s) as placeholder(s)
    3. Stream explanatory text while "loading"
    4. Update component(s) with actual data
    5. Stream completion message

    Supported patterns:
    - Single component with progressive load
    - Multiple components with staggered updates
    - Mixed text and components
    - Incremental data updates
    - Delayed card update (5-second delay) - Phase 2.1

    Args:
        user_message: The user's input message

    Yields:
        bytes: UTF-8 encoded chunks (text or JSON components)

    Example Output:
        User: "show me a card"
        
        Stream:
        1. $$${"type":"SimpleComponent","id":"abc","data":{}}$$$
        2. "Loading your card..."
        3. $$${"type":"SimpleComponent","id":"abc","data":{"title":"Card",...}}$$$
        4. " Done!"
    """
    # Clear active components for new response
    active_components.clear()
    
    user_message_lower = user_message.lower()

    # Pattern 0: Partial progressive update (Phase 2.1 Fix)
    # Triggered by "delayed card" or "partial card"
    if ("delayed" in user_message_lower or "partial" in user_message_lower) and "card" in user_message_lower:
        async for chunk in generate_card_with_delay():
            yield chunk
        return
    
    # Pattern 1: Single component with progressive loading
    if "card" in user_message_lower and not any(kw in user_message_lower for kw in ["two", "2", "three", "3", "multiple", "several"]):
        logger.info("Pattern: Single component with progressive loading")
        
        # Stage 1: Send empty component (creates placeholder)
        component_id = generate_uuid7()
        empty_component = create_empty_component(component_id)
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
            value=150
        )
        component_json = json.dumps(filled_component, separators=(',', ':'))
        yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
        await asyncio.sleep(settings.STREAM_DELAY)
        
        # Stage 4: Completion message
        yield " All set!".encode("utf-8")
        
        logger.info(f"Completed single component: {component_id}")
    
    # Pattern 2: Multiple components with progressive updates
    elif any(kw in user_message_lower for kw in ["two", "2", "three", "3", "multiple", "several"]):
        logger.info("Pattern: Multiple components with progressive updates")
        
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
            
            empty = create_empty_component(comp_id)
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
                value=(i+1) * 100
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
        empty = create_empty_component(component_id)
        component_json = json.dumps(empty, separators=(',', ':'))
        yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
        await asyncio.sleep(0.2)
        
        yield "Watch the card load incrementally... ".encode("utf-8")
        await asyncio.sleep(0.3)
        
        # Stage 2: Update with title only
        partial1 = create_partial_update(component_id, {"title": "Loading..."})
        component_json = json.dumps(partial1, separators=(',', ':'))
        yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
        await asyncio.sleep(0.5)
        
        # Stage 3: Update with title + description
        partial2 = create_partial_update(component_id, {
            "title": "Progressive Card",
            "description": "Description loaded..."
        })
        component_json = json.dumps(partial2, separators=(',', ':'))
        yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
        await asyncio.sleep(0.5)
        
        # Stage 4: Complete data
        filled = create_filled_component(
            component_id,
            title="Progressive Card",
            description="All data loaded successfully!",
            value=100
        )
        component_json = json.dumps(filled, separators=(',', ':'))
        yield f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}".encode("utf-8")
        await asyncio.sleep(0.2)
        
        yield " Done with incremental loading!".encode("utf-8")
        
        logger.info(f"Completed incremental updates for: {component_id}")
    
    # Pattern 4: Default text-only response
    else:
        logger.info("Pattern: Text-only response (no components)")
        
        response_text = (
            "This is a text-only response. "
            "Try asking for 'a card', 'two cards', or 'show me loading states' "
            "to see Phase 2 progressive component rendering in action!"
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
