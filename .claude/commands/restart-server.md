# Restart Server

Kill and restart the backend server.

## Usage

```bash
/restart-server
```

## What it does

1. Kills all running Python backend processes
2. Waits 1 second for cleanup
3. Starts a fresh backend server in background
4. Waits 3 seconds for server to initialize
5. Tests the server health endpoint

## Implementation

```bash
# Kill all backend processes
pkill -9 -f "uvicorn.*main:app" || pkill -9 -f "python.*main.py"

# Wait for cleanup
sleep 1

# Start backend in background
cd backend && python main.py > /tmp/backend.log 2>&1 &

# Wait for server to start
sleep 3

# Test health endpoint
curl -s http://localhost:8080/health || echo "❌ Backend failed to start - check /tmp/backend.log"
```
