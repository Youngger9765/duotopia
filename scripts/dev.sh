#!/bin/bash

# =============================================================================
# Development Environment Management Script
# =============================================================================
#
# Usage: ./scripts/dev.sh [command] [service]
#
# Commands:
#   start   [service]  Start services (default: all)
#   stop    [service]  Stop services (default: all)
#   restart [service]  Restart services (default: all)
#   status             Show status of all services
#   logs    <service>  Show last 100 lines of logs
#   logs-f  <service>  Follow logs in real-time (like tail -f)
#   kill-port <port>   Kill processes using a specific port
#
# Services:
#   all       All services (db + backend + frontend)
#   backend   Python FastAPI backend (port 8080)
#   frontend  Vite React frontend (port 5173)
#   db        PostgreSQL + Redis (Docker)
#
# Examples:
#   ./scripts/dev.sh start             # Start everything in background
#   ./scripts/dev.sh start backend     # Start only backend
#   ./scripts/dev.sh stop              # Stop everything
#   ./scripts/dev.sh stop frontend     # Stop only frontend
#   ./scripts/dev.sh restart           # Restart all services
#   ./scripts/dev.sh restart backend   # Restart only backend
#   ./scripts/dev.sh status            # Check status of all services
#   ./scripts/dev.sh logs backend      # View last 100 lines of backend logs
#   ./scripts/dev.sh logs frontend     # View last 100 lines of frontend logs
#   ./scripts/dev.sh logs-f backend    # Follow backend logs in real-time
#   ./scripts/dev.sh logs-f frontend   # Follow frontend logs in real-time
#   ./scripts/dev.sh kill-port 8080    # Free port 8080 if stuck
#
# Features:
#   - All services run in background (no need to keep terminal open)
#   - PID files stored in .dev-pids/ for process management
#   - Log files stored in .dev-logs/ for easy access
#   - Individual or batch control of services
#   - Real-time log following with logs-f command
#   - Automatic status display after start/stop/restart all
#
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$PROJECT_ROOT/.dev-pids"
LOG_DIR="$PROJECT_ROOT/.dev-logs"

# Create directories if they don't exist
mkdir -p "$PID_DIR" "$LOG_DIR"

# Helper functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

is_running() {
    local pid_file="$PID_DIR/$1.pid"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

get_pid() {
    local pid_file="$PID_DIR/$1.pid"
    if [ -f "$pid_file" ]; then
        cat "$pid_file"
    fi
}

# Start functions
start_db() {
    log_info "Starting database (PostgreSQL + Redis)..."
    cd "$PROJECT_ROOT"
    docker-compose up -d db redis
    log_success "Database services started"
}

kill_port() {
    local port=$1
    local pids=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pids" ]; then
        log_info "Killing processes on port $port: $pids"
        echo "$pids" | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
}

find_available_port() {
    local base_port=${1:-8080}
    local max_tries=10
    for i in $(seq 0 $max_tries); do
        local port=$((base_port + i))
        if ! lsof -ti :$port > /dev/null 2>&1; then
            echo $port
            return 0
        fi
    done
    echo $base_port
    return 1
}

update_frontend_env() {
    local port=$1
    local env_file="$PROJECT_ROOT/frontend/.env.local"

    # Update or add VITE_BACKEND_PORT and VITE_API_URL
    if [ -f "$env_file" ]; then
        # Update VITE_BACKEND_PORT
        if grep -q "^VITE_BACKEND_PORT=" "$env_file"; then
            sed -i '' "s/^VITE_BACKEND_PORT=.*/VITE_BACKEND_PORT=$port/" "$env_file"
        else
            # Ensure file ends with newline before appending
            [ -n "$(tail -c1 "$env_file")" ] && echo "" >> "$env_file"
            echo "" >> "$env_file"
            echo "# Backend port (auto-managed by dev.sh)" >> "$env_file"
            echo "VITE_BACKEND_PORT=$port" >> "$env_file"
        fi
        # Update VITE_API_URL
        if grep -q "^VITE_API_URL=" "$env_file"; then
            sed -i '' "s|^VITE_API_URL=.*|VITE_API_URL=http://localhost:$port|" "$env_file"
        fi
    else
        echo "VITE_BACKEND_PORT=$port" > "$env_file"
        echo "VITE_API_URL=http://localhost:$port" >> "$env_file"
    fi
}

start_backend() {
    if is_running "backend"; then
        log_warning "Backend is already running (PID: $(get_pid backend))"
        return
    fi

    # Try to free port 8080 first
    if lsof -ti :8080 > /dev/null 2>&1; then
        log_warning "Port 8080 is in use, attempting to free it..."
        kill_port 8080
        sleep 1
    fi

    # Find available port (try 8080 first, then 8081, 8082...)
    local port=$(find_available_port 8080)

    if [ "$port" != "8080" ]; then
        log_warning "Port 8080 still occupied, using port $port instead"
    fi

    log_info "Starting backend on port $port..."
    cd "$PROJECT_ROOT/backend"

    # Run in background and save PID
    nohup python3 -m uvicorn main:app --reload --port $port > "$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$PID_DIR/backend.pid"
    echo $port > "$PID_DIR/backend.port"

    sleep 2
    if is_running "backend"; then
        log_success "Backend started (PID: $(get_pid backend)) - http://localhost:$port"

        # Update frontend environment
        update_frontend_env $port
        log_info "Updated frontend .env.local with VITE_BACKEND_PORT=$port"

        # If frontend is running, warn user to restart
        if is_running "frontend"; then
            log_warning "Frontend is running - restart it to use new backend port: ./scripts/dev.sh restart frontend"
        fi
    else
        log_error "Failed to start backend. Check logs: ./scripts/dev.sh logs backend"
    fi
}

start_frontend() {
    if is_running "frontend"; then
        log_warning "Frontend is already running (PID: $(get_pid frontend))"
        return
    fi

    log_info "Starting frontend..."
    cd "$PROJECT_ROOT/frontend"

    # Run in background and save PID
    nohup npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
    echo $! > "$PID_DIR/frontend.pid"

    sleep 3
    if is_running "frontend"; then
        log_success "Frontend started (PID: $(get_pid frontend)) - http://localhost:5173"
    else
        log_error "Failed to start frontend. Check logs: ./scripts/dev.sh logs frontend"
    fi
}

# Stop functions
stop_db() {
    log_info "Stopping database services..."
    cd "$PROJECT_ROOT"
    docker-compose stop db redis
    log_success "Database services stopped"
}

stop_backend() {
    if ! is_running "backend"; then
        log_warning "Backend is not running"
        rm -f "$PID_DIR/backend.pid" "$PID_DIR/backend.port"
        return
    fi

    local pid=$(get_pid backend)
    log_info "Stopping backend (PID: $pid)..."

    # Kill the process and all children (uvicorn spawns workers)
    pkill -P "$pid" 2>/dev/null || true
    kill "$pid" 2>/dev/null || true

    rm -f "$PID_DIR/backend.pid" "$PID_DIR/backend.port"
    log_success "Backend stopped"
}

stop_frontend() {
    if ! is_running "frontend"; then
        log_warning "Frontend is not running"
        rm -f "$PID_DIR/frontend.pid"
        return
    fi

    local pid=$(get_pid frontend)
    log_info "Stopping frontend (PID: $pid)..."

    # Kill the process and all children
    pkill -P "$pid" 2>/dev/null || true
    kill "$pid" 2>/dev/null || true

    rm -f "$PID_DIR/frontend.pid"
    log_success "Frontend stopped"
}

# Status function
show_status() {
    echo ""
    echo "=== Development Environment Status ==="
    echo ""

    # Database
    if docker-compose ps db 2>/dev/null | grep -q "Up"; then
        echo -e "  Database (PostgreSQL): ${GREEN}Running${NC}"
    else
        echo -e "  Database (PostgreSQL): ${RED}Stopped${NC}"
    fi

    if docker-compose ps redis 2>/dev/null | grep -q "Up"; then
        echo -e "  Redis:                 ${GREEN}Running${NC}"
    else
        echo -e "  Redis:                 ${RED}Stopped${NC}"
    fi

    # Backend
    if is_running "backend"; then
        local backend_port="8080"
        if [ -f "$PID_DIR/backend.port" ]; then
            backend_port=$(cat "$PID_DIR/backend.port")
        fi
        echo -e "  Backend:               ${GREEN}Running${NC} (PID: $(get_pid backend)) - http://localhost:$backend_port"
    else
        echo -e "  Backend:               ${RED}Stopped${NC}"
    fi

    # Frontend
    if is_running "frontend"; then
        echo -e "  Frontend:              ${GREEN}Running${NC} (PID: $(get_pid frontend)) - http://localhost:5173"
    else
        echo -e "  Frontend:              ${RED}Stopped${NC}"
    fi

    echo ""
}

# Logs function
show_logs() {
    local service=$1
    local follow=${2:-false}

    case $service in
        backend)
            if [ "$follow" = "true" ]; then
                tail -f "$LOG_DIR/backend.log"
            else
                tail -100 "$LOG_DIR/backend.log"
            fi
            ;;
        frontend)
            if [ "$follow" = "true" ]; then
                tail -f "$LOG_DIR/frontend.log"
            else
                tail -100 "$LOG_DIR/frontend.log"
            fi
            ;;
        db)
            docker-compose logs ${follow:+-f} db
            ;;
        *)
            log_error "Unknown service: $service"
            echo "Available services: backend, frontend, db"
            exit 1
            ;;
    esac
}

# Main command handling
COMMAND=${1:-help}
SERVICE=${2:-all}

case $COMMAND in
    start)
        case $SERVICE in
            all)
                start_db
                sleep 2
                start_backend
                start_frontend
                echo ""
                show_status
                ;;
            backend)
                start_backend
                ;;
            frontend)
                start_frontend
                ;;
            db)
                start_db
                ;;
            *)
                log_error "Unknown service: $SERVICE"
                echo "Available services: all, backend, frontend, db"
                exit 1
                ;;
        esac
        ;;

    stop)
        case $SERVICE in
            all)
                stop_frontend
                stop_backend
                stop_db
                echo ""
                show_status
                ;;
            backend)
                stop_backend
                ;;
            frontend)
                stop_frontend
                ;;
            db)
                stop_db
                ;;
            *)
                log_error "Unknown service: $SERVICE"
                exit 1
                ;;
        esac
        ;;

    restart)
        case $SERVICE in
            all)
                stop_frontend
                stop_backend
                stop_db
                sleep 2
                start_db
                sleep 2
                start_backend
                start_frontend
                echo ""
                show_status
                ;;
            backend)
                stop_backend
                sleep 1
                start_backend
                ;;
            frontend)
                stop_frontend
                sleep 1
                start_frontend
                ;;
            db)
                stop_db
                sleep 1
                start_db
                ;;
            *)
                log_error "Unknown service: $SERVICE"
                exit 1
                ;;
        esac
        ;;

    status)
        show_status
        ;;

    logs)
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "all" ]; then
            log_error "Please specify a service: backend, frontend, or db"
            exit 1
        fi
        show_logs "$SERVICE" false
        ;;

    logs-f|logsf|follow)
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "all" ]; then
            log_error "Please specify a service: backend, frontend, or db"
            exit 1
        fi
        show_logs "$SERVICE" true
        ;;

    kill-port)
        if [ -z "$SERVICE" ] || [ "$SERVICE" = "all" ]; then
            log_error "Please specify a port number"
            echo "Usage: ./scripts/dev.sh kill-port 8080"
            exit 1
        fi
        kill_port "$SERVICE"
        if lsof -ti :"$SERVICE" > /dev/null 2>&1; then
            log_warning "Port $SERVICE may still be in use (zombie process)"
        else
            log_success "Port $SERVICE is now free"
        fi
        ;;

    help|--help|-h|*)
        echo ""
        echo "Development Environment Manager"
        echo ""
        echo "Usage: ./scripts/dev.sh [command] [service]"
        echo ""
        echo "Commands:"
        echo "  start   [service]  Start services (default: all)"
        echo "  stop    [service]  Stop services (default: all)"
        echo "  restart [service]  Restart services (default: all)"
        echo "  status             Show status of all services"
        echo "  logs    <service>  Show last 100 lines of logs"
        echo "  logs-f  <service>  Follow logs in real-time"
        echo "  kill-port <port>   Kill processes using a specific port"
        echo ""
        echo "Services:"
        echo "  all       All services (db + backend + frontend)"
        echo "  backend   Python FastAPI backend (port 8080)"
        echo "  frontend  Vite React frontend (port 5173)"
        echo "  db        PostgreSQL + Redis (Docker)"
        echo ""
        echo "Examples:"
        echo "  ./scripts/dev.sh start           # Start everything"
        echo "  ./scripts/dev.sh start backend   # Start only backend"
        echo "  ./scripts/dev.sh stop            # Stop everything"
        echo "  ./scripts/dev.sh restart frontend"
        echo "  ./scripts/dev.sh status"
        echo "  ./scripts/dev.sh logs backend"
        echo "  ./scripts/dev.sh logs-f frontend # Follow frontend logs"
        echo "  ./scripts/dev.sh kill-port 8080  # Free port 8080"
        echo ""
        ;;
esac
