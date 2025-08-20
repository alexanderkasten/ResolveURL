"""
REST API Web Server for ResolveURL
Provides HTTP endpoints for URL resolution without requiring Kodi
"""
import os
import sys
import json
import logging
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import traceback

# Add the resolveurl lib path
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# Apply monkey patches for Kodi dependencies BEFORE any other imports
import resolveurl.monkey_patches

# Now import resolveurl functionality
try:
    import resolveurl.standalone_resolveurl as resolveurl
    print("Successfully imported standalone resolveurl")
except Exception as e:
    print(f"Error importing resolveurl: {e}")
    traceback.print_exc()
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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
    </style>
</head>
<body>
    <div class="container">
        <h1>ResolveURL API</h1>
        <p>Enter a URL to resolve it to a direct media link:</p>
        
        <div class="form-group">
            <label for="url">URL to resolve:</label>
            <input type="url" id="url" placeholder="https://example.com/video/12345" required>
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
        'version': '1.0.0'
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
        
        # Resolve the URL
        result = resolveurl.resolve(url, return_all=return_all, subs=subs)
        
        if result:
            return jsonify({
                'success': True,
                'original_url': url,
                'resolved_url': result,
                'return_all': return_all,
                'subs': subs
            })
        else:
            return jsonify({
                'success': False,
                'original_url': url,
                'error': 'Could not resolve URL',
                'message': 'No suitable resolver found for this URL'
            }), 404
            
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
    
    Query parameters:
    - domain: Filter by domain
    - include_universal: Include universal resolvers (default: true)
    - include_popups: Include popup resolvers (default: true) 
    - include_disabled: Include disabled resolvers (default: false)
    """
    try:
        domain = request.args.get('domain')
        include_universal = request.args.get('include_universal', 'true').lower() == 'true'
        include_popups = request.args.get('include_popups', 'true').lower() == 'true'
        include_disabled = request.args.get('include_disabled', 'false').lower() == 'true'
        
        resolvers = resolveurl.relevant_resolvers(
            domain=domain,
            include_universal=include_universal,
            include_popups=include_popups,
            include_disabled=include_disabled,
            order_matters=True
        )
        
        resolver_list = []
        for resolver in resolvers:
            resolver_info = {
                'name': resolver.name,
                'domains': resolver.domains,
                'priority': getattr(resolver, 'priority', 100),
                'universal': resolver.isUniversal(),
                'popup': resolver.isPopup(),
                'enabled': resolver._is_enabled()
            }
            resolver_list.append(resolver_info)
        
        return jsonify({
            'resolvers': resolver_list,
            'count': len(resolver_list),
            'filters': {
                'domain': domain,
                'include_universal': include_universal,
                'include_popups': include_popups,
                'include_disabled': include_disabled
            }
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
    
    JSON body:
    {
        "urls": ["url1", "url2", "url3"],
        "return_all": false,
        "subs": false
    }
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
        
        return_all = data.get('return_all', False)
        subs = data.get('subs', False)
        
        results = []
        for url in urls:
            try:
                result = resolveurl.resolve(url, return_all=return_all, subs=subs)
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

@app.route('/api/scrape', methods=['POST'])
def scrape_supported():
    """
    Scrape HTML for supported URLs
    
    JSON body:
    {
        "html": "<html content>",
        "regex": "optional custom regex",
        "host_only": false
    }
    """
    try:
        data = request.get_json()
        if not data or 'html' not in data:
            return jsonify({
                'error': 'Missing required field: html'
            }), 400
        
        html = data['html']
        regex = data.get('regex')
        host_only = data.get('host_only', False)
        
        supported_urls = resolveurl.scrape_supported(html, regex=regex, host_only=host_only)
        
        return jsonify({
            'supported_urls': supported_urls,
            'count': len(supported_urls)
        })
        
    except Exception as e:
        logger.error(f"Error scraping HTML: {e}")
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
    print(f"API docs: http://{args.host}:{args.port}/health")
    
    app.run(host=args.host, port=args.port, debug=args.debug)