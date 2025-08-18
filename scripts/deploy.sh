#!/bin/bash

# Deploy script for Duotopia

set -e

echo "🚀 Deploying Duotopia to GCP..."

# Check if logged in to gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Please login to gcloud first: gcloud auth login"
    exit 1
fi

PROJECT_ID="duotopia-469413"
REGION="asia-east1"

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📡 Enabling required APIs..."
gcloud services enable \
    cloudrun.googleapis.com \
    cloudbuild.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    compute.googleapis.com \
    servicenetworking.googleapis.com

# Create Artifact Registry repository if it doesn't exist
echo "🏗️ Setting up Artifact Registry..."
gcloud artifacts repositories create duotopia \
    --repository-format=docker \
    --location=$REGION \
    --description="Duotopia Docker images" || true

# Build and push images
echo "🔨 Building Docker images..."
gcloud builds submit --config=cloudbuild.yaml

# Deploy with Terraform
echo "🏗️ Deploying infrastructure with Terraform..."
cd terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply deployment (will prompt for confirmation)
terraform apply

cd ..

echo "✅ Deployment complete!"
echo ""
echo "Your application URLs:"
terraform -chdir=terraform output -json | jq -r '.frontend_url.value'
terraform -chdir=terraform output -json | jq -r '.backend_url.value'