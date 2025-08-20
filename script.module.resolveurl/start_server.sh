#!/bin/bash
# ResolveURL API Startup Script

echo "=== ResolveURL API Startup Script ==="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "functional_server.py" ]; then
    echo "Error: functional_server.py not found"
    echo "Please run this script from the script.module.resolveurl directory"
    exit 1
fi

# Check if requirements are installed
if ! python3 -c "import flask" &> /dev/null; then
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install dependencies"
        exit 1
    fi
fi

# Default values
HOST="127.0.0.1"
PORT="5000"
DEBUG=false

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
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --host HOST     Host to bind to (default: 127.0.0.1)"
            echo "  --port PORT     Port to bind to (default: 5000)"
            echo "  --debug         Enable debug mode"
            echo "  --help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                           # Start on localhost:5000"
            echo "  $0 --host 0.0.0.0 --port 8080  # Start on all interfaces, port 8080"
            echo "  $0 --debug                  # Start with debug mode enabled"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "Starting ResolveURL API server..."
echo "Host: $HOST"
echo "Port: $PORT"
echo "Debug: $DEBUG"
echo ""
echo "Web interface will be available at: http://$HOST:$PORT"
echo "API health check: http://$HOST:$PORT/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Build the command
CMD="python3 functional_server.py --host $HOST --port $PORT"
if [ "$DEBUG" = true ]; then
    CMD="$CMD --debug"
fi

# Run the server
exec $CMD