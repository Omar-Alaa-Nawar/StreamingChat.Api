"""
Streaming service for handling real-time text and component streaming.

This service provides the core streaming functionality for the StreamForge backend.
Phase 1: Streams both text and JSON components using Server-Sent Events (SSE).

Components are wrapped with $$ delimiters:
$${"type":"SimpleComponent","id":"uuid","data":{...}}$$
"""

import asyncio
import json
import uuid
from typing import AsyncGenerator
from datetime import datetime, timezone
from config.settings import settings
from utils.id_generator import generate_uuid7
from schemas.component_schemas import ComponentData, SimpleComponentData


def create_simple_component(
    title: str = "Sample Card",
    description: str = "This is a sample component",
    value: int = 100
) -> dict:
    """
    Create a SimpleComponent with fake data.

    Args:
        title: Component title/heading
        description: Component description text
        value: Optional numeric value

    Returns:
        dict: Component data structure ready for streaming

    Example:
        >>> component = create_simple_component("Test", "Description", 42)
        >>> print(component)
        {
            "type": "SimpleComponent",
            "id": "01932e4f-a4c2-7890-b123-456789abcdef",
            "data": {
                "title": "Test",
                "description": "Description",
                "value": 42,
                "timestamp": "2025-10-14T12:34:56.789Z"
            }
        }
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


async def generate_chunks(user_message: str) -> AsyncGenerator[bytes, None]:
    """
    Generate streaming response with mixed text and JSON components.

    Phase 1 Implementation:
    - Analyzes user message to determine if components should be sent
    - Streams text chunks word-by-word
    - Streams JSON components wrapped in $$ delimiters
    - Simulates LLM decision-making for component generation

    Flow:
    1. Check if user requests components (keywords: card, component, show, give)
    2. Stream appropriate response (text only OR text + components)
    3. Each component is formatted as: $$<JSON>$$
    4. Text chunks are sent with trailing spaces

    Args:
        user_message: The user's input message

    Yields:
        bytes: UTF-8 encoded chunks (text or JSON components)

    Example Output:
        For "show me a card":
        - "Here's " (text)
        - "a " (text)
        - "component " (text)
        - "for " (text)
        - "you: " (text)
        - $${"type":"SimpleComponent",...}$$ (component)
        - " " (text)
        - "Hope " (text)
        - "this " (text)
        - "helps!" (text)
    """
    user_message_lower = user_message.lower()

    # Simulate LLM decision-making: Check if user wants components
    wants_component = any(keyword in user_message_lower for keyword in [
        "card", "component", "show", "give", "display", "create"
    ])

    # Check if user wants multiple components
    wants_multiple = any(keyword in user_message_lower for keyword in [
        "two", "2", "three", "3", "multiple", "several", "few"
    ])

    if wants_component:
        if wants_multiple:
            # Generate response with multiple components
            async for chunk in stream_text_with_multiple_components(user_message):
                yield chunk
            return

        # Generate response with single component
        # Stream initial text
        intro_text = "Here's a component for you: "
        for word in intro_text.split():
            yield f"{word} ".encode("utf-8")
            await asyncio.sleep(settings.STREAM_DELAY)

        # Stream JSON component with $$ delimiters
        component = create_simple_component(
            title="Sample Card",
            description="This is a dynamically generated component based on your request",
            value=100
        )

        # Format as: $$<JSON>$$
        component_json = json.dumps(component, separators=(',', ':'))  # Compact JSON
        component_str = f"{settings.COMPONENT_DELIMITER}{component_json}{settings.COMPONENT_DELIMITER}"

        # Stream component character-by-character to trigger skeleton loaders
        for char in component_str:
            yield char.encode("utf-8")
            await asyncio.sleep(0.01)  # 10ms per character = ~100 chars/second (visible streaming)

        # Stream closing text
        closing_text = " Hope this helps!"
        for word in closing_text.split():
            yield f"{word} ".encode("utf-8")
            await asyncio.sleep(settings.STREAM_DELAY)

    else:
        # No components requested - stream text only (Phase 0 behavior)
        response_text = (
            "This is a simulated streaming response from the LLM. "
            "Each word appears one at a time. "
            "Try asking for a 'card' or 'component' to see JSON streaming!"
        )

        words = response_text.split()
        for word in words:
            yield f"{word} ".encode("utf-8")
            await asyncio.sleep(settings.STREAM_DELAY)


async def stream_text_with_multiple_components(user_message: str) -> AsyncGenerator[bytes, None]:
    """
    Generate streaming response with multiple JSON components.

    Used when user explicitly asks for multiple components.

    Args:
        user_message: The user's input message

    Yields:
        bytes: UTF-8 encoded chunks with multiple components

    Example:
        For "give me two components":
        - Text intro
        - Component 1
        - Text middle
        - Component 2
        - Text closing
    """
    # Stream intro text
    intro = "Here are your components: "
    for word in intro.split():
        yield f"{word} ".encode("utf-8")
        await asyncio.sleep(settings.STREAM_DELAY)

    # Stream first component character-by-character
    component1 = create_simple_component(
        title="First Component",
        description="This is the first component in the sequence",
        value=1
    )
    component1_json = json.dumps(component1, separators=(',', ':'))
    component1_str = f"{settings.COMPONENT_DELIMITER}{component1_json}{settings.COMPONENT_DELIMITER}"

    for char in component1_str:
        yield char.encode("utf-8")
        await asyncio.sleep(0.01)  # 10ms per character

    # Stream middle text
    middle = " and here's another one: "
    for word in middle.split():
        yield f"{word} ".encode("utf-8")
        await asyncio.sleep(settings.STREAM_DELAY)

    # Stream second component character-by-character
    component2 = create_simple_component(
        title="Second Component",
        description="This is the second component with different data",
        value=2
    )
    component2_json = json.dumps(component2, separators=(',', ':'))
    component2_str = f"{settings.COMPONENT_DELIMITER}{component2_json}{settings.COMPONENT_DELIMITER}"

    for char in component2_str:
        yield char.encode("utf-8")
        await asyncio.sleep(0.01)  # 10ms per character

    # Stream closing text
    closing = " Let me know if you need more!"
    for word in closing.split():
        yield f"{word} ".encode("utf-8")
        await asyncio.sleep(settings.STREAM_DELAY)


async def generate_llm_stream(user_message: str) -> AsyncGenerator[bytes, None]:
    """
    Future: Generate streaming response from actual LLM.

    This function will be implemented when integrating with LangChain.
    It will invoke the LLM chain and stream the response back to the client.

    Phase 2+ Implementation:
    - Real LLM will decide when to generate components
    - LLM will provide component parameters
    - Streaming will be based on actual token generation

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
    - Data is a dictionary

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

        # Check data is dict
        if not isinstance(component["data"], dict):
            return False

        return True

    except Exception:
        return False
