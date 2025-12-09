#!/bin/bash

# VM Full-Stack Deployment Helper Script
# This script helps you quickly deploy to the VM without using GitHub Actions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="duotopia-472708"
REGION="asia-east1"
ZONE="asia-east1-b"
VM_NAME="duotopia-prod-vm"
VM_USER="young"
VM_IP="34.81.38.211"

ARTIFACT_REGISTRY="asia-east1-docker.pkg.dev/duotopia-472708/duotopia-repo"
BACKEND_IMAGE="duotopia-backend-vm"
FRONTEND_IMAGE="duotopia-frontend-vm"

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Duotopia VM Full-Stack Deployment Helper     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Function to show usage
usage() {
    echo "Usage: $0 [COMPONENT]"
    echo ""
    echo "COMPONENT:"
    echo "  frontend  - Deploy only frontend"
    echo "  backend   - Deploy only backend"
    echo "  both      - Deploy both frontend and backend (default)"
    echo "  status    - Show current deployment status"
    echo "  logs      - View container logs"
    echo ""
    echo "Examples:"
    echo "  $0 both       # Deploy complete stack"
    echo "  $0 frontend   # Update only frontend"
    echo "  $0 status     # Check deployment status"
    exit 1
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"

    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found. Please install it first.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Function to show status
show_status() {
    echo -e "${YELLOW}📊 Checking VM deployment status...${NC}"

    gcloud compute ssh $VM_USER@$VM_NAME --zone=$ZONE --command="
        echo '=== Container Status ==='
        docker ps -a --filter name=duotopia --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
        echo ''
        echo '=== Resource Usage ==='
        docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}'
    "

    echo ""
    echo -e "${YELLOW}🌐 Testing health endpoints...${NC}"

    if curl -sf "http://$VM_IP/health" > /dev/null; then
        echo -e "${GREEN}✅ Nginx health: OK${NC}"
    else
        echo -e "${RED}❌ Nginx health: FAILED${NC}"
    fi

    if curl -sf "http://$VM_IP/api/health" > /dev/null; then
        echo -e "${GREEN}✅ Backend health: OK${NC}"
    else
        echo -e "${RED}❌ Backend health: FAILED${NC}"
    fi

    if curl -sf "http://$VM_IP/" | grep -q "<!DOCTYPE html>"; then
        echo -e "${GREEN}✅ Frontend health: OK${NC}"
    else
        echo -e "${RED}❌ Frontend health: FAILED${NC}"
    fi
}

# Function to view logs
view_logs() {
    echo -e "${YELLOW}📜 Available logs:${NC}"
    echo "  1. Backend logs"
    echo "  2. Frontend logs"
    echo "  3. Nginx logs"
    echo "  4. All logs"
    echo ""
    read -p "Select (1-4): " choice

    case $choice in
        1)
            echo -e "${BLUE}Showing backend logs (Ctrl+C to exit)...${NC}"
            gcloud compute ssh $VM_USER@$VM_NAME --zone=$ZONE --command="docker logs -f duotopia-backend"
            ;;
        2)
            echo -e "${BLUE}Showing frontend logs (Ctrl+C to exit)...${NC}"
            gcloud compute ssh $VM_USER@$VM_NAME --zone=$ZONE --command="docker logs -f duotopia-frontend"
            ;;
        3)
            echo -e "${BLUE}Showing nginx logs (Ctrl+C to exit)...${NC}"
            gcloud compute ssh $VM_USER@$VM_NAME --zone=$ZONE --command="docker logs -f duotopia-nginx"
            ;;
        4)
            echo -e "${BLUE}Showing all recent logs...${NC}"
            gcloud compute ssh $VM_USER@$VM_NAME --zone=$ZONE --command="
                echo '=== Backend Logs ===' && docker logs --tail=20 duotopia-backend &&
                echo '' && echo '=== Frontend Logs ===' && docker logs --tail=20 duotopia-frontend &&
                echo '' && echo '=== Nginx Logs ===' && docker logs --tail=20 duotopia-nginx
            "
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            ;;
    esac
}

# Function to build and deploy
deploy() {
    COMPONENT=$1

    echo -e "${YELLOW}🚀 Starting deployment of: ${COMPONENT}${NC}"
    echo ""

    # Confirm deployment
    read -p "Deploy ${COMPONENT} to VM ($VM_IP)? (yes/no): " confirm
    if [[ $confirm != "yes" ]]; then
        echo -e "${RED}Deployment cancelled${NC}"
        exit 0
    fi

    # Configure gcloud
    echo -e "${YELLOW}🔧 Configuring gcloud...${NC}"
    gcloud config set project $PROJECT_ID
    gcloud auth configure-docker $REGION-docker.pkg.dev

    # Build and deploy based on component
    if [[ $COMPONENT == "backend" || $COMPONENT == "both" ]]; then
        echo -e "${BLUE}📦 Building backend...${NC}"
        cd backend
        IMAGE_TAG="manual-$(date +%Y%m%d-%H%M%S)"
        docker build -t $ARTIFACT_REGISTRY/$BACKEND_IMAGE:$IMAGE_TAG -t $ARTIFACT_REGISTRY/$BACKEND_IMAGE:latest .
        docker push $ARTIFACT_REGISTRY/$BACKEND_IMAGE:$IMAGE_TAG
        docker push $ARTIFACT_REGISTRY/$BACKEND_IMAGE:latest
        cd ..
        echo -e "${GREEN}✅ Backend image pushed${NC}"
    fi

    if [[ $COMPONENT == "frontend" || $COMPONENT == "both" ]]; then
        echo -e "${BLUE}📦 Building frontend...${NC}"
        cd frontend
        IMAGE_TAG="manual-$(date +%Y%m%d-%H%M%S)"
        docker build \
            --build-arg VITE_API_URL="" \
            --build-arg VITE_ENVIRONMENT=production \
            --build-arg BUILD_TIMESTAMP="$(date -u +%Y%m%d-%H%M%S)" \
            -t $ARTIFACT_REGISTRY/$FRONTEND_IMAGE:$IMAGE_TAG \
            -t $ARTIFACT_REGISTRY/$FRONTEND_IMAGE:latest .
        docker push $ARTIFACT_REGISTRY/$FRONTEND_IMAGE:$IMAGE_TAG
        docker push $ARTIFACT_REGISTRY/$FRONTEND_IMAGE:latest
        cd ..
        echo -e "${GREEN}✅ Frontend image pushed${NC}"
    fi

    # Deploy to VM
    echo -e "${BLUE}🚀 Deploying to VM...${NC}"

    # Upload nginx config if deploying both
    if [[ $COMPONENT == "both" ]]; then
        gcloud compute scp deployment/vm/nginx.conf $VM_USER@$VM_NAME:/tmp/nginx.conf --zone=$ZONE
    fi

    # Deploy containers
    gcloud compute ssh $VM_USER@$VM_NAME --zone=$ZONE --command="
        set -e

        echo '🔐 Configuring Docker...'
        docker-credential-gcr configure-docker --registries=$REGION-docker.pkg.dev

        if [[ '$COMPONENT' == 'backend' || '$COMPONENT' == 'both' ]]; then
            echo '📥 Pulling backend image...'
            docker pull $ARTIFACT_REGISTRY/$BACKEND_IMAGE:latest

            echo '🛑 Stopping old backend...'
            docker stop duotopia-backend 2>/dev/null || true
            docker rm duotopia-backend 2>/dev/null || true

            echo '🚀 Starting backend...'
            docker run -d \
                --name duotopia-backend \
                --restart unless-stopped \
                --network=host \
                --env-file /tmp/backend.env \
                $ARTIFACT_REGISTRY/$BACKEND_IMAGE:latest
        fi

        if [[ '$COMPONENT' == 'frontend' || '$COMPONENT' == 'both' ]]; then
            echo '📥 Pulling frontend image...'
            docker pull $ARTIFACT_REGISTRY/$FRONTEND_IMAGE:latest

            echo '🛑 Stopping old frontend...'
            docker stop duotopia-frontend 2>/dev/null || true
            docker rm duotopia-frontend 2>/dev/null || true

            echo '🚀 Starting frontend...'
            docker run -d \
                --name duotopia-frontend \
                --restart unless-stopped \
                --network=host \
                -e BACKEND_URL=http://localhost:8080 \
                $ARTIFACT_REGISTRY/$FRONTEND_IMAGE:latest
        fi

        if [[ '$COMPONENT' == 'both' ]]; then
            echo '🛑 Restarting nginx...'
            docker stop duotopia-nginx 2>/dev/null || true
            docker rm duotopia-nginx 2>/dev/null || true

            echo '🚀 Starting nginx...'
            docker run -d \
                --name duotopia-nginx \
                --restart unless-stopped \
                --network=host \
                -v /tmp/nginx.conf:/etc/nginx/nginx.conf:ro \
                nginx:alpine
        fi

        echo '🧹 Cleaning up...'
        docker image prune -f

        echo '✅ Deployment complete'
    "

    # Health check
    echo -e "${YELLOW}🩺 Running health check...${NC}"
    sleep 10

    if curl -sf "http://$VM_IP/api/health" > /dev/null; then
        echo -e "${GREEN}✅ Backend is healthy${NC}"
    else
        echo -e "${RED}❌ Backend health check failed${NC}"
    fi

    if curl -sf "http://$VM_IP/" | grep -q "<!DOCTYPE html>"; then
        echo -e "${GREEN}✅ Frontend is healthy${NC}"
    else
        echo -e "${RED}❌ Frontend health check failed${NC}"
    fi

    echo ""
    echo -e "${GREEN}🎉 Deployment completed!${NC}"
    echo -e "${BLUE}🔗 Access URLs:${NC}"
    echo -e "  Frontend: http://$VM_IP/"
    echo -e "  Backend API: http://$VM_IP/api/docs"
    echo -e "  Backend Health: http://$VM_IP/api/health"
}

# Main script logic
check_prerequisites

COMPONENT=${1:-both}

case $COMPONENT in
    frontend|backend|both)
        deploy $COMPONENT
        ;;
    status)
        show_status
        ;;
    logs)
        view_logs
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo -e "${RED}❌ Invalid component: $COMPONENT${NC}"
        echo ""
        usage
        ;;
esac
