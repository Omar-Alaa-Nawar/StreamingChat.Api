# StreamForge Backend - Quick Start Guide

## Terminal Commands to Run the Project

### Step 1: Navigate to Backend Directory
```bash
cd C:\Users\omar.nawar\streamforge\backend
```

### Step 2: Install Dependencies (First Time Only)
```bash
pip install -r requirements.txt
```

### Step 3: Run the Server

#### Option A: Using Python (Simplest)
```bash
python main.py
```

#### Option B: Using Batch File (Windows)
```bash
start.bat
```

#### Option C: Using Uvicorn Directly
```bash
uvicorn main:app --reload
```

### Step 4: Access the Application

Open your browser and go to:
- **API**: http://localhost:8001
- **Swagger UI**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

---

## One-Line Command (After First Install)

```bash
cd C:\Users\omar.nawar\streamforge\backend && python main.py
```

---

## Testing the Streaming Endpoint

### Using Browser (Easiest)
1. Go to http://localhost:8001/docs
2. Click on **POST /chat**
3. Click **"Try it out"**
4. Enter: `{"message": "Hello!"}`
5. Click **"Execute"**
6. Watch the streaming response!

### Using curl (Terminal)
```bash
curl -X POST http://localhost:8001/chat -H "Content-Type: application/json" -d "{\"message\": \"Hello!\"}"
```

### Using PowerShell
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/chat" -Method Post -ContentType "application/json" -Body '{"message": "Hello!"}'
```

---

## Stopping the Server

Press `CTRL + C` in the terminal where the server is running.

---

## Troubleshooting

### Port Already in Use?
Change the port in `config/settings.py`:
```python
PORT: int = 8001  # Change to any available port
```

### Module Not Found?
Make sure you're in the backend directory:
```bash
cd C:\Users\omar.nawar\streamforge\backend
```

### Dependencies Missing?
Reinstall dependencies:
```bash
pip install -r requirements.txt
```

---

## What's Running?

When you run the server, you get:
- ✅ FastAPI application with auto-reload
- ✅ Streaming chat endpoint (SSE)
- ✅ Interactive API documentation
- ✅ CORS enabled for frontend
- ✅ Health check endpoints

Server logs will show:
```
INFO:     Uvicorn running on http://127.0.0.1:8001
INFO:     Application startup complete.
```

---

## Next Steps

1. ✅ Run the server
2. ✅ Test in Swagger UI (http://localhost:8001/docs)
3. ⏭️ Connect your React frontend
4. ⏭️ Integrate real LLM (Phase 1)
