#!/bin/bash

# Blacksmith Atlas Metadata Ingester Runner
# This script provides easy commands to run the metadata ingester

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Default values
API_URL="http://localhost:8000"
VERBOSE=""
DRY_RUN=""

# Help function
show_help() {
    cat << EOF
Blacksmith Atlas Metadata Ingester

Usage: $0 [OPTIONS] COMMAND [ARGS...]

Commands:
  test                    Test ingester with example metadata.json
  file <path>            Ingest single metadata file
  dir <path>             Ingest all metadata files in directory
  recursive <path>       Ingest all metadata files recursively
  help                   Show this help

Options:
  --api-url <url>        Atlas API URL (default: http://localhost:8000)
  --verbose              Enable verbose logging
  --dry-run              Parse files but don't create assets

Examples:
  $0 test                                    # Test with example file
  $0 file /path/to/metadata.json           # Ingest single file
  $0 dir /path/to/assets                    # Ingest directory
  $0 recursive /path/to/library --verbose   # Recursive with verbose output
  $0 file metadata.json --dry-run           # Validate file without creating asset

EOF
}

# Check if Atlas API is running
check_api() {
    echo -e "${BLUE}🔍 Checking Atlas API at $API_URL...${NC}"
    
    if curl -sf "$API_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Atlas API is running${NC}"
        return 0
    else
        echo -e "${RED}❌ Atlas API is not accessible at $API_URL${NC}"
        echo -e "${YELLOW}💡 Make sure the API is running with: npm run docker:dev${NC}"
        return 1
    fi
}

# Run Python ingester
run_ingester() {
    local cmd="$1"
    shift
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Set Python path
    export PYTHONPATH="$PROJECT_ROOT/backend:$PYTHONPATH"
    
    # Run the ingester
    case "$cmd" in
        "test")
            echo -e "${BLUE}🧪 Running test ingester...${NC}"
            python3 scripts/utilities/test_ingester.py
            ;;
        "file")
            if [[ $# -eq 0 ]]; then
                echo -e "${RED}❌ Error: file path required${NC}"
                exit 1
            fi
            python3 scripts/utilities/ingest_metadata.py "$@" $VERBOSE $DRY_RUN --api-url "$API_URL"
            ;;
        "dir")
            if [[ $# -eq 0 ]]; then
                echo -e "${RED}❌ Error: directory path required${NC}"
                exit 1
            fi
            python3 scripts/utilities/ingest_metadata.py "$@" $VERBOSE $DRY_RUN --api-url "$API_URL" --directory
            ;;
        "recursive")
            if [[ $# -eq 0 ]]; then
                echo -e "${RED}❌ Error: directory path required${NC}"
                exit 1
            fi
            python3 scripts/utilities/ingest_metadata.py "$@" $VERBOSE $DRY_RUN --api-url "$API_URL" --directory --recursive
            ;;
        *)
            echo -e "${RED}❌ Error: unknown command '$cmd'${NC}"
            show_help
            exit 1
            ;;
    esac
}

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        help|--help|-h)
            show_help
            exit 0
            ;;
        -*)
            echo -e "${RED}❌ Error: unknown option '$1'${NC}"
            show_help
            exit 1
            ;;
        *)
            break
            ;;
    esac
done

# Check if command provided
if [[ $# -eq 0 ]]; then
    echo -e "${RED}❌ Error: command required${NC}"
    show_help
    exit 1
fi

# Get command
COMMAND="$1"
shift

# Handle help command
if [[ "$COMMAND" == "help" ]]; then
    show_help
    exit 0
fi

# Check API unless it's a dry run
if [[ -z "$DRY_RUN" ]]; then
    if ! check_api; then
        exit 1
    fi
fi

# Run the command
echo -e "${BLUE}🚀 Starting Atlas Metadata Ingester...${NC}"
echo -e "${BLUE}   Command: $COMMAND${NC}"
echo -e "${BLUE}   API URL: $API_URL${NC}"
if [[ -n "$VERBOSE" ]]; then
    echo -e "${BLUE}   Verbose: enabled${NC}"
fi
if [[ -n "$DRY_RUN" ]]; then
    echo -e "${YELLOW}   Dry run: enabled (no assets will be created)${NC}"
fi
echo ""

# Run the ingester
if run_ingester "$COMMAND" "$@"; then
    echo ""
    echo -e "${GREEN}🎉 Ingestion completed successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Ingestion failed${NC}"
    exit 1
fi