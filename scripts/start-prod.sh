#!/bin/bash
# Start Blacksmith Atlas in production mode with external ArangoDB

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Blacksmith Atlas in Production Mode${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please copy .env.example to .env and configure your ArangoDB settings:${NC}"
    echo "  cp .env.example .env"
    echo "  # Then edit .env with your company's ArangoDB credentials"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Validate required environment variables
if [ -z "$ARANGO_HOST" ] || [ "$ARANGO_HOST" == "your-company-arangodb-host.com" ]; then
    echo -e "${RED}Error: ARANGO_HOST not configured in .env file${NC}"
    exit 1
fi

if [ -z "$ARANGO_USER" ] || [ "$ARANGO_USER" == "your_username" ]; then
    echo -e "${RED}Error: ARANGO_USER not configured in .env file${NC}"
    exit 1
fi

if [ -z "$ARANGO_PASSWORD" ] || [ "$ARANGO_PASSWORD" == "your_password" ]; then
    echo -e "${RED}Error: ARANGO_PASSWORD not configured in .env file${NC}"
    exit 1
fi

echo -e "${GREEN}Configuration:${NC}"
echo "  ArangoDB Host: $ARANGO_HOST:$ARANGO_PORT"
echo "  Database: $ARANGO_DATABASE"
echo "  User: $ARANGO_USER"

# Start services using production compose file
echo -e "\n${GREEN}Starting services...${NC}"
podman compose -f docker-compose.prod.yml up -d

# Wait for services to start
echo -e "\n${YELLOW}Waiting for services to start...${NC}"
sleep 5

# Check backend health
echo -e "\n${GREEN}Checking backend health...${NC}"
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
    echo "Check logs with: podman logs blacksmith-atlas-backend"
fi

echo -e "\n${GREEN}Blacksmith Atlas is running!${NC}"
echo "  Frontend: http://localhost:3011"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "To view logs: podman compose -f docker-compose.prod.yml logs -f"
echo "To stop: podman compose -f docker-compose.prod.yml down"