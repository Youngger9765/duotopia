# Duotopia Development Makefile

# 變數設定
BACKEND_DIR = backend
FRONTEND_DIR = frontend
PROJECT_ID = duotopia-469413
REGION = asia-east1

# 開發環境
.PHONY: dev-setup
dev-setup:
	@echo "Setting up development environment..."
	docker-compose up -d
	cd $(FRONTEND_DIR) && npm install
	cd $(BACKEND_DIR) && pip install -r requirements.txt

.PHONY: dev-backend
dev-backend:
	@echo "Starting backend development server..."
	cd $(BACKEND_DIR) && uvicorn main:app --reload --port 8000

.PHONY: dev-frontend  
dev-frontend:
	@echo "Starting frontend development server..."
	cd $(FRONTEND_DIR) && npm run dev

# 測試
.PHONY: test
test:
	@echo "Running all tests..."
	cd $(BACKEND_DIR) && python -m pytest tests/ -v

.PHONY: test-backend
test-backend:
	@echo "Running backend unit tests..."
	cd $(BACKEND_DIR) && python -m pytest tests/ -v

.PHONY: test-cov
test-cov:
	@echo "Running tests with coverage..."
	cd $(BACKEND_DIR) && python -m pytest tests/ --cov=routers --cov=models --cov-report=term-missing

.PHONY: test-auth
test-auth:
	@echo "Running auth tests..."
	cd $(BACKEND_DIR) && python -m pytest tests/test_auth.py -v

.PHONY: test-frontend
test-frontend:
	@echo "Running frontend tests..."
	cd $(FRONTEND_DIR) && npm run typecheck
	cd $(FRONTEND_DIR) && npm run lint

.PHONY: build
build:
	@echo "Building applications..."
	cd $(FRONTEND_DIR) && npm run build
	cd $(BACKEND_DIR) && docker build -t duotopia-backend .
	cd $(FRONTEND_DIR) && docker build -t duotopia-frontend .

# 本地測試
.PHONY: test-local
test-local:
	@echo "Testing locally with Docker..."
	docker run -d -p 8080:8080 --name duotopia-backend-test duotopia-backend
	docker run -d -p 3000:80 --name duotopia-frontend-test duotopia-frontend
	sleep 5
	curl -f http://localhost:8080/health || (echo "Backend test failed" && exit 1)
	curl -f http://localhost:3000 || (echo "Frontend test failed" && exit 1)
	docker stop duotopia-backend-test duotopia-frontend-test
	docker rm duotopia-backend-test duotopia-frontend-test
	@echo "Local tests passed!"

# 部署
.PHONY: deploy-staging
deploy-staging:
	@echo "Deploying to staging..."
	git push origin staging

# 清理
.PHONY: clean
clean:
	@echo "Cleaning up..."
	docker-compose down -v
	cd $(FRONTEND_DIR) && rm -rf node_modules dist
	cd $(BACKEND_DIR) && find . -name "__pycache__" -exec rm -rf {} +

# 日誌查看
.PHONY: logs-backend
logs-backend:
	gcloud run logs read duotopia-backend --limit=50

.PHONY: logs-frontend
logs-frontend:
	gcloud run logs read duotopia-frontend --limit=50

# 資料庫管理
.PHONY: db-create
db-create:
	@echo "Creating Cloud SQL instance with cost-optimized settings..."
	gcloud sql instances create duotopia-dev \
		--tier=db-f1-micro \
		--region=$(REGION) \
		--database-version=POSTGRES_17 \
		--storage-size=10GB \
		--storage-type=SSD \
		--no-backup \
		--no-assign-ip \
		--network=projects/$(PROJECT_ID)/global/networks/default \
		--availability-type=ZONAL \
		--activation-policy=NEVER \
		--maintenance-release-channel=production \
		--maintenance-window-day=SUN \
		--maintenance-window-hour=03 \
		--deletion-protection=false \
		--project=$(PROJECT_ID)
	@echo "✅ Database created with cost optimization:"
	@echo "   - No public IP (saves $$9.49/month)"
	@echo "   - No backup (saves $$2/month)" 
	@echo "   - SSD storage (better performance)"
	@echo "   - Default: STOPPED ($$0 until you start it)"
	@echo "   - Total when running: ~$$11/month"
	@echo ""
	@echo "⚠️  Remember to run 'make db-start' to begin using it"

.PHONY: db-start
db-start:
	@echo "Starting Cloud SQL..."
	gcloud sql instances patch duotopia-dev --activation-policy=ALWAYS --project=$(PROJECT_ID)

.PHONY: db-stop
db-stop:
	@echo "Stopping Cloud SQL..."
	gcloud sql instances patch duotopia-dev --activation-policy=NEVER --project=$(PROJECT_ID)

.PHONY: db-delete
db-delete:
	@echo "Deleting Cloud SQL instance..."
	gcloud sql instances delete duotopia-dev --quiet --project=$(PROJECT_ID)

# 狀態檢查
.PHONY: status
status:
	@echo "Checking service status..."
	gcloud run services list --platform managed --region $(REGION)
	@echo "Checking database status..."
	gcloud sql instances describe duotopia-dev --format="value(state,settings.activationPolicy)" 2>/dev/null || echo "No database"

# 幫助
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  dev-setup     - Set up development environment"
	@echo "  dev-backend   - Start backend dev server"
	@echo "  dev-frontend  - Start frontend dev server"
	@echo "  test          - Run all tests"
	@echo "  build         - Build Docker images"
	@echo "  test-local    - Test with local Docker containers"
	@echo "  deploy-staging - Deploy to staging environment"
	@echo "  logs-backend  - View backend logs"
	@echo "  logs-frontend - View frontend logs"
	@echo "  status        - Check service status"
	@echo "  clean         - Clean up development environment"