"""
Simple ResolveURL REST API
A minimal web server that provides URL resolution functionality
"""
import os
import sys
import json
import logging
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import traceback
import tempfile

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Mock the modules that would normally come from Kodi
class MockCommon:
    def __init__(self):
        self.logger = logger
        self.addon_version = "6.0.0"
        self._settings = {
            'allow_universal': 'true',
            'allow_popups': 'true',
            'auto_pick': 'true',
            'use_cache': 'true'
        }
    
    def get_setting(self, key):
        return self._settings.get(key, '')
    
    def set_setting(self, key, value):
        self._settings[key] = str(value)
    
    def log_debug(self, msg):
        logger.debug(msg)
    
    def log_warning(self, msg):
        logger.warning(msg)

# Create global mock common
common = MockCommon()

# HTML template for simple web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ResolveURL API</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #333; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="url"], textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        .result { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; background-color: #f9f9f9; }
        .error { background-color: #f8d7da; border-color: #f5c6cb; color: #721c24; }
        .success { background-color: #d4edda; border-color: #c3e6cb; color: #155724; }
        pre { white-space: pre-wrap; }
        .info { background-color: #d1ecf1; border-color: #bee5eb; color: #0c5460; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ResolveURL API</h1>
        <p>This is a standalone ResolveURL web service that works without Kodi.</p>
        
        <div class="result info">
            <h3>Available Endpoints:</h3>
            <ul>
                <li><strong>GET /</strong> - This web interface</li>
                <li><strong>GET /health</strong> - Health check</li>
                <li><strong>POST /api/resolve</strong> - Resolve a URL to direct media link</li>
                <li><strong>GET /api/resolvers</strong> - List available resolvers</li>
                <li><strong>POST /api/resolve/multiple</strong> - Resolve multiple URLs</li>
            </ul>
        </div>
        
        <div class="form-group">
            <label for="url">URL to resolve (for testing when available):</label>
            <input type="url" id="url" placeholder="https://example.com/video/12345">
        </div>
        
        <div class="form-group">
            <button onclick="resolveUrl()">Resolve URL</button>
            <button onclick="getResolvers()">List Resolvers</button>
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
                resultDiv.className = response.ok ? 'result success' : 'result error';
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
        'service': 'ResolveURL API',
        'version': '1.0.0',
        'note': 'This is a minimal implementation. Full resolver functionality requires Kodi dependencies.'
    })

@app.route('/api/resolve', methods=['POST'])
def resolve_url():
    """
    Resolve a URL to a direct media link
    
    JSON body:
    {
        "url": "https://example.com/video/12345",
        "return_all": false,
        "subs": false
    }
    """
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({
                'error': 'Missing required field: url'
            }), 400
        
        url = data['url']
        return_all = data.get('return_all', False)
        subs = data.get('subs', False)
        
        logger.info(f"Resolving URL: {url}")
        
        # For now, this is a placeholder
        # In a full implementation, this would use the ResolveURL library
        return jsonify({
            'success': False,
            'original_url': url,
            'error': 'Resolver not fully implemented',
            'message': 'This is a minimal standalone implementation. Full resolver functionality requires proper Kodi dependency handling.',
            'note': 'To fully implement this, the ResolveURL library needs to be refactored to work without Kodi dependencies.'
        }), 501
        
    except Exception as e:
        logger.error(f"Error resolving URL: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/resolvers', methods=['GET'])
def get_resolvers():
    """
    Get list of available resolvers
    """
    try:
        # This would normally return the actual resolvers
        # For now, return a sample list to show the API structure
        sample_resolvers = [
            {
                'name': 'youtube',
                'domains': ['youtube.com', 'youtu.be'],
                'priority': 10,
                'universal': False,
                'popup': False,
                'enabled': True,
                'note': 'Sample resolver - not functional'
            },
            {
                'name': 'generic',
                'domains': ['*'],
                'priority': 100,
                'universal': True,
                'popup': False,
                'enabled': True,
                'note': 'Sample resolver - not functional'
            }
        ]
        
        return jsonify({
            'resolvers': sample_resolvers,
            'count': len(sample_resolvers),
            'note': 'These are sample resolvers for API demonstration. Real resolvers require Kodi dependencies.',
            'message': 'To get actual resolvers, the ResolveURL library needs to be refactored for standalone operation.'
        })
        
    except Exception as e:
        logger.error(f"Error getting resolvers: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/resolve/multiple', methods=['POST'])
def resolve_multiple():
    """
    Resolve multiple URLs at once
    """
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
        
        # For now, return placeholder results
        results = []
        for url in urls:
            results.append({
                'original_url': url,
                'success': False,
                'error': 'Resolver not implemented',
                'note': 'This is a placeholder response'
            })
        
        return jsonify({
            'results': results,
            'total': len(urls),
            'successful': 0,
            'note': 'This is a placeholder implementation'
        })
        
    except Exception as e:
        logger.error(f"Error resolving multiple URLs: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='ResolveURL REST API Server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print(f"Starting ResolveURL API server on {args.host}:{args.port}")
    print(f"Web interface: http://{args.host}:{args.port}")
    print(f"Health check: http://{args.host}:{args.port}/health")
    print("")
    print("NOTE: This is a minimal implementation that demonstrates the API structure.")
    print("Full URL resolution functionality requires refactoring the ResolveURL library")
    print("to work without Kodi dependencies.")
    
    app.run(host=args.host, port=args.port, debug=args.debug)