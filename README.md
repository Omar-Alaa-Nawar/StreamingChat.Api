# StreamForge Backend - Phase 5 ✅

Enterprise FastAPI backend for streaming chat application with progressive component rendering and multi-component support.

**Current Version**: 0.6.0  
**Status**: Phase 5 Complete - Multi-Component Streaming + Refactored Architecture

## 🎯 Features

- ✅ **Real-time Server-Sent Events (SSE)** streaming
- ✅ **Progressive Component Rendering** (Phase 2)
- ✅ **SimpleComponent** with empty → data update flow
- ✅ **TableA Component** with row-by-row streaming (Phase 3)
- ✅ **ChartComponent** with progressive data points (Phase 4)
- ✅ **Multi-Component Support** - Multiple tables, charts, cards (Phase 5)
- ✅ **Modular Architecture** - Refactored from 1,363-line monolith to 7 focused modules
- ✅ **Code Quality** - All SonarQube complexity issues resolved
- ✅ Component state tracking and merge logic
- ✅ Predefined table schemas (sales, users, products)
- ✅ Predefined chart types (line, bar)
- 🔄 **LLM Integration** (coming soon)

## 📚 Documentation

**🎯 Main Documentation:** See [STREAMING_SERVICE_REFACTOR.md](STREAMING_SERVICE_REFACTOR.md) for complete details on:
- Architecture overview
- Module documentation
- Migration guide
- Code quality improvements
- Testing & validation

**🚀 Quick Start:** See [QUICKSTART.md](QUICKSTART.md) for setup instructions

## Project Structure

```
backend/
├── main.py                          # FastAPI application entry point
├── routers/
│   └── chat.py                     # Chat endpoints with streaming
├── services/
│   └── streaming_service/          # 🆕 Modular streaming service
│       ├── __init__.py             # Public API exports
│       ├── core.py                 # Shared utilities
│       ├── constants.py            # Configuration
│       ├── simple_component.py     # SimpleComponent logic
│       ├── table_component.py      # TableA logic
│       ├── chart_component.py      # ChartComponent logic
│       └── patterns.py             # Pattern detection & routing
├── chains/
│   └── core/
│       └── llm_setup.py            # LLM setup placeholder
├── schemas/
│   └── component_schemas.py        # Pydantic component models
├── config/
│   └── settings.py                 # Centralized configuration
├── tests/
│   ├── test_phase3.py              # TableA tests
│   ├── test_phase4.py              # ChartComponent tests
│   ├── test_phase5.py              # Multi-component tests
│   └── quick_test.py               # Smoke tests
└── requirements.txt                # Python dependencies
```

## Architecture

### Separation of Concerns

- **Routers** (`routers/`): API endpoint definitions and request/response handling
- **Services** (`services/streaming_service/`): Modular streaming business logic
  - `patterns.py`: Pattern detection and routing
  - `simple_component.py`: Card/SimpleComponent handlers
  - `table_component.py`: TableA progressive streaming
  - `chart_component.py`: ChartComponent progressive streaming
  - `core.py`: Shared utilities and validation
  - `constants.py`: Configuration and presets
- **Chains** (`chains/`): LangChain integration placeholders (future phases)
- **Schemas** (`schemas/`): Pydantic models for type safety
- **Config** (`config/`): Centralized configuration management

### Streaming Flow

```
Client Request → Router → Pattern Detection → Component Handler → Progressive Updates → SSE Stream → Client
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
