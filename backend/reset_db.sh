#!/bin/bash

echo "🔄 Resetting database..."

# Drop all tables
echo "🗑️  Dropping all tables..."
./venv/bin/python -c "
from database import engine
from models import Base
Base.metadata.drop_all(bind=engine)
print('✅ All tables dropped')
"

# Run migrations
echo "🏗️  Running migrations..."
./venv/bin/alembic upgrade head

# Seed database
echo "🌱 Seeding database..."
./venv/bin/python seed.py

echo "✨ Database reset complete!"