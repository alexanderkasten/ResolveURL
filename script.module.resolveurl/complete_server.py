"""
Complete ResolveURL REST API Server
Integrates all existing resolver plugins with standalone compatibility layer
"""
import os
import sys
import json
import logging
import traceback
from urllib.parse import urlparse
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize compatibility layer FIRST
try:
    import standalone_compatibility
    logger.info("Compatibility layer loaded successfully")
except ImportError as e:
    logger.error(f"Failed to load compatibility layer: {e}")
    sys.exit(1)

# Now we can import resolveurl modules
try:
    # Import the main resolveurl functionality
    import resolveurl
    from resolveurl import common
    from resolveurl.resolver import ResolveUrl, ResolverError
    from resolveurl.hmf import HostedMediaFile
    logger.info("ResolveURL modules loaded successfully")
except ImportError as e:
    logger.error(f"Failed to load ResolveURL modules: {e}")
    traceback.print_exc()
    sys.exit(1)

# Create Flask app
app = Flask(__name__)
CORS(app)

class CompatibilityError(Exception):
    """Error in compatibility layer"""
    pass

def get_all_resolvers():
    """Get all available resolver plugins"""
    try:
        # Get all resolver classes
        resolvers = resolveurl.relevant_resolvers(
            include_universal=True, 
            include_disabled=True,
            include_popups=True
        )
        
        logger.info(f"Found {len(resolvers)} resolver plugins")
        return resolvers
    except Exception as e:
        logger.error(f"Error getting resolvers: {e}")
        return []

def format_resolver_info(resolver_class):
    """Format resolver information for API response"""
    try:
        return {
            'name': getattr(resolver_class, 'name', resolver_class.__name__),
            'domains': getattr(resolver_class, 'domains', []),
            'pattern': getattr(resolver_class, 'pattern', None),
            'priority': getattr(resolver_class, 'priority', getattr(resolver_class, '_get_priority', lambda: 100)()),
            'universal': getattr(resolver_class, 'isUniversal', lambda: False)(),
            'popup': getattr(resolver_class, 'isPopup', lambda: False)(),
            'enabled': getattr(resolver_class, '_is_enabled', lambda: True)()
        }
    except Exception as e:
        logger.error(f"Error formatting resolver {resolver_class}: {e}")
        return {
            'name': str(resolver_class),
            'error': str(e)
        }

def resolve_url_with_resolveurl(url):
    """Use the full ResolveURL system to resolve a URL"""
    try:
        logger.info(f"Resolving URL with ResolveURL: {url}")
        
        # Use the main resolveurl.resolve function
        result = resolveurl.resolve(url)
        
        if result and result != False:
            logger.info(f"Successfully resolved: {url} -> {result}")
            return result
        else:
            logger.info(f"ResolveURL could not resolve: {url}")
            return None
            
    except Exception as e:
        logger.error(f"Error resolving {url}: {e}")
        logger.debug(traceback.format_exc())
        return None

def resolve_with_manual_resolver_search(url):
    """Manually search through resolvers using domain matching"""
    try:
        logger.info(f"Manual resolver search for: {url}")
        
        # Extract domain from URL for efficient resolver matching
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower() if parsed_url.netloc else ''
        
        # Get only relevant resolvers for this domain using ResolveURL's built-in logic
        try:
            import resolveurl
            relevant_resolvers = resolveurl.relevant_resolvers(
                domain=domain, 
                include_universal=True, 
                include_popups=True, 
                include_external=True,
                include_disabled=False, 
                order_matters=True
            )
            logger.info(f"Found {len(relevant_resolvers)} relevant resolvers for domain: {domain}")
        except Exception as e:
            logger.warning(f"Could not get relevant resolvers: {e}, falling back to all resolvers")
            relevant_resolvers = get_all_resolvers()
            # Filter by domain manually
            filtered_resolvers = []
            for resolver_class in relevant_resolvers:
                try:
                    if hasattr(resolver_class, 'domains'):
                        for res_domain in resolver_class.domains:
                            if domain and (domain in res_domain.lower() or res_domain == '*'):
                                filtered_resolvers.append(resolver_class)
                                break
                except:
                    continue
            relevant_resolvers = filtered_resolvers
            logger.info(f"Manually filtered to {len(relevant_resolvers)} relevant resolvers")
        
        # Try each relevant resolver
        for resolver_class in relevant_resolvers:
            try:
                # Skip disabled resolvers
                if hasattr(resolver_class, '_is_enabled') and not resolver_class._is_enabled():
                    continue
                
                logger.info(f"Trying resolver: {resolver_class.name}")
                
                # Create resolver instance
                resolver = resolver_class()
                
                # Check if resolver handles this URL
                if hasattr(resolver, 'valid_url') and resolver.valid_url(url, domain):
                    # Get host and media_id
                    host, media_id = resolver.get_host_and_id(url)
                    if host and media_id:
                        # Try to resolve
                        result = resolver.get_media_url(host, media_id)
                        if result and result != False:
                            logger.info(f"Successfully resolved with {resolver_class.name}: {url} -> {result}")
                            return result
                        
            except Exception as e:
                logger.debug(f"Resolver {resolver_class.name} failed: {e}")
                continue
        
        return None
        
    except Exception as e:
        logger.error(f"Error in manual resolver search: {e}")
        return None

def resolve_url_complete(url):
    """Complete URL resolution using all available methods"""
    # Try main ResolveURL system first
    result = resolve_url_with_resolveurl(url)
    if result:
        return result
    
    # Try manual resolver search
    result = resolve_with_manual_resolver_search(url)
    if result:
        return result
    
    # Try simple direct link check
    if url and any(ext in url.lower() for ext in ['.mp4', '.avi', '.mkv', '.mov', '.webm']):
        try:
            import requests
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                if 'video' in content_type:
                    return url
        except:
            pass
    
    return None

# HTML template for web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ResolveURL API - Complete Edition</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: #333; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat-card { padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="url"], textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; margin-bottom: 10px; }
        button:hover { background-color: #0056b3; }
        .result { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; background-color: #f9f9f9; }
        .error { background-color: #f8d7da; border-color: #f5c6cb; color: #721c24; }
        .success { background-color: #d4edda; border-color: #c3e6cb; color: #155724; }
        .info { background-color: #d1ecf1; border-color: #bee5eb; color: #0c5460; }
        pre { white-space: pre-wrap; word-wrap: break-word; max-height: 400px; overflow-y: auto; }
        .resolver-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 10px; margin-top: 10px; }
        .resolver-item { padding: 8px; border: 1px solid #ddd; border-radius: 4px; background: #fff; font-size: 12px; }
        .resolver-name { font-weight: bold; color: #333; }
        .resolver-domains { color: #666; font-size: 11px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ResolveURL API - Complete Edition</h1>
        <p>Full integration with all {{ resolver_count }} ResolveURL plugins</p>
        
        <div class="stats">
            <div class="stat-card">
                <h3>{{ resolver_count }}</h3>
                <p>Total Resolvers</p>
            </div>
            <div class="stat-card">
                <h3>{{ enabled_count }}</h3>
                <p>Enabled Resolvers</p>
            </div>
            <div class="stat-card">
                <h3>{{ universal_count }}</h3>
                <p>Universal Resolvers</p>
            </div>
        </div>
        
        <div class="form-group">
            <label for="url">URL to resolve:</label>
            <input type="url" id="url" placeholder="https://example.com/video-link" required>
        </div>
        
        <div class="form-group">
            <button onclick="resolveUrl()">Resolve URL</button>
            <button onclick="getResolvers()">List All Resolvers</button>
            <button onclick="getEnabledResolvers()">List Enabled Only</button>
            <button onclick="testUrls()">Test Sample URLs</button>
            <button onclick="searchResolvers()">Search Resolvers</button>
        </div>
        
        <div class="form-group">
            <label for="search">Search resolvers by domain:</label>
            <input type="text" id="search" placeholder="youtube.com, streamtape.com, etc.">
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
                resultContent.textContent = 'Resolving URL...';
                resultDiv.className = 'result info';
                resultDiv.style.display = 'block';
                
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
            } catch (error) {
                resultDiv.className = 'result error';
                resultContent.textContent = 'Error: ' + error.message;
            }
        }
        
        async function getResolvers() {
            const resultDiv = document.getElementById('result');
            const resultContent = document.getElementById('result-content');
            
            try {
                resultContent.textContent = 'Loading resolvers...';
                resultDiv.className = 'result info';
                resultDiv.style.display = 'block';
                
                const response = await fetch('/api/resolvers');
                const data = await response.json();
                resultDiv.className = 'result success';
                resultContent.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                resultDiv.className = 'result error';
                resultContent.textContent = 'Error: ' + error.message;
            }
        }
        
        async function getEnabledResolvers() {
            const resultDiv = document.getElementById('result');
            const resultContent = document.getElementById('result-content');
            
            try {
                resultContent.textContent = 'Loading enabled resolvers...';
                resultDiv.className = 'result info';
                resultDiv.style.display = 'block';
                
                const response = await fetch('/api/resolvers?enabled_only=true');
                const data = await response.json();
                resultDiv.className = 'result success';
                resultContent.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                resultDiv.className = 'result error';
                resultContent.textContent = 'Error: ' + error.message;
            }
        }
        
        async function testUrls() {
            const testUrls = [
                'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'https://youtu.be/dQw4w9WgXcQ',
                'https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4'
            ];
            
            const resultDiv = document.getElementById('result');
            const resultContent = document.getElementById('result-content');
            
            try {
                resultContent.textContent = 'Testing URLs...';
                resultDiv.className = 'result info';
                resultDiv.style.display = 'block';
                
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
            } catch (error) {
                resultDiv.className = 'result error';
                resultContent.textContent = 'Error: ' + error.message;
            }
        }
        
        async function searchResolvers() {
            const domain = document.getElementById('search').value;
            if (!domain) {
                alert('Please enter a domain to search for');
                return;
            }
            
            const resultDiv = document.getElementById('result');
            const resultContent = document.getElementById('result-content');
            
            try {
                resultContent.textContent = 'Searching resolvers...';
                resultDiv.className = 'result info';
                resultDiv.style.display = 'block';
                
                const response = await fetch(`/api/resolvers/search?domain=${encodeURIComponent(domain)}`);
                const data = await response.json();
                resultDiv.className = 'result success';
                resultContent.textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                resultDiv.className = 'result error';
                resultContent.textContent = 'Error: ' + error.message;
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main web interface with resolver statistics"""
    try:
        resolvers = get_all_resolvers()
        enabled_resolvers = [r for r in resolvers if getattr(r, '_is_enabled', lambda: True)()]
        universal_resolvers = [r for r in resolvers if getattr(r, 'isUniversal', lambda: False)()]
        
        return render_template_string(HTML_TEMPLATE,
            resolver_count=len(resolvers),
            enabled_count=len(enabled_resolvers),
            universal_count=len(universal_resolvers)
        )
    except Exception as e:
        logger.error(f"Error loading index page: {e}")
        return render_template_string(HTML_TEMPLATE,
            resolver_count=0,
            enabled_count=0,
            universal_count=0
        )

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        resolvers = get_all_resolvers()
        return jsonify({
            'status': 'healthy',
            'service': 'ResolveURL API - Complete Edition',
            'version': '2.0.0',
            'resolvers': len(resolvers),
            'compatibility_layer': True
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

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
        logger.info(f"API resolve request: {url}")
        
        result = resolve_url_complete(url)
        
        if result:
            return jsonify({
                'success': True,
                'original_url': url,
                'resolved_url': result,
                'message': 'URL resolved successfully',
                'system': 'Complete ResolveURL integration'
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
        logger.debug(traceback.format_exc())
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/resolvers', methods=['GET'])
def api_get_resolvers():
    """Get list of available resolvers"""
    try:
        enabled_only = request.args.get('enabled_only', 'false').lower() == 'true'
        
        all_resolvers = get_all_resolvers()
        
        if enabled_only:
            resolvers = [r for r in all_resolvers if getattr(r, '_is_enabled', lambda: True)()]
        else:
            resolvers = all_resolvers
        
        resolver_list = []
        for resolver in resolvers:
            try:
                info = format_resolver_info(resolver)
                resolver_list.append(info)
            except Exception as e:
                logger.error(f"Error formatting resolver {resolver}: {e}")
                resolver_list.append({
                    'name': str(resolver),
                    'error': str(e)
                })
        
        # Sort by name for consistent output
        resolver_list.sort(key=lambda x: x.get('name', '').lower())
        
        return jsonify({
            'resolvers': resolver_list,
            'count': len(resolver_list),
            'total_available': len(all_resolvers),
            'enabled_only': enabled_only
        })
        
    except Exception as e:
        logger.error(f"Error getting resolvers: {e}")
        logger.debug(traceback.format_exc())
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/api/resolvers/search', methods=['GET'])
def api_search_resolvers():
    """Search resolvers by domain"""
    try:
        domain = request.args.get('domain', '').lower()
        if not domain:
            return jsonify({
                'error': 'Missing domain parameter'
            }), 400
        
        all_resolvers = get_all_resolvers()
        matching_resolvers = []
        
        for resolver in all_resolvers:
            try:
                resolver_domains = getattr(resolver, 'domains', [])
                if any(domain in resolver_domain.lower() for resolver_domain in resolver_domains):
                    info = format_resolver_info(resolver)
                    matching_resolvers.append(info)
            except Exception as e:
                logger.error(f"Error checking resolver {resolver}: {e}")
        
        return jsonify({
            'domain': domain,
            'resolvers': matching_resolvers,
            'count': len(matching_resolvers)
        })
        
    except Exception as e:
        logger.error(f"Error searching resolvers: {e}")
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
                logger.info(f"Resolving: {url}")
                result = resolve_url_complete(url)
                results.append({
                    'original_url': url,
                    'success': bool(result),
                    'resolved_url': result if result else None
                })
            except Exception as e:
                logger.error(f"Error resolving {url}: {e}")
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
    
    parser = argparse.ArgumentParser(description='ResolveURL REST API Server - Complete Edition')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Initialize and test the resolver system
    try:
        resolvers = get_all_resolvers()
        enabled_resolvers = [r for r in resolvers if getattr(r, '_is_enabled', lambda: True)()]
        
        print(f"Starting ResolveURL Complete API server on {args.host}:{args.port}")
        print(f"Web interface: http://{args.host}:{args.port}")
        print(f"Health check: http://{args.host}:{args.port}/health")
        print("")
        print(f"Loaded {len(resolvers)} resolver plugins ({len(enabled_resolvers)} enabled)")
        print("This server provides full ResolveURL functionality with all resolver plugins!")
        
    except Exception as e:
        logger.error(f"Failed to initialize resolver system: {e}")
        print("Error: Could not initialize resolver system. Check logs for details.")
        sys.exit(1)
    
    app.run(host=args.host, port=args.port, debug=args.debug)