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

# 資料庫管理 - Staging 環境
.PHONY: db-staging-create
db-staging-create:
	@echo "Creating STAGING Cloud SQL instance with cost-optimized settings..."
	gcloud sql instances create duotopia-staging-0827 \
		--database-version=POSTGRES_17 \
		--tier=db-f1-micro \
		--region=$(REGION) \
		--edition=ENTERPRISE \
		--storage-size=10GB \
		--storage-type=SSD \
		--availability-type=ZONAL \
		--no-backup \
		--project=$(PROJECT_ID)
	@echo "✅ STAGING Database created with cost optimization:"
	@echo "   - Instance: duotopia-staging-0827"
	@echo "   - Tier: db-f1-micro (~$$11/month)"
	@echo "   - No backup (saves $$2/month)"
	@echo ""
	@echo "⚠️  IMPORTANT: Run 'make db-staging-stop' NOW to save money!"
	@echo "   The instance is RUNNING and charging you!"

.PHONY: db-staging-env
db-staging-env:
	@echo "🔧 Updating staging Cloud Run environment variables..."
	@echo "⚠️  請確保已在 .env.staging 設定正確的 DATABASE_URL"
	@if [ ! -f backend/.env.staging ]; then \
		echo "❌ 錯誤：找不到 backend/.env.staging 檔案"; \
		echo "請建立該檔案並設定 DATABASE_URL"; \
		exit 1; \
	fi
	@source backend/.env.staging && \
	gcloud run services update $(BACKEND_SERVICE) \
		--set-env-vars="DATABASE_URL=$$DATABASE_URL,JWT_SECRET=$$JWT_SECRET,JWT_ALGORITHM=$$JWT_ALGORITHM,JWT_EXPIRE_MINUTES=$$JWT_EXPIRE_MINUTES" \
		--region=$(REGION) \
		--project=$(PROJECT_ID)
	@echo "✅ Staging environment variables updated from .env.staging"

.PHONY: db-staging-start
db-staging-start:
	@echo "Starting STAGING Cloud SQL..."
	gcloud sql instances patch duotopia-staging-0827 --activation-policy=ALWAYS --project=$(PROJECT_ID)

.PHONY: db-staging-stop
db-staging-stop:
	@echo "Stopping STAGING Cloud SQL to save money..."
	gcloud sql instances patch duotopia-staging-0827 --activation-policy=NEVER --project=$(PROJECT_ID)
	@echo "✅ Instance stopped - not charging you anymore!"

.PHONY: db-staging-delete
db-staging-delete:
	@echo "⚠️  WARNING: Deleting STAGING Cloud SQL instance..."
	@echo "Instance: duotopia-staging-0827"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	gcloud sql instances delete duotopia-staging-0827 --quiet --project=$(PROJECT_ID)

# 資料庫 Seed
.PHONY: db-seed-local
db-seed-local:
	@echo "🌱 Seeding local database with demo data..."
	cd $(BACKEND_DIR) && python seed_data.py
	@echo "✅ Local database seeded!"

.PHONY: db-seed-staging
db-seed-staging:
	@echo "🌱 Seeding STAGING database with demo data..."
	@echo "⚠️  Ensuring staging database is running..."
	@make db-staging-start
	@echo "Waiting for database to be ready..."
	@sleep 5
	@echo "Running seed script..."
	cd $(BACKEND_DIR) && DATABASE_URL="postgresql://postgres:postgres@34.80.209.41/postgres" python seed_data.py
	@echo "✅ Staging database seeded!"
	@echo "⚠️  Remember to stop the database: make db-staging-stop"

# 狀態檢查
.PHONY: status
status:
	@echo "Checking service status..."
	gcloud run services list --platform managed --region $(REGION)
	@echo "Checking database status..."
	gcloud sql instances describe duotopia-staging-0827 --format="value(state,settings.activationPolicy)" 2>/dev/null || echo "No database"

# 幫助
.PHONY: help
help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  dev-setup      - Set up development environment"
	@echo "  dev-backend    - Start backend dev server"
	@echo "  dev-frontend   - Start frontend dev server"
	@echo ""
	@echo "Testing:"
	@echo "  test           - Run all tests"
	@echo "  test-local     - Test with local Docker containers"
	@echo ""
	@echo "Database - Staging:"
	@echo "  db-staging-create - Create staging database (duotopia-staging-0827)"
	@echo "  db-staging-start  - Start staging database"
	@echo "  db-staging-stop   - Stop staging database (save money)"
	@echo "  db-staging-delete - Delete staging database"
	@echo "  db-staging-env    - Update Cloud Run env vars (DB connection)"
	@echo ""
	@echo "Database - Seed Data:"
	@echo "  db-seed-local     - Seed local database with demo data"
	@echo "  db-seed-staging   - Seed staging database with demo data"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy-staging - Deploy to staging environment"
	@echo "  build          - Build Docker images"
	@echo ""
	@echo "Monitoring:"
	@echo "  logs-backend   - View backend logs"
	@echo "  logs-frontend  - View frontend logs"
	@echo "  status         - Check all services status"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean          - Clean up development environment"