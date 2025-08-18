.PHONY: help install dev build test clean

help:
	@echo "Available commands:"
	@echo "  install    Install all dependencies"
	@echo "  dev        Start development servers"
	@echo "  build      Build for production"
	@echo "  test       Run tests"
	@echo "  clean      Clean build artifacts"
	@echo "  db-up      Start database containers"
	@echo "  db-down    Stop database containers"
	@echo "  migrate    Run database migrations"

install:
	npm install
	cd backend && pip install -r requirements.txt

dev:
	npm run dev

build:
	npm run build

test:
	npm test

clean:
	rm -rf node_modules
	rm -rf frontend/dist
	rm -rf backend/__pycache__
	rm -rf shared/dist

db-up:
	docker-compose up -d

db-down:
	docker-compose down

migrate:
	cd backend && alembic upgrade head