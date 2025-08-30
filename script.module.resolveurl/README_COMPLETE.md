# ResolveURL Complete API Documentation

This document describes the complete ResolveURL REST API implementation that integrates all 257+ resolver plugins with a comprehensive standalone compatibility layer.

## Quick Start

### Native Python

```bash
# Start the complete server with all resolvers
./start_complete_server.sh

# Start on all interfaces, port 8080
./start_complete_server.sh --host 0.0.0.0 --port 8080

# Start with debug logging
./start_complete_server.sh --debug

# Start the original functional server
./start_complete_server.sh --server functional
```

### Docker

```bash
# Start with Docker Compose
./start_complete_server.sh --docker

# Build and start with Docker Compose
./start_complete_server.sh --docker-build

# Or manually
docker-compose up -d
```

## Features

### 🎯 Complete Resolver Integration
- **257+ Resolver Plugins** - All existing ResolveURL plugins included
- **Automatic Plugin Discovery** - Dynamically loads all available resolvers
- **Domain-based Routing** - Intelligent resolver selection by URL patterns
- **Priority System** - Resolvers ordered by priority for optimal resolution

### 🔧 Advanced Compatibility Layer
- **Zero Kodi Dependencies** - Complete standalone operation
- **Mock XBMC/Kodi APIs** - Comprehensive compatibility layer
- **Plugin Compatibility** - Works with existing resolver plugins without modification
- **Fallback Systems** - Multiple resolution strategies for maximum success

### 🌐 Enhanced API Features
- **Resolver Search** - Find resolvers by domain or pattern
- **Batch Resolution** - Resolve multiple URLs simultaneously  
- **Detailed Statistics** - Comprehensive resolver and system information
- **Health Monitoring** - Built-in health checks and status endpoints

## API Endpoints

### Core Resolution

#### POST `/api/resolve`
Resolve a single URL to a direct media link.

**Request:**
```json
{
  "url": "https://example.com/video-link"
}
```

**Response:**
```json
{
  "success": true,
  "original_url": "https://example.com/video-link",
  "resolved_url": "https://cdn.example.com/video.mp4",
  "message": "URL resolved successfully",
  "system": "Complete ResolveURL integration"
}
```

#### POST `/api/resolve/multiple`
Resolve multiple URLs in a single request.

**Request:**
```json
{
  "urls": [
    "https://youtube.com/watch?v=VIDEO_ID",
    "https://streamtape.com/e/VIDEO_ID",
    "https://example.com/video.mp4"
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "original_url": "https://youtube.com/watch?v=VIDEO_ID",
      "success": true,
      "resolved_url": "plugin://plugin.video.youtube/play/?video_id=VIDEO_ID"
    },
    {
      "original_url": "https://streamtape.com/e/VIDEO_ID", 
      "success": true,
      "resolved_url": "https://streamtape.com/get_video?id=VIDEO_ID"
    },
    {
      "original_url": "https://example.com/video.mp4",
      "success": true,
      "resolved_url": "https://example.com/video.mp4"
    }
  ],
  "total": 3,
  "successful": 3
}
```

### Resolver Management

#### GET `/api/resolvers`
List all available resolver plugins.

**Query Parameters:**
- `enabled_only` - Only return enabled resolvers (default: false)

**Response:**
```json
{
  "resolvers": [
    {
      "name": "YouTube",
      "domains": ["youtube.com", "youtu.be", "youtube-nocookie.com"],
      "pattern": "...",
      "priority": 10,
      "universal": false,
      "popup": false,
      "enabled": true
    },
    {
      "name": "StreamTape",
      "domains": ["streamtape.com", "strtape.cloud", "..."],
      "pattern": "...",
      "priority": 100,
      "universal": false,
      "popup": false,
      "enabled": true
    }
  ],
  "count": 257,
  "total_available": 257,
  "enabled_only": false
}
```

#### GET `/api/resolvers/search?domain=DOMAIN`
Search for resolvers that handle a specific domain.

**Example:** `/api/resolvers/search?domain=youtube.com`

**Response:**
```json
{
  "domain": "youtube.com",
  "resolvers": [
    {
      "name": "YouTube",
      "domains": ["youtube.com", "youtu.be", "youtube-nocookie.com"],
      "pattern": "...",
      "priority": 10,
      "universal": false,
      "popup": false,
      "enabled": true
    }
  ],
  "count": 1
}
```

### System Information

#### GET `/health`
System health and status information.

**Response:**
```json
{
  "status": "healthy",
  "service": "ResolveURL API - Complete Edition",
  "version": "2.0.0",
  "resolvers": 257,
  "compatibility_layer": true
}
```

## Supported Resolver Plugins

The complete implementation includes all resolver plugins from the original ResolveURL project:

### Popular Video Hosts
- **YouTube** - YouTube.com, youtu.be links
- **Streamtape** - StreamTape and all mirror domains
- **MixDrop** - MixDrop and mirror domains
- **StreamWish** - StreamWish hosting
- **Vidoza** - Vidoza video hosting
- **Doodstream** - DoodStream hosting
- **FileMoon** - FileMoon hosting
- **And 250+ more...**

### Universal Resolvers
- **Debrid Services** - RealDebrid, AllDebrid, Premiumize
- **Direct Links** - Direct video file URLs
- **Generic Embeds** - Common embed patterns

### Specialized Platforms
- **Social Media** - Facebook, VK, Dailymotion
- **File Hosts** - Various file hosting services
- **Streaming Sites** - Video streaming platforms

## Architecture

### Compatibility Layer (`standalone_compatibility.py`)
Provides comprehensive mocking of Kodi/XBMC dependencies:

- **Mock Kodi Module** - Settings, paths, translations
- **Mock XBMC APIs** - Logging, VFS, GUI components  
- **Mock Network Layer** - HTTP client with requests backend
- **Mock Cache System** - Function caching for performance
- **Mock Helper Functions** - Utilities and common functions

### Complete Server (`complete_server.py`)
Main server implementation with full resolver integration:

- **Dynamic Plugin Loading** - Automatically discovers all resolver plugins
- **Resolver Management** - Priority-based resolver selection
- **Error Handling** - Comprehensive error handling and fallbacks
- **Web Interface** - Interactive HTML interface for testing
- **API Endpoints** - RESTful API for programmatic access

### Resolution Process
1. **URL Analysis** - Parse URL and extract domain/path components
2. **Resolver Discovery** - Find all resolvers that can handle the URL
3. **Priority Sorting** - Order resolvers by priority (lower = higher priority)
4. **Resolution Attempts** - Try each resolver until successful
5. **Fallback Methods** - Use multiple resolution strategies
6. **Result Validation** - Verify resolved URLs when possible

## Deployment Options

### Development
```bash
# Quick start for testing
python3 complete_server.py

# With custom settings
python3 complete_server.py --host 0.0.0.0 --port 8080 --debug
```

### Production with Docker
```bash
# Start services
docker-compose up -d

# Scale for load balancing
docker-compose up -d --scale resolveurl-api=3

# Enable nginx proxy
docker-compose --profile production up -d
```

### Production Native
```bash
# Install in virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start with production settings
python3 complete_server.py --host 0.0.0.0 --port 5000

# Or use process manager
gunicorn --bind 0.0.0.0:5000 --workers 4 complete_server:app
```

## Configuration

### Environment Variables
- `FLASK_ENV` - Flask environment (development/production)
- `PYTHONPATH` - Python path for imports
- `LOG_LEVEL` - Logging level (DEBUG/INFO/WARNING/ERROR)

### Server Settings
Settings are managed through the ResolveURL configuration system:

- `allow_universal` - Enable universal resolvers (default: true)
- `allow_popups` - Enable popup-based resolvers (default: true)  
- `auto_pick` - Auto-select single source (default: true)
- `use_cache` - Enable function caching (default: true)

## Monitoring

### Health Checks
The `/health` endpoint provides system status information and can be used for monitoring:

```bash
# Check server health
curl http://localhost:5000/health

# Use in monitoring systems
curl -f http://localhost:5000/health || exit 1
```

### Logging
Comprehensive logging is available at multiple levels:

- **DEBUG** - Detailed resolver operations and HTTP requests
- **INFO** - General operation information and successful resolutions
- **WARNING** - Failed resolution attempts and compatibility issues
- **ERROR** - System errors and exceptions

### Docker Health Checks
Docker containers include built-in health checks:

```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# View health check logs
docker inspect --format='{{json .State.Health}}' <container_id>
```

## Integration Examples

### Python Client
```python
import requests

# Resolve a single URL
response = requests.post('http://localhost:5000/api/resolve', 
                        json={'url': 'https://youtube.com/watch?v=VIDEO_ID'})
result = response.json()
print(f"Resolved: {result['resolved_url']}")

# Get available resolvers
response = requests.get('http://localhost:5000/api/resolvers?enabled_only=true')
resolvers = response.json()
print(f"Found {resolvers['count']} enabled resolvers")
```

### JavaScript/Node.js
```javascript
// Resolve multiple URLs
const response = await fetch('http://localhost:5000/api/resolve/multiple', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    urls: [
      'https://youtube.com/watch?v=VIDEO_ID',
      'https://streamtape.com/e/VIDEO_ID'
    ]
  })
});

const result = await response.json();
console.log(`Resolved ${result.successful}/${result.total} URLs`);
```

### cURL Commands
```bash
# Resolve URL
curl -X POST http://localhost:5000/api/resolve \
  -H "Content-Type: application/json" \
  -d '{"url":"https://youtube.com/watch?v=dQw4w9WgXcQ"}'

# Search resolvers
curl "http://localhost:5000/api/resolvers/search?domain=youtube.com"

# Health check
curl http://localhost:5000/health
```

## Troubleshooting

### Common Issues

#### Resolver Not Found
If a URL isn't being resolved:
1. Check if a resolver exists for the domain: `/api/resolvers/search?domain=DOMAIN`
2. Verify the resolver is enabled in the response
3. Check server logs for specific error messages

#### Import Errors
If you see import errors on startup:
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check that you're in the correct directory
3. Verify Python path includes the resolveurl library

#### Network Timeouts
For network-related issues:
1. Check firewall settings for outbound connections
2. Verify DNS resolution is working
3. Increase timeout settings if needed

### Debug Mode
Enable debug mode for detailed logging:

```bash
# Native Python
python3 complete_server.py --debug

# Docker
docker-compose logs -f resolveurl-api
```

### Log Analysis
Key log patterns to look for:

- `"Resolving URL with ResolveURL: <url>"` - Resolution attempts
- `"Successfully resolved: <url> -> <result>"` - Successful resolutions  
- `"ResolveURL could not resolve: <url>"` - Failed resolutions
- `"Found X resolver plugins"` - Plugin loading status

## Performance

### Optimization Tips
1. **Use caching** - Enable function caching for better performance
2. **Connection pooling** - The underlying requests session reuses connections
3. **Batch requests** - Use `/api/resolve/multiple` for multiple URLs
4. **Disable debug logs** - Reduce logging overhead in production

### Scaling
For high-load deployments:

1. **Multiple workers** - Use gunicorn with multiple worker processes
2. **Load balancing** - Deploy multiple instances behind a load balancer
3. **Caching layer** - Add Redis or Memcached for resolved URL caching
4. **Database** - Store resolution results for repeat requests

## Security Considerations

### Network Security
- Run behind a reverse proxy (nginx) for production
- Use HTTPS in production environments
- Implement rate limiting for API endpoints
- Monitor for abuse patterns

### Container Security  
- Runs as non-root user in Docker
- Minimal base image (python:3.11-slim)
- No unnecessary capabilities or privileged access
- Regular dependency updates

### Input Validation
- URL validation and sanitization
- Request size limits
- Timeout protections for external requests
- Error message sanitization

This complete implementation provides a robust, scalable, and feature-complete solution for URL resolution without Kodi dependencies.