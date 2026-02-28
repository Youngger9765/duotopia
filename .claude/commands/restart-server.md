# Restart Server

Kill and restart the backend server.

## Usage

```bash
/restart-server
```

## What it does

1. Kills all running Python backend processes (Windows-compatible)
2. Waits 1 second for cleanup
3. Starts a fresh backend server in background
4. Waits 3 seconds for server to initialize
5. Tests the server health endpoint

## Implementation

```bash
# Kill all Python processes (Windows-compatible: must use cmd.exe because bash interprets /F as path)
cmd.exe //c "taskkill /F /IM python.exe" 2>/dev/null || true

# Wait for cleanup
sleep 1

# Start backend in background
cd backend && nohup python -m uvicorn main:app --reload --port 8080 > /dev/null 2>&1 &

# Wait for server to start
sleep 3

# Test health endpoint
curl -s -o /dev/null -w "Backend status: HTTP %{http_code}\n" http://localhost:8080/docs || echo "❌ Backend failed to start"
```
