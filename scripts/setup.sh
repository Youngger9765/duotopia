#!/bin/bash

# Setup script for Duotopia project

echo "🚀 Setting up Duotopia project..."

# Check prerequisites
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed."; exit 1; }
command -v terraform >/dev/null 2>&1 || { echo "❌ Terraform is required but not installed."; exit 1; }
command -v gcloud >/dev/null 2>&1 || { echo "❌ Google Cloud SDK is required but not installed."; exit 1; }

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Setup Python virtual environment
echo "🐍 Setting up Python environment..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Copy environment files
echo "📋 Setting up environment files..."
cp .env.example .env
cp backend/.env.example backend/.env
cp terraform/terraform.tfvars.example terraform/terraform.tfvars

# Start local services
echo "🐳 Starting local services..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database..."
sleep 10

# Run database migrations
echo "🗄️ Running database migrations..."
cd backend
source venv/bin/activate
alembic upgrade head
cd ..

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env files with your configuration"
echo "2. Update terraform/terraform.tfvars with your GCP configuration"
echo "3. Run 'make dev' to start development servers"
echo ""
echo "For production deployment:"
echo "1. Set up GitHub secrets for CI/CD"
echo "2. Initialize Terraform state: cd terraform && terraform init"
echo "3. Deploy infrastructure: terraform apply"