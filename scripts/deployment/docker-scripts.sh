#!/bin/bash

# Blacksmith Atlas Docker Scripts
# This script replaces the npm scripts with Docker commands

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null; then
        print_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi
}

# Function to stop all Atlas containers
stop_atlas() {
    print_status "Stopping all Blacksmith Atlas containers..."
    docker-compose down --remove-orphans
    print_success "All containers stopped"
}

# Function to build and start all services
start_atlas() {
    print_status "Building and starting Blacksmith Atlas..."
    
    # Build images
    print_status "Building Docker images..."
    docker-compose build --no-cache
    
    # Start services
    print_status "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    print_status "Checking service health..."
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend is healthy"
    else
        print_warning "Backend health check failed, but service may still be starting"
    fi
    
    if curl -f http://localhost:3011 > /dev/null 2>&1; then
        print_success "Frontend is running"
    else
        print_warning "Frontend may still be starting"
    fi
    
    print_success "Blacksmith Atlas is starting up!"
    print_status "Backend API: http://localhost:8000"
    print_status "Frontend: http://localhost:3011"
    print_status "ArangoDB: http://localhost:8529"
    print_status "API Docs: http://localhost:8000/docs"
}

# Function to start only backend
start_backend() {
    print_status "Starting backend only..."
    docker-compose up -d backend arangodb
    print_success "Backend started"
    print_status "API: http://localhost:8000"
    print_status "Docs: http://localhost:8000/docs"
}

# Function to start only frontend
start_frontend() {
    print_status "Starting frontend only..."
    docker-compose up -d frontend
    print_success "Frontend started"
    print_status "Frontend: http://localhost:3011"
}

# Function to view logs
view_logs() {
    local service=${1:-""}
    if [ -z "$service" ]; then
        print_status "Showing logs for all services..."
        docker-compose logs -f
    else
        print_status "Showing logs for $service..."
        docker-compose logs -f "$service"
    fi
}

# Function to restart services
restart_atlas() {
    print_status "Restarting Blacksmith Atlas..."
    docker-compose restart
    print_success "Services restarted"
}

# Function to clean up everything
cleanup() {
    print_status "Cleaning up Blacksmith Atlas..."
    docker-compose down --volumes --remove-orphans
    docker system prune -f
    print_success "Cleanup complete"
}

# Function to show status
show_status() {
    print_status "Blacksmith Atlas Status:"
    echo ""
    docker-compose ps
    echo ""
    print_status "Service URLs:"
    echo "  Backend API: http://localhost:8000"
    echo "  Frontend: http://localhost:3011"
    echo "  ArangoDB: http://localhost:8529"
    echo "  API Docs: http://localhost:8000/docs"
}

# Function to setup database
setup_database() {
    print_status "Setting up database..."
    docker-compose exec backend python -m backend.assetlibrary.database.setup_arango_database
    print_success "Database setup complete"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    docker-compose exec backend python -m pytest
    print_success "Tests complete"
}

# Main script logic
case "${1:-}" in
    "start"|"dev")
        check_docker
        check_docker_compose
        stop_atlas
        start_atlas
        ;;
    "backend")
        check_docker
        check_docker_compose
        start_backend
        ;;
    "frontend")
        check_docker
        check_docker_compose
        start_frontend
        ;;
    "stop"|"kill")
        check_docker_compose
        stop_atlas
        ;;
    "restart")
        check_docker_compose
        restart_atlas
        ;;
    "logs")
        check_docker_compose
        view_logs "$2"
        ;;
    "status")
        check_docker_compose
        show_status
        ;;
    "setup-db"|"db:setup")
        check_docker_compose
        setup_database
        ;;
    "test")
        check_docker_compose
        run_tests
        ;;
    "cleanup"|"clean")
        check_docker_compose
        cleanup
        ;;
    "build")
        check_docker
        check_docker_compose
        print_status "Building Docker images..."
        docker-compose build --no-cache
        print_success "Build complete"
        ;;
    *)
        echo "Blacksmith Atlas Docker Scripts"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  start, dev     - Start all services (backend, frontend, database)"
        echo "  backend        - Start backend and database only"
        echo "  frontend       - Start frontend only"
        echo "  stop, kill     - Stop all services"
        echo "  restart        - Restart all services"
        echo "  logs [service] - View logs (all services or specific service)"
        echo "  status         - Show service status and URLs"
        echo "  setup-db       - Setup database schema and initial data"
        echo "  test           - Run tests"
        echo "  cleanup        - Stop services and clean up volumes/images"
        echo "  build          - Build Docker images"
        echo ""
        echo "Examples:"
        echo "  $0 start       # Start everything"
        echo "  $0 logs backend # View backend logs"
        echo "  $0 status      # Check service status"
        ;;
esac 