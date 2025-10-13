"""
Streaming service for handling real-time text streaming.

This service provides the core streaming functionality for the StreamForge backend.
It simulates LLM-style streaming responses using async generators and Server-Sent Events.
"""

import asyncio
from typing import AsyncGenerator
from config.settings import settings


async def generate_chunks(user_message: str) -> AsyncGenerator[bytes, None]:
    """
    Generate streaming response chunks word-by-word.

    This function simulates an LLM streaming response by breaking text into
    words and yielding them one at a time with realistic delays. Each chunk
    is UTF-8 encoded bytes suitable for Server-Sent Events.

    Args:
        user_message: The user's input message (currently not used in simulation)

    Yields:
        bytes: UTF-8 encoded text chunks with spaces

    Example:
        async for chunk in generate_chunks("Hello"):
            print(chunk.decode('utf-8'))  # Outputs: "This ", "is ", "a ", ...
    """

    # Simulated LLM response
    # Future: This will be replaced with actual LLM chain invocation
    response_text = (
        "This is a simulated streaming response from the LLM. "
        "Each word appears one at a time."
    )

    # Split response into words for streaming
    words = response_text.split()

    # Stream each word with realistic delay
    for word in words:
        # Yield word with trailing space as UTF-8 encoded bytes
        chunk = f"{word} ".encode("utf-8")
        yield chunk

        # Simulate realistic streaming delay between words
        # This creates the "typing" effect similar to ChatGPT
        await asyncio.sleep(settings.STREAM_DELAY)


async def generate_llm_stream(user_message: str) -> AsyncGenerator[bytes, None]:
    """
    Future: Generate streaming response from actual LLM.

    This function will be implemented when integrating with LangChain.
    It will invoke the LLM chain and stream the response back to the client.

    Args:
        user_message: The user's input message

    Yields:
        bytes: UTF-8 encoded text chunks from the LLM
    """
    # Placeholder for future LLM integration
    # When implemented, this will:
    # 1. Invoke LangChain streaming chain
    # 2. Process streaming tokens
    # 3. Yield formatted chunks back to client

    raise NotImplementedError("LLM integration coming in future phase")
