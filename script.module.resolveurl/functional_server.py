"""
Functional ResolveURL REST API
A working implementation that provides actual URL resolution functionality
"""
import os
import sys
import json
import logging
import re
import requests
from urllib.parse import urlparse, parse_qs
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import traceback

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

class ResolverError(Exception):
    pass

class SimpleNet:
    """Simple HTTP client for making web requests"""
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
        })
    
    def http_GET(self, url, headers=None):
        """Make GET request"""
        try:
            response = self.session.get(url, headers=headers or {}, timeout=10)
            response.raise_for_status()
            return response
        except Exception as e:
            logger.error(f"HTTP GET error for {url}: {e}")
            raise ResolverError(f"HTTP request failed: {e}")

class BaseResolver:
    """Base class for URL resolvers"""
    name = 'base'
    domains = []
    pattern = None
    priority = 100
    
    def __init__(self):
        self.net = SimpleNet()
    
    def valid_url(self, url, host=None):
        """Check if this resolver can handle the URL"""
        if not url:
            return False
        
        if self.pattern:
            return re.search(self.pattern, url, re.I) is not None
        
        if host and self.domains:
            return any(domain in host.lower() for domain in self.domains)
        
        return False
    
    def get_host_and_id(self, url):
        """Extract host and media ID from URL"""
        if self.pattern:
            match = re.search(self.pattern, url, re.I)
            if match:
                return match.groups()
        return None, None
    
    def resolve(self, url):
        """Resolve URL to direct media link"""
        host, media_id = self.get_host_and_id(url)
        if host and media_id:
            return self.get_media_url(host, media_id)
        return None
    
    def get_media_url(self, host, media_id):
        """Override this method in subclasses"""
        raise NotImplementedError
    
    def get_url(self, host, media_id):
        """Build URL from host and media_id"""
        return f"http://{host}/embed-{media_id}.html"

class DirectLinkResolver(BaseResolver):
    """Resolver for direct video links"""
    name = 'DirectLink'
    domains = ['*']
    priority = 200
    
    def valid_url(self, url, host=None):
        """Check if URL is a direct video link"""
        if not url:
            return False
        
        # Check for common video file extensions
        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']
        url_lower = url.lower()
        
        # Check if URL ends with video extension
        if any(url_lower.endswith(ext) for ext in video_extensions):
            return True
        
        # Check if URL contains video extension in query params
        if any(ext in url_lower for ext in video_extensions):
            return True
        
        return False
    
    def resolve(self, url):
        """For direct links, just return the URL after basic validation"""
        try:
            # Try to make a HEAD request to verify the URL exists
            response = self.net.session.head(url, timeout=5)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'video' in content_type or any(ext in url.lower() for ext in ['.mp4', '.avi', '.mkv', '.mov']):
                    return url
        except:
            pass
        
        return None
    
    def get_media_url(self, host, media_id):
        return f"http://{host}/{media_id}"

class GenericEmbedResolver(BaseResolver):
    """Generic resolver for common embed patterns"""
    name = 'GenericEmbed'
    domains = ['*']
    priority = 150
    
    def valid_url(self, url, host=None):
        """Check if URL looks like a generic embed"""
        if not url:
            return False
        
        # Look for common embed patterns
        embed_patterns = [
            r'/embed/',
            r'/watch\?v=',
            r'/video/',
            r'/stream/',
            r'/play/'
        ]
        
        return any(re.search(pattern, url, re.I) for pattern in embed_patterns)
    
    def resolve(self, url):
        """Try to extract video URL from page source"""
        try:
            response = self.net.http_GET(url)
            content = response.text
            
            # Look for common video URL patterns in the page
            video_patterns = [
                r'"(https?://[^"]+\.mp4[^"]*)"',
                r"'(https?://[^']+\.mp4[^']*)'",
                r'src="(https?://[^"]+\.mp4[^"]*)"',
                r"src='(https?://[^']+\.mp4[^']*)'",
                r'"file":\s*"([^"]+\.mp4[^"]*)"',
                r'"url":\s*"([^"]+\.mp4[^"]*)"',
                r'"src":\s*"([^"]+\.mp4[^"]*)"',
            ]
            
            for pattern in video_patterns:
                matches = re.findall(pattern, content, re.I)
                if matches:
                    # Return the first match that looks like a valid URL
                    for match in matches:
                        if match.startswith('http'):
                            return match
        
        except Exception as e:
            logger.debug(f"Generic resolver failed for {url}: {e}")
        
        return None
    
    def get_media_url(self, host, media_id):
        return None

class YouTubeResolver(BaseResolver):
    """Simple YouTube resolver (limited functionality)"""
    name = 'YouTube'
    domains = ['youtube.com', 'youtu.be']
    pattern = r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)'
    priority = 10
    
    def get_media_url(self, host, media_id):
        """Note: This is a placeholder - actual YouTube resolution requires more complex handling"""
        # In a real implementation, you'd need to handle YouTube's complex URL extraction
        # For now, return a placeholder to show the structure works
        return None

# Registry of available resolvers
RESOLVERS = [
    DirectLinkResolver(),
    GenericEmbedResolver(), 
    YouTubeResolver(),
]

def find_resolver(url):
    """Find the best resolver for a URL"""
    host = urlparse(url).netloc.lower() if url else None
    
    # Sort resolvers by priority (lower number = higher priority)
    sorted_resolvers = sorted(RESOLVERS, key=lambda x: x.priority)
    
    for resolver in sorted_resolvers:
        if resolver.valid_url(url, host):
            return resolver
    
    return None

def resolve_url(url):
    """Resolve a URL to a direct media link"""
    resolver = find_resolver(url)
    if resolver:
        logger.info(f"Using resolver: {resolver.name} for URL: {url}")
        try:
            result = resolver.resolve(url)
            if result:
                return result
        except Exception as e:
            logger.error(f"Resolver {resolver.name} failed: {e}")
    
    return None

# HTML template for web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ResolveURL API - Working Version</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #333; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="url"], textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        button:hover { background-color: #0056b3; }
        .result { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; background-color: #f9f9f9; }
        .error { background-color: #f8d7da; border-color: #f5c6cb; color: #721c24; }
        .success { background-color: #d4edda; border-color: #c3e6cb; color: #155724; }
        .info { background-color: #d1ecf1; border-color: #bee5eb; color: #0c5460; }
        pre { white-space: pre-wrap; word-wrap: break-word; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ResolveURL API - Working Version</h1>
        <p>This version provides actual URL resolution functionality for supported sites.</p>
        
        <div class="result info">
            <h3>Supported URL Types:</h3>
            <ul>
                <li><strong>Direct Video Links</strong> - URLs ending in .mp4, .avi, .mkv, etc.</li>
                <li><strong>Generic Embeds</strong> - Common video embed pages</li>
                <li><strong>YouTube</strong> - Basic pattern recognition (limited functionality)</li>
            </ul>
            <p><strong>Note:</strong> This is a demonstration implementation. Full resolver functionality would require implementing the specific logic for each video hosting site.</p>
        </div>
        
        <div class="form-group">
            <label for="url">URL to resolve:</label>
            <input type="url" id="url" placeholder="https://example.com/video.mp4" required>
        </div>
        
        <div class="form-group">
            <button onclick="resolveUrl()">Resolve URL</button>
            <button onclick="getResolvers()">List Resolvers</button>
            <button onclick="testUrls()">Test Sample URLs</button>
        </div>
        
        <div id="result" class="result" style="display: none;">
            <h3>Result:</h3>
            <pre id="result-content"></pre>
        </div>
    </div>

    <script>
        async function resolveUrl() {
            const url = document.getElementById('url').value;
            if (!url) {
                alert('Please enter a URL');
                return;
            }
            
            const resultDiv = document.getElementById('result');
            const resultContent = document.getElementById('result-content');
            
            try {
                const response = await fetch('/api/resolve', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: url })
                });
                
                const data = await response.json();
                resultDiv.className = response.ok && data.success ? 'result success' : 'result error';
                resultContent.textContent = JSON.stringify(data, null, 2);
                resultDiv.style.display = 'block';
            } catch (error) {
                resultDiv.className = 'result error';
                resultContent.textContent = 'Error: ' + error.message;
                resultDiv.style.display = 'block';
            }
        }
        
        async function getResolvers() {
            const resultDiv = document.getElementById('result');
            const resultContent = document.getElementById('result-content');
            
            try {
                const response = await fetch('/api/resolvers');
                const data = await response.json();
                resultDiv.className = 'result success';
                resultContent.textContent = JSON.stringify(data, null, 2);
                resultDiv.style.display = 'block';
            } catch (error) {
                resultDiv.className = 'result error';
                resultContent.textContent = 'Error: ' + error.message;
                resultDiv.style.display = 'block';
            }
        }
        
        async function testUrls() {
            const testUrls = [
                'https://example.com/video.mp4',
                'https://youtu.be/dQw4w9WgXcQ',
                'https://youtube.com/watch?v=dQw4w9WgXcQ'
            ];
            
            const resultDiv = document.getElementById('result');
            const resultContent = document.getElementById('result-content');
            
            try {
                const response = await fetch('/api/resolve/multiple', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ urls: testUrls })
                });
                
                const data = await response.json();
                resultDiv.className = 'result info';
                resultContent.textContent = JSON.stringify(data, null, 2);
                resultDiv.style.display = 'block';
            } catch (error) {
                resultDiv.className = 'result error';
                resultContent.textContent = 'Error: ' + error.message;
                resultDiv.style.display = 'block';
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'ResolveURL API - Working Version',
        'version': '1.1.0',
        'resolvers': len(RESOLVERS)
    })

@app.route('/api/resolve', methods=['POST'])
def api_resolve_url():
    """Resolve a URL to a direct media link"""
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'error': 'Missing required field: url'
            }), 400
        
        url = data['url']
        logger.info(f"Resolving URL: {url}")
        
        result = resolve_url(url)
        
        if result:
            return jsonify({
                'success': True,
                'original_url': url,
                'resolved_url': result,
                'message': 'URL resolved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'original_url': url,
                'error': 'Could not resolve URL',
                'message': 'No suitable resolver found or resolution failed'
            }), 404
            
    except Exception as e:
        logger.error(f"Error resolving URL: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/resolvers', methods=['GET'])
def api_get_resolvers():
    """Get list of available resolvers"""
    try:
        resolver_list = []
        for resolver in RESOLVERS:
            resolver_info = {
                'name': resolver.name,
                'domains': resolver.domains,
                'priority': resolver.priority,
                'pattern': resolver.pattern
            }
            resolver_list.append(resolver_info)
        
        return jsonify({
            'resolvers': resolver_list,
            'count': len(resolver_list)
        })
        
    except Exception as e:
        logger.error(f"Error getting resolvers: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/resolve/multiple', methods=['POST'])
def api_resolve_multiple():
    """Resolve multiple URLs at once"""
    try:
        data = request.get_json()
        if not data or 'urls' not in data:
            return jsonify({
                'error': 'Missing required field: urls'
            }), 400
        
        urls = data['urls']
        if not isinstance(urls, list):
            return jsonify({
                'error': 'urls must be a list'
            }), 400
        
        results = []
        for url in urls:
            try:
                result = resolve_url(url)
                results.append({
                    'original_url': url,
                    'success': bool(result),
                    'resolved_url': result if result else None
                })
            except Exception as e:
                results.append({
                    'original_url': url,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'results': results,
            'total': len(urls),
            'successful': sum(1 for r in results if r['success'])
        })
        
    except Exception as e:
        logger.error(f"Error resolving multiple URLs: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='ResolveURL REST API Server - Working Version')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print(f"Starting ResolveURL API server on {args.host}:{args.port}")
    print(f"Web interface: http://{args.host}:{args.port}")
    print(f"Health check: http://{args.host}:{args.port}/health")
    print("")
    print("This version provides working URL resolution for supported formats:")
    print("- Direct video links (.mp4, .avi, .mkv, etc.)")
    print("- Generic embed pages")
    print("- Basic pattern recognition for popular sites")
    
    app.run(host=args.host, port=args.port, debug=args.debug)