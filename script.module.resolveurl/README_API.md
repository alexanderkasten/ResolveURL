# ResolveURL REST API Documentation

## Overview

This project provides a standalone REST API web server for URL resolution functionality that works completely without Kodi. The server can resolve URLs from various hosting sites to direct media links.

## Features

- **Standalone Operation**: Works without any Kodi dependencies
- **REST API**: HTTP endpoints for URL resolution
- **Web Interface**: Simple HTML interface for testing
- **Multiple Resolvers**: Support for different types of video URLs
- **Extensible**: Easy to add new resolvers

## Installation

1. Navigate to the script.module.resolveurl directory:
```bash
cd script.module.resolveurl
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Start the server:
```bash
python3 functional_server.py
```

Or with custom host/port:
```bash
python3 functional_server.py --host 0.0.0.0 --port 8080
```

## API Endpoints

### Health Check
**GET** `/health`

Returns server status and basic information.

**Response:**
```json
{
    "status": "healthy",
    "service": "ResolveURL API - Working Version",
    "version": "1.1.0",
    "resolvers": 3
}
```

### Resolve Single URL
**POST** `/api/resolve`

Resolve a single URL to a direct media link.

**Request Body:**
```json
{
    "url": "https://example.com/video.mp4"
}
```

**Response (Success):**
```json
{
    "success": true,
    "original_url": "https://example.com/video.mp4",
    "resolved_url": "https://cdn.example.com/direct/video.mp4",
    "message": "URL resolved successfully"
}
```

**Response (Failure):**
```json
{
    "success": false,
    "original_url": "https://example.com/video.mp4",
    "error": "Could not resolve URL",
    "message": "No suitable resolver found or resolution failed"
}
```

### List Available Resolvers
**GET** `/api/resolvers`

Get a list of all available URL resolvers.

**Response:**
```json
{
    "count": 3,
    "resolvers": [
        {
            "name": "DirectLink",
            "domains": ["*"],
            "pattern": null,
            "priority": 200
        },
        {
            "name": "GenericEmbed",
            "domains": ["*"],
            "pattern": null,
            "priority": 150
        },
        {
            "name": "YouTube",
            "domains": ["youtube.com", "youtu.be"],
            "pattern": "(?:youtube\\.com/watch\\?v=|youtu\\.be/)([a-zA-Z0-9_-]+)",
            "priority": 10
        }
    ]
}
```

### Resolve Multiple URLs
**POST** `/api/resolve/multiple`

Resolve multiple URLs in a single request.

**Request Body:**
```json
{
    "urls": [
        "https://example.com/video1.mp4",
        "https://example.com/video2.mp4",
        "https://youtu.be/dQw4w9WgXcQ"
    ]
}
```

**Response:**
```json
{
    "results": [
        {
            "original_url": "https://example.com/video1.mp4",
            "success": true,
            "resolved_url": "https://cdn.example.com/direct/video1.mp4"
        },
        {
            "original_url": "https://example.com/video2.mp4",
            "success": false,
            "error": "Resolution failed"
        },
        {
            "original_url": "https://youtu.be/dQw4w9WgXcQ",
            "success": false,
            "resolved_url": null
        }
    ],
    "total": 3,
    "successful": 1
}
```

## Web Interface

Access the web interface at `http://localhost:5000` (or your configured host/port).

The interface provides:
- URL input field for testing resolution
- Buttons to list resolvers and test sample URLs
- Real-time results display

## Current Resolvers

The system includes several built-in resolvers:

### 1. DirectLink Resolver
- **Purpose**: Handles direct video file links
- **Supported**: URLs ending in .mp4, .avi, .mkv, .mov, .wmv, .flv, .webm, .m4v
- **Priority**: 200 (lowest priority)

### 2. GenericEmbed Resolver
- **Purpose**: Extracts video URLs from generic embed pages
- **Supported**: Pages containing common embed patterns
- **Priority**: 150

### 3. YouTube Resolver
- **Purpose**: Basic YouTube URL pattern recognition
- **Supported**: youtube.com/watch?v= and youtu.be/ URLs
- **Priority**: 10 (highest priority)
- **Note**: Currently only does pattern recognition, actual resolution requires YouTube-specific implementation

## Adding New Resolvers

To add a new resolver, create a class that inherits from `BaseResolver`:

```python
class MyResolver(BaseResolver):
    name = 'MyResolver'
    domains = ['mysite.com']
    pattern = r'mysite\.com/video/([a-zA-Z0-9]+)'
    priority = 50
    
    def get_media_url(self, host, media_id):
        # Implement resolution logic here
        # Return direct video URL or None
        pass
```

Then add it to the `RESOLVERS` list in `functional_server.py`.

## Architecture

The system is designed with minimal dependencies and maximum portability:

1. **No Kodi Dependencies**: Completely standalone Python application
2. **Simple Architecture**: Flask web server with pluggable resolvers
3. **Extensible Design**: Easy to add new resolvers and endpoints
4. **Error Handling**: Proper HTTP status codes and error messages

## Files Structure

```
script.module.resolveurl/
├── functional_server.py          # Main working server
├── simple_server.py             # Basic demo server
├── requirements.txt              # Python dependencies
├── lib/resolveurl/              # Original ResolveURL library
├── web_server.py                # Advanced server (requires more work)
└── README_API.md                # This documentation
```

## Limitations

This is a demonstration implementation with the following limitations:

1. **Limited Resolvers**: Only includes basic resolver types
2. **No Captcha Handling**: Complex sites with captchas not supported
3. **No Authentication**: Sites requiring login not supported
4. **Basic Error Handling**: Production deployment would need more robust error handling

## Future Enhancements

To make this production-ready, consider:

1. **More Resolvers**: Implement specific resolvers for popular hosting sites
2. **Caching**: Add response caching for better performance
3. **Rate Limiting**: Prevent abuse of the API
4. **Authentication**: Add API key authentication
5. **Monitoring**: Add metrics and logging
6. **Configuration**: External configuration file support
7. **Database**: Persistent storage for settings and cache

## Usage Examples

### Command Line (curl)

```bash
# Health check
curl http://localhost:5000/health

# Resolve a URL
curl -X POST -H "Content-Type: application/json" \
     -d '{"url":"https://example.com/video.mp4"}' \
     http://localhost:5000/api/resolve

# List resolvers
curl http://localhost:5000/api/resolvers

# Resolve multiple URLs
curl -X POST -H "Content-Type: application/json" \
     -d '{"urls":["url1","url2","url3"]}' \
     http://localhost:5000/api/resolve/multiple
```

### Python Client

```python
import requests

# Resolve a URL
response = requests.post('http://localhost:5000/api/resolve', 
                        json={'url': 'https://example.com/video.mp4'})
result = response.json()

if result['success']:
    print(f"Resolved: {result['resolved_url']}")
else:
    print(f"Failed: {result['message']}")
```

### JavaScript Client

```javascript
// Resolve a URL
fetch('/api/resolve', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        url: 'https://example.com/video.mp4'
    })
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        console.log('Resolved:', data.resolved_url);
    } else {
        console.log('Failed:', data.message);
    }
});
```