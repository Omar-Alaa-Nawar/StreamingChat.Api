"""
Chat router for handling streaming chat endpoints.

This module defines the API endpoints for chat functionality,
including streaming responses using Server-Sent Events (SSE).
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.streaming_service import generate_chunks


# Create router for chat endpoints
router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)


class ChatRequest(BaseModel):
    """
    Request model for chat endpoint.

    Attributes:
        message: The user's message/query to send to the LLM
    """
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hello, how are you?"
            }
        }


class ChatResponse(BaseModel):
    """
    Response model for non-streaming chat responses.

    Future: This will be used for non-streaming endpoints.
    """
    response: str
    metadata: dict = {}


@router.post("")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response using Server-Sent Events (SSE).

    This endpoint accepts a user message and returns a streaming response
    where each word is sent as a separate chunk, simulating real-time
    LLM response generation similar to ChatGPT.

    Args:
        request: ChatRequest containing the user's message

    Returns:
        StreamingResponse: SSE stream of response chunks

    Example:
        POST /chat
        Body: {"message": "Tell me a story"}

        Response (streamed):
        data: This
        data: is
        data: a
        data: simulated
        ...
    """
    return StreamingResponse(
        generate_chunks(request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/health")
async def chat_health():
    """
    Health check endpoint for chat service.

    Returns:
        dict: Service status information
    """
    return {
        "service": "chat",
        "status": "healthy",
        "streaming": "enabled"
    }
