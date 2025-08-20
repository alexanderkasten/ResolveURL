#!/usr/bin/env python3
"""
ResolveURL API Client Example
Demonstrates how to use the ResolveURL REST API
"""
import requests
import json
import sys

# Server configuration
API_BASE = "http://localhost:5000"

def test_health():
    """Test server health"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"✓ Server is healthy: {data['service']} v{data['version']}")
        print(f"  Resolvers available: {data['resolvers']}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def get_resolvers():
    """Get list of available resolvers"""
    try:
        response = requests.get(f"{API_BASE}/api/resolvers?enabled_only=true")
        response.raise_for_status()
        data = response.json()
        
        print(f"\\n📋 Found {data['count']} enabled resolvers:")
        for resolver in data['resolvers'][:10]:  # Show first 10
            domains = resolver.get('domains', [])
            domain_str = ', '.join(domains[:3])  # Show first 3 domains
            if len(domains) > 3:
                domain_str += f" (and {len(domains)-3} more)"
            print(f"  • {resolver['name']}: {domain_str}")
        
        if data['count'] > 10:
            print(f"  ... and {data['count'] - 10} more resolvers")
        
        return data['resolvers']
    except Exception as e:
        print(f"✗ Failed to get resolvers: {e}")
        return []

def resolve_url(url):
    """Resolve a single URL"""
    try:
        print(f"\\n🔍 Resolving: {url}")
        response = requests.post(f"{API_BASE}/api/resolve", 
                               json={"url": url}, 
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✓ Resolved to: {data['resolved_url']}")
                return data['resolved_url']
            else:
                print(f"✗ Resolution failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"✗ API error: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Request failed: {e}")
    
    return None

def resolve_multiple_urls(urls):
    """Resolve multiple URLs"""
    try:
        print(f"\\n🔍 Resolving {len(urls)} URLs...")
        response = requests.post(f"{API_BASE}/api/resolve/multiple", 
                               json={"urls": urls}, 
                               timeout=60)
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Batch resolution: {data['successful']}/{data['total']} successful")
        
        for result in data['results']:
            status = "✓" if result['success'] else "✗"
            url = result['original_url']
            if result['success']:
                resolved = result['resolved_url']
                print(f"  {status} {url} -> {resolved}")
            else:
                error = result.get('error', 'Failed')
                print(f"  {status} {url} -> {error}")
        
        return data['results']
        
    except Exception as e:
        print(f"✗ Batch resolution failed: {e}")
        return []

def search_resolvers(domain):
    """Search for resolvers by domain"""
    try:
        print(f"\\n🔎 Searching resolvers for domain: {domain}")
        response = requests.get(f"{API_BASE}/api/resolvers/search?domain={domain}")
        response.raise_for_status()
        data = response.json()
        
        if data['count'] > 0:
            print(f"✓ Found {data['count']} resolver(s):")
            for resolver in data['resolvers']:
                print(f"  • {resolver['name']}: {resolver['domains']}")
        else:
            print("✗ No resolvers found for this domain")
            
        return data['resolvers']
        
    except Exception as e:
        print(f"✗ Search failed: {e}")
        return []

def main():
    """Main demo function"""
    print("ResolveURL API Client Demo")
    print("=" * 30)
    
    # Test server health
    if not test_health():
        print("\\nServer is not available. Make sure it's running:")
        print("  ./start_complete_server.sh")
        sys.exit(1)
    
    # Get resolver list
    resolvers = get_resolvers()
    
    # Search for specific resolvers
    search_resolvers("youtube.com")
    search_resolvers("streamtape.com")
    
    # Test URL resolution
    test_urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4",
    ]
    
    # Resolve individual URLs
    for url in test_urls:
        resolve_url(url)
    
    # Resolve multiple URLs at once
    resolve_multiple_urls(test_urls)
    
    print("\\n✓ Demo completed! Check the web interface at http://localhost:5000")

if __name__ == "__main__":
    main()