"""
Standalone Compatibility Layer for ResolveURL
Provides comprehensive mocking of Kodi dependencies to enable all resolver plugins
to work in a standalone Python environment without Kodi.
"""
import os
import sys
import json
import logging
import requests
from urllib.parse import urljoin, urlparse
import re
import hashlib
import time
from collections import defaultdict

# Add the resolveurl lib path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(current_dir, 'lib')
resolveurl_path = os.path.join(current_dir, 'lib', 'resolveurl')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)
if resolveurl_path not in sys.path:
    sys.path.insert(0, resolveurl_path)

logger = logging.getLogger(__name__)

# Mock settings storage
_settings_store = {
    'allow_universal': 'true',
    'allow_popups': 'true', 
    'auto_pick': 'true',
    'use_cache': 'true',
    'addon_debug': 'false',
    'personal_nid': '',
    'last_ua_create': '0',
    'current_ua': '',
}

# Mock cache storage
_cache_store = {}

class MockLogger:
    """Mock logger for resolveurl"""
    def log_debug(self, msg):
        logger.debug(msg)
    
    def log_notice(self, msg):
        logger.info(msg)
    
    def log_warning(self, msg):
        logger.warning(msg)
    
    def log_error(self, msg):
        logger.error(msg)
    
    def log(self, msg, level=0):
        """Generic log method"""
        if level >= 3:  # WARNING
            logger.warning(msg)
        elif level >= 1:  # INFO
            logger.info(msg)
        else:  # DEBUG
            logger.debug(msg)
    
    def disable(self):
        """Disable logging"""
        pass
    
    def enable(self):
        """Enable logging"""
        pass

class MockKodi:
    """Mock Kodi module"""
    @staticmethod
    def get_setting(setting_id):
        return _settings_store.get(setting_id, '')
    
    @staticmethod 
    def set_setting(setting_id, value):
        _settings_store[setting_id] = value
    
    @staticmethod
    def get_path():
        return current_dir
    
    @staticmethod
    def get_profile():
        return os.path.join(current_dir, 'profile')
    
    @staticmethod
    def translate_path(path):
        return path
    
    @staticmethod
    def get_version():
        return '3.0.0'
    
    @staticmethod
    def kodi_version():
        return 21
    
    @staticmethod
    def open_settings():
        pass
    
    @staticmethod
    def has_addon(addon_id):
        return addon_id == 'plugin.video.youtube'
    
    @staticmethod
    def i18n(msg_id):
        # Return basic English strings for common message IDs
        translations = {
            'enable_universal': 'Enable Universal Resolvers',
            'enable_popups': 'Enable Popup Windows',
            'auto_pick': 'Auto-select single source',
            'use_function_cache': 'Use Function Cache',
            'reset_function_cache': 'Reset Function Cache',
            'clean_settings': 'Clean Settings',
            'universal_resolvers': 'Universal Resolvers',
            'resolvers': 'Resolvers'
        }
        return translations.get(msg_id, msg_id)
    
    @staticmethod
    def supported_video_extensions():
        return ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.ts', '.mpg', '.mpeg']

class MockNet:
    """Mock Network class that wraps requests"""
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
        })
    
    def http_GET(self, url, headers=None, cookies=None, compression=True, allow_redirect=True, cache_limit=8):
        """Mock HTTP GET method"""
        try:
            response = self.session.get(
                url, 
                headers=headers or {}, 
                cookies=cookies or {},
                allow_redirects=allow_redirect,
                timeout=30
            )
            
            # Create a mock response object that matches expected interface
            class MockResponse:
                def __init__(self, response):
                    self._response = response
                    self.content = response.text
                    self.status_code = response.status_code
                    self.headers = response.headers
                    self.url = response.url
                    
                def get_url(self):
                    return self.url
                    
                def get_headers(self):
                    return dict(self.headers)
            
            return MockResponse(response)
        except Exception as e:
            logger.error(f"HTTP GET error for {url}: {e}")
            raise
    
    def http_POST(self, url, form_data=None, headers=None, cookies=None, compression=True, allow_redirect=True):
        """Mock HTTP POST method"""
        try:
            response = self.session.post(
                url,
                data=form_data,
                headers=headers or {},
                cookies=cookies or {},
                allow_redirects=allow_redirect,
                timeout=30
            )
            
            class MockResponse:
                def __init__(self, response):
                    self._response = response
                    self.content = response.text
                    self.status_code = response.status_code
                    self.headers = response.headers
                    self.url = response.url
                    
                def get_url(self):
                    return self.url
                    
                def get_headers(self):
                    return dict(self.headers)
            
            return MockResponse(response)
        except Exception as e:
            logger.error(f"HTTP POST error for {url}: {e}")
            raise

class MockCache:
    """Mock cache functionality"""
    @staticmethod
    def get(cache_function, cache_duration=0):
        """Simple caching decorator"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Simple cache key based on function name and args
                cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
                
                if cache_key in _cache_store:
                    cached_time, cached_result = _cache_store[cache_key]
                    if cache_duration == 0 or (time.time() - cached_time) < cache_duration:
                        return cached_result
                
                result = func(*args, **kwargs)
                _cache_store[cache_key] = (time.time(), result)
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def cache_method(cache_limit=1):
        """Mock cache_method decorator"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Simple cache key based on function name and args
                cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
                
                if cache_key in _cache_store:
                    cached_time, cached_result = _cache_store[cache_key]
                    # Simple time-based cache (cache for 5 minutes)
                    if (time.time() - cached_time) < 300:
                        return cached_result
                
                result = func(*args, **kwargs)
                _cache_store[cache_key] = (time.time(), result)
                return result
            return wrapper
        return decorator

class MockHelpers:
    """Mock helpers module"""
    @staticmethod
    def get_ua():
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
    
    @staticmethod
    def append_headers(headers):
        return headers or {}
    
    @staticmethod
    def gibberish():
        import random
        import string
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    @staticmethod 
    def scrape_sources(html, result=None, patterns=None, generic_patterns=None):
        """Extract video sources from HTML"""
        if result is None:
            result = []
        
        # Basic pattern matching for common video sources
        video_patterns = [
            r'"(https?://[^"]+\.mp4[^"]*)"',
            r"'(https?://[^']+\.mp4[^']*)'",
            r'src="(https?://[^"]+\.mp4[^"]*)"',
            r'"file":\s*"([^"]+\.mp4[^"]*)"',
            r'"url":\s*"([^"]+\.mp4[^"]*)"',
        ]
        
        if patterns:
            video_patterns.extend(patterns)
        
        for pattern in video_patterns:
            matches = re.findall(pattern, html, re.I)
            for match in matches:
                if match.startswith('http'):
                    result.append({
                        'quality': 'HD',
                        'url': match,
                        'direct': True
                    })
        
        return result

# Mock XBMC modules
class MockXBMC:
    LOGDEBUG = 0
    LOGINFO = 1
    LOGNOTICE = 2
    LOGWARNING = 3
    LOGERROR = 4
    LOGFATAL = 5
    
    @staticmethod
    def log(msg, level=LOGDEBUG):
        if level >= MockXBMC.LOGWARNING:
            logger.warning(msg)
        elif level >= MockXBMC.LOGINFO:
            logger.info(msg)
        else:
            logger.debug(msg)

class MockXBMCVFS:
    @staticmethod
    def exists(path):
        return os.path.exists(path)
    
    @staticmethod
    def mkdirs(path):
        os.makedirs(path, exist_ok=True)
        
    @staticmethod
    def listdir(path):
        if os.path.exists(path):
            items = os.listdir(path)
            dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
            files = [item for item in items if os.path.isfile(os.path.join(path, item))]
            return (dirs, files)
        return ([], [])

class MockXBMCGUI:
    class Dialog:
        @staticmethod
        def select(heading, options):
            # For standalone mode, just return first option
            return 0 if options else -1

class MockXBMCAddon:
    def __init__(self, addon_id='script.module.resolveurl'):
        self.addon_id = addon_id
    
    def getSetting(self, setting_id):
        return _settings_store.get(setting_id, '')
    
    def setSetting(self, setting_id, value):
        _settings_store[setting_id] = value
    
    def getAddonInfo(self, info_type):
        if info_type == 'path':
            return current_dir
        elif info_type == 'profile':
            return os.path.join(current_dir, 'profile')
        elif info_type == 'version':
            return '3.0.0'
        return ''

# Setup mock modules in sys.modules
sys.modules['xbmc'] = MockXBMC()
sys.modules['xbmcvfs'] = MockXBMCVFS()
sys.modules['xbmcgui'] = MockXBMCGUI()
sys.modules['xbmcaddon'] = MockXBMCAddon
sys.modules['kodi_six'] = type('MockKodiSix', (), {
    'xbmcvfs': MockXBMCVFS(),
    'xbmcgui': MockXBMCGUI(),
    'xbmcaddon': MockXBMCAddon
})()

# Setup resolveurl mock modules  
sys.modules['resolveurl.lib.kodi'] = MockKodi()
sys.modules['resolveurl.lib.net'] = type('MockNetModule', (), {
    'Net': MockNet,
    'get_ua': MockHelpers.get_ua
})()
sys.modules['resolveurl.lib.cache'] = MockCache()
sys.modules['resolveurl.lib.helpers'] = MockHelpers()
sys.modules['resolveurl.lib.log_utils'] = type('MockLogUtils', (), {
    'Logger': type('Logger', (), {
        'get_logger': lambda name=None: MockLogger()
    })
})()

# Mock additional modules that may be needed
sys.modules['resolveurl.lib'] = type('MockLib', (), {
    'kodi': MockKodi(),
    'net': type('MockNetModule', (), {
        'Net': MockNet,
        'get_ua': MockHelpers.get_ua
    })(),
    'cache': MockCache(),
    'helpers': MockHelpers(),
    'log_utils': type('MockLogUtils', (), {
        'Logger': type('Logger', (), {
            'get_logger': lambda name=None: MockLogger()
        })
    })(),
    'pyaes': type('MockPyAES', (), {})()
})()

# Mock pyaes module that's imported by common.py
class MockPyAES:
    """Mock pyaes encryption library"""
    class Decrypter:
        def __init__(self, *args):
            pass
        def feed(self, data=None):
            return data or b''
    
    class Encrypter:
        def __init__(self, *args):
            pass
        def feed(self, data=None):
            return data or b''
    
    class AESModeOfOperationCBC:
        def __init__(self, key, iv):
            self.key = key
            self.iv = iv

sys.modules['pyaes'] = MockPyAES()
sys.modules['resolveurl.lib.pyaes'] = MockPyAES()

def get_ua():
    """Get user agent string"""
    return MockHelpers.get_ua()

# Create compatibility constants
USER_AGENTS = {
    'FF_USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
    'IE_USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'OPERA_USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 OPR/119.0.0.0',
    'RAND_UA': get_ua(),
}

# Ensure compatibility constants are available
for ua_name, ua_string in USER_AGENTS.items():
    globals()[ua_name] = ua_string

logger.info("Standalone compatibility layer initialized")