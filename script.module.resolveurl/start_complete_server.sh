#!/bin/bash

# ResolveURL Complete API Server Startup Script
# Supports both the simple functional server and the complete integration

set -e

# Default values
HOST="127.0.0.1"
PORT="5000"
DEBUG=false
SERVER_TYPE="complete"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_color() {
    echo -e "${1}${2}${NC}"
}

print_header() {
    echo
    print_color $BLUE "======================================"
    print_color $BLUE "  ResolveURL API Server Launcher"
    print_color $BLUE "======================================"
    echo
}

print_help() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --host HOST          Host to bind to (default: 127.0.0.1)"
    echo "  --port PORT          Port to bind to (default: 5000)"
    echo "  --debug              Enable debug mode"
    echo "  --server TYPE        Server type: 'complete' or 'functional' (default: complete)"
    echo "  --docker             Start with Docker Compose"
    echo "  --docker-build       Build and start with Docker Compose"
    echo "  --help               Show this help message"
    echo
    echo "Server Types:"
    echo "  complete    - Full integration with all 257+ ResolveURL plugins"
    echo "  functional  - Simple server with basic resolvers (original implementation)"
    echo
    echo "Examples:"
    echo "  $0                                    # Start complete server on localhost:5000"
    echo "  $0 --host 0.0.0.0 --port 8080       # Start on all interfaces, port 8080"
    echo "  $0 --server functional --debug       # Start functional server with debug"
    echo "  $0 --docker                          # Start with Docker Compose"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --server)
            SERVER_TYPE="$2"
            shift 2
            ;;
        --docker)
            DOCKER_MODE=true
            shift
            ;;
        --docker-build)
            DOCKER_BUILD=true
            shift
            ;;
        --help)
            print_help
            exit 0
            ;;
        *)
            print_color $RED "Unknown option: $1"
            print_help
            exit 1
            ;;
    esac
done

print_header

# Check if we're in the right directory
if [[ ! -f "complete_server.py" && ! -f "functional_server.py" ]]; then
    print_color $RED "Error: Server files not found!"
    print_color $YELLOW "Please run this script from the script.module.resolveurl directory"
    exit 1
fi

# Docker mode
if [[ "$DOCKER_MODE" == "true" || "$DOCKER_BUILD" == "true" ]]; then
    print_color $BLUE "Starting ResolveURL API in Docker mode..."
    
    if [[ "$DOCKER_BUILD" == "true" ]]; then
        print_color $YELLOW "Building Docker image..."
        docker-compose build
    fi
    
    print_color $YELLOW "Starting containers..."
    docker-compose up -d
    
    print_color $GREEN "Docker containers started!"
    print_color $BLUE "Web interface: http://localhost:8080"
    print_color $BLUE "Health check: http://localhost:8080/health"
    
    echo
    print_color $YELLOW "To view logs: docker-compose logs -f"
    print_color $YELLOW "To stop: docker-compose down"
    exit 0
fi

# Native Python mode
print_color $BLUE "Starting ResolveURL API Server..."
print_color $YELLOW "Server type: $SERVER_TYPE"
print_color $YELLOW "Host: $HOST"
print_color $YELLOW "Port: $PORT"
print_color $YELLOW "Debug: $DEBUG"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    print_color $RED "Error: Python 3 is not installed!"
    exit 1
fi

# Check and install requirements
if [[ ! -d "venv" ]]; then
    print_color $YELLOW "Creating virtual environment..."
    python3 -m venv venv
fi

print_color $YELLOW "Activating virtual environment..."
source venv/bin/activate

print_color $YELLOW "Installing/updating dependencies..."
pip install -r requirements.txt

# Determine which server to start
if [[ "$SERVER_TYPE" == "complete" ]]; then
    SERVER_FILE="complete_server.py"
    DESCRIPTION="Complete integration with all ResolveURL plugins"
elif [[ "$SERVER_TYPE" == "functional" ]]; then
    SERVER_FILE="functional_server.py"  
    DESCRIPTION="Simple functional server with basic resolvers"
else
    print_color $RED "Error: Invalid server type '$SERVER_TYPE'"
    print_color $YELLOW "Valid types: complete, functional"
    exit 1
fi

if [[ ! -f "$SERVER_FILE" ]]; then
    print_color $RED "Error: Server file '$SERVER_FILE' not found!"
    exit 1
fi

print_color $GREEN "Starting $DESCRIPTION..."
echo

# Build command
CMD="python3 $SERVER_FILE --host $HOST --port $PORT"
if [[ "$DEBUG" == "true" ]]; then
    CMD="$CMD --debug"
fi

# Show startup info
print_color $GREEN "Server starting on http://$HOST:$PORT"
print_color $BLUE "Web interface: http://$HOST:$PORT"
print_color $BLUE "Health check: http://$HOST:$PORT/health"
print_color $BLUE "API endpoint: http://$HOST:$PORT/api/resolve"

if [[ "$HOST" == "0.0.0.0" ]]; then
    print_color $YELLOW "Server accessible from all network interfaces"
fi

echo
print_color $YELLOW "Press Ctrl+C to stop the server"
echo

# Start the server
exec $CMD