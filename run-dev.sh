#!/bin/bash

# Start servers for local development

echo "Starting Duotopia development servers..."

# Check if Docker containers are running
if ! docker ps | grep -q duotopia-db; then
    echo "Starting Docker containers..."
    docker-compose up -d
    echo "Waiting for database to be ready..."
    sleep 5
fi

# Function to cleanup on exit
cleanup() {
    echo -e "\n\nShutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup EXIT INT TERM

# Start backend server
echo -e "\n🚀 Starting backend server on http://localhost:8000"
cd backend
./venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a bit for backend to start
sleep 3

# Start frontend server
echo -e "\n🚀 Starting frontend server on http://localhost:5173"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo -e "\n✅ Development servers are running!"
echo -e "\n📚 Backend API: http://localhost:8000"
echo -e "📚 Backend API Docs: http://localhost:8000/docs"
echo -e "🎨 Frontend: http://localhost:5173"
echo -e "\nPress Ctrl+C to stop all servers\n"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID