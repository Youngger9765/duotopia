# Duotopia Development Makefile

# 變數設定
BACKEND_DIR = backend
FRONTEND_DIR = frontend
PROJECT_ID = duotopia-469413
REGION = asia-east1

# 資料庫 Migration 指令
.PHONY: db-check
db-check:
	@echo "🔍 Checking for uncommitted model changes..."
	@cd $(BACKEND_DIR) && alembic check || (echo "❌ Model changes detected! Run: make db-migrate MSG='your message'" && exit 1)

.PHONY: db-migrate
db-migrate:
	@if [ -z "$(MSG)" ]; then \
		echo "❌ Error: Please provide a migration message"; \
		echo "Usage: make db-migrate MSG='add new field'"; \
		exit 1; \
	fi
	@echo "🔄 Generating migration: $(MSG)"
	@cd $(BACKEND_DIR) && alembic revision --autogenerate -m "$(MSG)"
	@echo "✅ Migration generated. Please review the file and run: make db-upgrade"

.PHONY: db-upgrade
db-upgrade:
	@echo "⬆️ Upgrading LOCAL database to latest migration..."
	@cd $(BACKEND_DIR) && alembic upgrade head
	@echo "✅ Database upgraded successfully"

.PHONY: db-upgrade-staging
db-upgrade-staging:
	@echo "⬆️ Upgrading STAGING database to latest migration..."
	@if [ ! -f backend/.env.staging ]; then \
		echo "❌ Error: backend/.env.staging not found"; \
		exit 1; \
	fi
	@cd $(BACKEND_DIR) && \
		source .env.staging && \
		DATABASE_URL="$$DATABASE_URL" alembic upgrade head
	@echo "✅ Staging database upgraded successfully"

.PHONY: db-history
db-history:
	@echo "📜 Migration history:"
	@cd $(BACKEND_DIR) && alembic history

.PHONY: db-current
db-current:
	@echo "📍 Current LOCAL database version:"
	@cd $(BACKEND_DIR) && alembic current

.PHONY: db-current-staging
db-current-staging:
	@echo "📍 Current STAGING database version:"
	@cd $(BACKEND_DIR) && \
		source .env.staging && \
		DATABASE_URL="$$DATABASE_URL" alembic current

.PHONY: db-fix-migration
db-fix-migration:
	@echo "🔧 Auto-fixing migration revision issues..."
	@cd $(BACKEND_DIR) && python fix_migration.py

# 開發環境
.PHONY: dev-setup
dev-setup:
	@echo "Setting up development environment..."
	docker-compose up -d
	cd $(FRONTEND_DIR) && npm install
	cd $(BACKEND_DIR) && pip install -r requirements.txt
	@echo "Installing pre-commit hooks..."
	pip install pre-commit
	pre-commit install
	@echo "✅ Development environment ready!"

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

# 部署 - 支援多資料庫選擇
.PHONY: deploy-staging-supabase
deploy-staging-supabase:
	@echo "🚀 Deploying to Staging with Supabase (Free)..."
	@echo "This will use Supabase free tier database"
	@gh workflow run deploy-staging.yml -f database=supabase

.PHONY: deploy-staging-cloudsql
deploy-staging-cloudsql:
	@echo "🚀 Deploying to Staging with Cloud SQL..."
	@echo "💰 Warning: This will cost $$2.28/day!"
	@read -p "Continue? (y/n) " -n 1 -r; echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		gh workflow run deploy-staging.yml -f database=cloudsql; \
	else \
		echo "Deployment cancelled."; \
	fi

.PHONY: deploy-staging
deploy-staging: deploy-staging-supabase
	@echo "Default staging deployment uses Supabase (free)"

# 快速切換資料庫（不重新部署）
.PHONY: switch-staging-supabase
switch-staging-supabase:
	@echo "Switching staging to Supabase (free tier)..."
	gcloud run services update duotopia-staging-backend \
		--region=$(REGION) \
		--update-env-vars DATABASE_TYPE=supabase \
		--update-env-vars DATABASE_URL="$${STAGING_SUPABASE_URL}"
	@echo "✅ Switched to Supabase (Cost: $$0/day)"

.PHONY: switch-staging-cloudsql
switch-staging-cloudsql:
	@echo "Switching staging to Cloud SQL..."
	@echo "💰 This will cost $$2.28/day"
	@read -p "Continue? (y/n) " -n 1 -r; echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		./scripts/manage-db.sh start; \
		gcloud run services update duotopia-staging-backend \
			--region=$(REGION) \
			--update-env-vars DATABASE_TYPE=cloudsql \
			--update-env-vars DATABASE_URL="$${STAGING_CLOUDSQL_URL}"; \
		echo "✅ Switched to Cloud SQL (Cost: $$2.28/day)"; \
	fi

# 檢查當前資料庫狀態
.PHONY: check-database
check-database:
	@echo "Checking current database configuration..."
	@gcloud run services describe duotopia-staging-backend \
		--region=$(REGION) \
		--format="value(spec.template.spec.containers[0].env[?key=='DATABASE_TYPE'].value)" 2>/dev/null || echo "Not set"
	@echo ""
	@echo "Cloud SQL Status:"
	@gcloud sql instances describe duotopia-staging-0827 \
		--format="value(state,settings.activationPolicy)" 2>/dev/null || echo "Not found"

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
	@echo "   - No high availability (saves $$5/month)"
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
	@echo "🌱 Seeding STAGING database with demo data (Supabase)..."
	@echo "Running seed script with Supabase..."
	@if [ -z "$$DATABASE_URL" ]; then \
		echo "❌ Error: DATABASE_URL environment variable not set"; \
		echo "Please set DATABASE_URL before running this command"; \
		exit 1; \
	fi
	cd $(BACKEND_DIR) && python seed_data.py
	@echo "✅ Staging database seeded!"

.PHONY: db-seed-staging-pooler
db-seed-staging-pooler:
	@echo "🌱 Seeding STAGING database using Supabase Pooler URL (備用方案)..."
	@echo "⚠️  Using pooler connection for better reliability"
	@if [ ! -f backend/.env.staging ]; then \
		echo "❌ Error: backend/.env.staging not found"; \
		exit 1; \
	fi
	@cd $(BACKEND_DIR) && \
		DATABASE_URL="postgresql://postgres.oenkjognodqhvujaooax:Duotopia2025@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres" \
		python seed_data.py
	@echo "✅ Staging database seeded via pooler!"
	@echo "💡 Tip: If direct connection fails, use this pooler method"

# 狀態檢查
.PHONY: status
status:
	@echo "Checking service status..."
	gcloud run services list --platform managed --region $(REGION)
	@echo "Checking database status..."
	gcloud sql instances describe duotopia-staging-0827 --format="value(state,settings.activationPolicy)" 2>/dev/null || echo "No database"

# 資料庫成本檢查
.PHONY: db-staging-cost-check
db-staging-cost-check:
	@echo "🔍 檢查 Staging 資料庫成本設定..."
	@echo ""
	@gcloud sql instances describe duotopia-staging-0827 \
		--format="table(name,settings.availabilityType,settings.tier,settings.backupConfiguration.enabled,state)" \
		--project=$(PROJECT_ID) || echo "No database found"
	@echo ""
	@echo "✅ 成本優化檢查："
	@echo "   - ZONAL = 單區域（省錢）"
	@echo "   - db-f1-micro = 最小機器（約 $$11/月）"
	@echo "   - Backup False = 無備份（省 $$2/月）"
	@echo "   - STOPPED = 已停機（不收費）"
	@echo ""
	@echo "⚠️  高可用性（High Availability）狀態：未啟用"
	@echo "   如果 Console 顯示可啟用，那是因為資料庫已停機"

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
	@echo "Database Migration:"
	@echo "  db-migrate MSG='msg' - Generate new migration"
	@echo "  db-upgrade     - Upgrade LOCAL database to latest"
	@echo "  db-upgrade-staging - Upgrade STAGING database to latest"
	@echo "  db-current     - Show current LOCAL migration version"
	@echo "  db-current-staging - Show current STAGING migration version"
	@echo "  db-history     - Show migration history"
	@echo "  db-fix-migration - Auto-fix migration revision issues"
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
	@echo "  db-staging-cost-check - Check database cost optimization settings"
	@echo ""
	@echo "Database - Seed Data:"
	@echo "  db-seed-local     - Seed local database with demo data"
	@echo "  db-seed-staging   - Seed staging database with demo data"
	@echo "  db-seed-staging-pooler - Seed staging via Supabase pooler (備用方案)"
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
