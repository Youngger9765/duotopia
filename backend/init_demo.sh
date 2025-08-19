#!/bin/bash

# Duotopia Demo Database Initialization Script
# This script initializes the database with demo data for development and testing

set -e  # Exit on any error

echo "🚀 Duotopia Demo Database Initialization"
echo "========================================"

# Check if we're in the backend directory
if [ ! -f "seed_demo.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not detected. Attempting to activate..."
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Virtual environment not found. Please create and activate it first:"
        echo "   python -m venv venv"
        echo "   source venv/bin/activate"
        echo "   pip install -r requirements.txt"
        exit 1
    fi
fi

# Check if database file exists
if [ ! -f "duotopia.db" ]; then
    echo "📊 Database file not found. Creating database..."
    python -c "
from database import engine, Base
from models import *
print('Creating database tables...')
Base.metadata.create_all(bind=engine)
print('✅ Database tables created')
"
else
    echo "📊 Database file found"
fi

# Run migrations if alembic is available
if command -v alembic &> /dev/null; then
    echo "🔄 Running database migrations..."
    alembic upgrade head
    echo "✅ Migrations completed"
else
    echo "⚠️  Alembic not available, skipping migrations"
fi

# Ask user for confirmation to clear data
read -p "🗑️  Do you want to clear existing data before seeding? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    CLEAR_FLAG="--clear"
    echo "🗑️  Will clear existing data"
else
    CLEAR_FLAG=""
    echo "📝 Will preserve existing data"
fi

# Run the seeder
echo "🌱 Running demo data seeder..."
python seed_demo.py $CLEAR_FLAG

# Check if backend server is running
if pgrep -f "uvicorn.*main:app" > /dev/null; then
    echo "⚠️  Backend server is running. You may want to restart it to see changes."
    read -p "🔄 Do you want to restart the backend server? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🛑 Stopping backend server..."
        pkill -f "uvicorn.*main:app" || true
        sleep 2
        echo "🚀 Starting backend server..."
        python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
        echo "✅ Backend server restarted"
        echo "📋 Backend logs: tail -f backend.log"
    fi
else
    echo "ℹ️  Backend server is not running."
    read -p "🚀 Do you want to start the backend server? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 Starting backend server..."
        python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
        echo "✅ Backend server started"
        echo "📋 Backend logs: tail -f backend.log"
        echo "🌐 API available at: http://localhost:8000"
        echo "📚 API docs at: http://localhost:8000/docs"
    fi
fi

echo ""
echo "🎉 Demo initialization completed!"
echo "======================================"
echo "🔗 Quick Links:"
echo "   Frontend: http://localhost:5174"  
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "🔑 Demo Login Credentials:"
echo "   Admin:   admin@duotopia.com / admin123"
echo "   Teacher: teacher1@duotopia.com / teacher123"
echo "   Student: student1@duotopia.com / 20090828"
echo "======================================"