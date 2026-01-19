#!/bin/bash

# Deploy script for Payment Tracker
# Usage: ./deploy.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BUILD_ALL=false
BUILD_BACKEND=false
BUILD_FRONTEND=false
BUILD_DB=false
NO_CACHE=false
DETACH=true
LOGS=false
DOWN_FIRST=false
PRUNE=false

print_usage() {
    echo -e "${BLUE}Payment Tracker Deploy Script${NC}"
    echo ""
    echo "Usage: ./deploy.sh [options]"
    echo ""
    echo "Build Options:"
    echo "  -a, --all          Rebuild all containers"
    echo "  -b, --backend      Rebuild backend container only"
    echo "  -f, --frontend     Rebuild frontend container only"
    echo "  -d, --db           Rebuild database container only"
    echo "  --no-cache         Build without using cache"
    echo ""
    echo "Run Options:"
    echo "  --foreground       Run in foreground (don't detach)"
    echo "  -l, --logs         Follow logs after starting"
    echo "  --down             Stop and remove containers before rebuilding"
    echo ""
    echo "Maintenance:"
    echo "  --prune            Remove unused Docker resources after deploy"
    echo "  --status           Show container status and exit"
    echo "  --stop             Stop all containers and exit"
    echo "  --restart          Restart all containers without rebuilding"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh                    # Just start containers (no rebuild)"
    echo "  ./deploy.sh -a                 # Rebuild all and start"
    echo "  ./deploy.sh -b                 # Rebuild backend only and start"
    echo "  ./deploy.sh -b -f              # Rebuild backend and frontend"
    echo "  ./deploy.sh -a --no-cache      # Full rebuild without cache"
    echo "  ./deploy.sh --down -a          # Stop, rebuild all, start"
    echo "  ./deploy.sh -b -l              # Rebuild backend and follow logs"
}

print_status() {
    echo -e "${BLUE}=== Container Status ===${NC}"
    docker compose ps
    echo ""
    echo -e "${BLUE}=== Resource Usage ===${NC}"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker compose ps -q 2>/dev/null) 2>/dev/null || echo "No running containers"
}

stop_containers() {
    echo -e "${YELLOW}Stopping containers...${NC}"
    docker compose down
    echo -e "${GREEN}Containers stopped${NC}"
}

restart_containers() {
    echo -e "${YELLOW}Restarting containers...${NC}"
    docker compose restart
    echo -e "${GREEN}Containers restarted${NC}"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--all)
            BUILD_ALL=true
            shift
            ;;
        -b|--backend)
            BUILD_BACKEND=true
            shift
            ;;
        -f|--frontend)
            BUILD_FRONTEND=true
            shift
            ;;
        -d|--db)
            BUILD_DB=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --foreground)
            DETACH=false
            shift
            ;;
        -l|--logs)
            LOGS=true
            shift
            ;;
        --down)
            DOWN_FIRST=true
            shift
            ;;
        --prune)
            PRUNE=true
            shift
            ;;
        --status)
            print_status
            exit 0
            ;;
        --stop)
            stop_containers
            exit 0
            ;;
        --restart)
            restart_containers
            exit 0
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Build cache option
CACHE_OPT=""
if [ "$NO_CACHE" = true ]; then
    CACHE_OPT="--no-cache"
    echo -e "${YELLOW}Building without cache${NC}"
fi

# Stop containers first if requested
if [ "$DOWN_FIRST" = true ]; then
    echo -e "${YELLOW}Stopping existing containers...${NC}"
    docker compose down
fi

# Build containers
if [ "$BUILD_ALL" = true ]; then
    echo -e "${BLUE}Building all containers...${NC}"
    docker compose build $CACHE_OPT
elif [ "$BUILD_BACKEND" = true ] || [ "$BUILD_FRONTEND" = true ] || [ "$BUILD_DB" = true ]; then
    SERVICES=""
    if [ "$BUILD_BACKEND" = true ]; then
        SERVICES="$SERVICES backend"
        echo -e "${BLUE}Building backend...${NC}"
    fi
    if [ "$BUILD_FRONTEND" = true ]; then
        SERVICES="$SERVICES frontend"
        echo -e "${BLUE}Building frontend...${NC}"
    fi
    if [ "$BUILD_DB" = true ]; then
        SERVICES="$SERVICES db"
        echo -e "${BLUE}Building database...${NC}"
    fi
    docker compose build $CACHE_OPT $SERVICES
fi

# Start containers
echo -e "${BLUE}Starting containers...${NC}"
if [ "$DETACH" = true ]; then
    docker compose up -d
    echo -e "${GREEN}Containers started in background${NC}"

    # Show status
    echo ""
    print_status
else
    docker compose up
fi

# Prune if requested
if [ "$PRUNE" = true ]; then
    echo -e "${YELLOW}Pruning unused Docker resources...${NC}"
    docker system prune -f
    echo -e "${GREEN}Prune complete${NC}"
fi

# Follow logs if requested
if [ "$LOGS" = true ] && [ "$DETACH" = true ]; then
    echo ""
    echo -e "${BLUE}Following logs (Ctrl+C to exit)...${NC}"
    docker compose logs -f
fi
