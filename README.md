# StreamForge Backend - Phase 0

Enterprise FastAPI backend for streaming chat application with real-time Server-Sent Events (SSE).

## Project Structure

```
backend/
├── main.py                    # FastAPI application entry point
├── routers/
│   └── chat.py               # Chat endpoints with streaming
├── services/
│   ├── streaming_service.py  # Core streaming logic
│   └── chain_service.py      # Chain creation (future LLM integration)
├── chains/
│   └── core/
│       └── llm_setup.py      # LLM setup placeholder
├── config/
│   └── settings.py           # Centralized configuration
└── requirements.txt          # Python dependencies
```

## Architecture

### Separation of Concerns

- **Routers** (`routers/`): API endpoint definitions and request/response handling
- **Services** (`services/`): Business logic and core functionality
- **Chains** (`chains/`): LangChain integration placeholders (future phases)
- **Config** (`config/`): Centralized configuration management

### Streaming Flow

```
Client Request → Router → Service → Async Generator → SSE Stream → Client
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Method 1: Using Python directly (Recommended)
```bash
cd C:\Users\omar.nawar\streamforge\backend
python main.py
```

### Method 2: Using uvicorn command
```bash
cd C:\Users\omar.nawar\streamforge\backend
uvicorn main:app --reload
```

### Method 3: Using the batch file (Windows)
```bash
cd C:\Users\omar.nawar\streamforge\backend
start.bat
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Root Endpoint
- **GET** `/` - API information and available endpoints
- **GET** `/health` - Global health check

### Chat Endpoints
- **POST** `/chat` - Stream chat response using SSE
  - Body: `{"message": "your message here"}`
  - Response: Server-Sent Events stream
- **GET** `/chat/health` - Chat service health check

### Documentation
- **GET** `/docs` - Interactive API documentation (Swagger UI)
- **GET** `/openapi.json` - OpenAPI schema

## Testing the Streaming Endpoint

### Using curl
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

### Expected Response
```
data: This
data: is
data: a
data: simulated
data: streaming
data: response
...
```

### Using Python
```python
import requests

response = requests.post(
    "http://localhost:8000/chat",
    json={"message": "Hello"},
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

## Configuration

Configuration is centralized in `config/settings.py`:

- **CORS**: Allows all origins for development
- **Streaming Delay**: 0.1 seconds between words
- **Server**: Default host `0.0.0.0`, port `8000`

## Phase 0 Features

- FastAPI application with CORS middleware
- POST `/chat` endpoint with streaming response
- Server-Sent Events (SSE) format
- Word-by-word streaming simulation
- Async/await throughout
- Enterprise architecture ready for LLM integration

## Future Phases

### Phase 1: LLM Integration
- Integrate LangChain
- Connect to OpenAI/Anthropic APIs
- Real LLM streaming responses

### Phase 2: RAG (Retrieval-Augmented Generation)
- Vector store integration
- Document embedding and retrieval
- Knowledge-augmented responses

### Phase 3: Advanced Features
- Conversation memory
- Multiple LLM providers
- Custom prompts and templates
- Session management

## Development Notes

- All services use async/await for optimal performance
- Streaming uses Python async generators
- SSE headers configured for real-time streaming:
  - `Cache-Control: no-cache`
  - `Connection: keep-alive`
  - `X-Accel-Buffering: no`

## Tech Stack

- **FastAPI**: Modern, fast web framework
- **Uvicorn**: Lightning-fast ASGI server
- **Python asyncio**: Async streaming support
- **Pydantic**: Data validation and settings

## Contributing

This is Phase 0 - the foundation. Future phases will build upon this architecture to add real LLM capabilities, RAG, and advanced features.
