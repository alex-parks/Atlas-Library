@echo off
REM Blacksmith Atlas Docker Scripts for Windows
REM This script replaces the npm scripts with Docker commands

setlocal enabledelayedexpansion

REM Check if command is provided
if "%1"=="" goto :usage

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)

REM Check if docker-compose is available
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] docker-compose is not installed. Please install it and try again.
    exit /b 1
)

REM Route to appropriate function based on command
if "%1"=="start" goto :start_atlas
if "%1"=="dev" goto :start_atlas
if "%1"=="backend" goto :start_backend
if "%1"=="frontend" goto :start_frontend
if "%1"=="stop" goto :stop_atlas
if "%1"=="kill" goto :stop_atlas
if "%1"=="restart" goto :restart_atlas
if "%1"=="logs" goto :view_logs
if "%1"=="status" goto :show_status
if "%1"=="setup-db" goto :setup_database
if "%1"=="db:setup" goto :setup_database
if "%1"=="test" goto :run_tests
if "%1"=="cleanup" goto :cleanup
if "%1"=="clean" goto :cleanup
if "%1"=="build" goto :build_images
goto :usage

:start_atlas
echo [INFO] Building and starting Blacksmith Atlas...
echo [INFO] Building Docker images...
docker-compose build --no-cache
if errorlevel 1 (
    echo [ERROR] Build failed
    exit /b 1
)

echo [INFO] Starting services...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start services
    exit /b 1
)

echo [INFO] Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo [INFO] Checking service health...
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Backend health check failed, but service may still be starting
) else (
    echo [SUCCESS] Backend is healthy
)

curl -f http://localhost:3011 >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Frontend may still be starting
) else (
    echo [SUCCESS] Frontend is running
)

echo [SUCCESS] Blacksmith Atlas is starting up!
echo [INFO] Backend API: http://localhost:8000
echo [INFO] Frontend: http://localhost:3011
echo [INFO] ArangoDB: http://localhost:8529
echo [INFO] API Docs: http://localhost:8000/docs
goto :end

:start_backend
echo [INFO] Starting backend only...
docker-compose up -d backend arangodb
if errorlevel 1 (
    echo [ERROR] Failed to start backend
    exit /b 1
)
echo [SUCCESS] Backend started
echo [INFO] API: http://localhost:8000
echo [INFO] Docs: http://localhost:8000/docs
goto :end

:start_frontend
echo [INFO] Starting frontend only...
docker-compose up -d frontend
if errorlevel 1 (
    echo [ERROR] Failed to start frontend
    exit /b 1
)
echo [SUCCESS] Frontend started
echo [INFO] Frontend: http://localhost:3011
goto :end

:stop_atlas
echo [INFO] Stopping all Blacksmith Atlas containers...
docker-compose down --remove-orphans
echo [SUCCESS] All containers stopped
goto :end

:restart_atlas
echo [INFO] Restarting Blacksmith Atlas...
docker-compose restart
echo [SUCCESS] Services restarted
goto :end

:view_logs
if "%2"=="" (
    echo [INFO] Showing logs for all services...
    docker-compose logs -f
) else (
    echo [INFO] Showing logs for %2...
    docker-compose logs -f %2
)
goto :end

:show_status
echo [INFO] Blacksmith Atlas Status:
echo.
docker-compose ps
echo.
echo [INFO] Service URLs:
echo   Backend API: http://localhost:8000
echo   Frontend: http://localhost:3011
echo   ArangoDB: http://localhost:8529
echo   API Docs: http://localhost:8000/docs
goto :end

:setup_database
echo [INFO] Setting up database...
docker-compose exec backend python -m backend.assetlibrary.database.setup_arango_database
echo [SUCCESS] Database setup complete
goto :end

:run_tests
echo [INFO] Running tests...
docker-compose exec backend python -m pytest
echo [SUCCESS] Tests complete
goto :end

:cleanup
echo [INFO] Cleaning up Blacksmith Atlas...
docker-compose down --volumes --remove-orphans
docker system prune -f
echo [SUCCESS] Cleanup complete
goto :end

:build_images
echo [INFO] Building Docker images...
docker-compose build --no-cache
echo [SUCCESS] Build complete
goto :end

:usage
echo Blacksmith Atlas Docker Scripts for Windows
echo.
echo Usage: %0 {command}
echo.
echo Commands:
echo   start, dev     - Start all services (backend, frontend, database)
echo   backend        - Start backend and database only
echo   frontend       - Start frontend only
echo   stop, kill     - Stop all services
echo   restart        - Restart all services
echo   logs [service] - View logs (all services or specific service)
echo   status         - Show service status and URLs
echo   setup-db       - Setup database schema and initial data
echo   test           - Run tests
echo   cleanup        - Stop services and clean up volumes/images
echo   build          - Build Docker images
echo.
echo Examples:
echo   %0 start       # Start everything
echo   %0 logs backend # View backend logs
echo   %0 status      # Check service status
goto :end

:end
endlocal 