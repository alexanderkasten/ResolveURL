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
        # Return setting from store if it exists
        if setting_id in _settings_store:
            return _settings_store[setting_id]
        
        # Default settings for resolvers - enable all resolvers by default
        if setting_id.endswith('_enabled'):
            return 'true'
        if setting_id.endswith('_login'):
            return 'true'
        if setting_id.endswith('_priority'):
            return '100'
        
        # Return empty string for unknown settings (existing behavior)
        return ''
    
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
        return '|%s' % '&'.join(['%s=%s' % (key, headers[key]) for key in headers]) if headers else ''
    
    @staticmethod
    def gibberish():
        import random
        import string
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    @staticmethod
    def b64decode(data, binary=False):
        """Base64 decode function"""
        import base64
        import six
        if len(data) % 4 != 0:
            data += '=' * (-len(data) % 4)
        result = base64.b64decode(data)
        return result if binary else six.ensure_str(result)
    
    @staticmethod
    def b64encode(data):
        """Base64 encode function"""
        import base64
        import six
        return six.ensure_str(base64.b64encode(data if isinstance(data, bytes) else six.b(data)))
    
    @staticmethod
    def get_hidden(html, form_id=None, index=None, include_submit=True):
        """Extract hidden form fields from HTML"""
        hidden = {}
        if form_id:
            pattern = r'''<form [^>]*(?:id|name)\s*=\s*['"]?%s['"]?[^>]*>(.*?)</form>''' % (form_id)
        else:
            pattern = '''<form[^>]*>(.*?)</form>'''

        for i, form in enumerate(re.finditer(pattern, html, re.DOTALL | re.I)):
            if index is None or i == index:
                for field in re.finditer('''<input [^>]*type=['"]?hidden['"]?[^>]*>''', form.group(1)):
                    match = re.search(r'''name\s*=\s*['"]([^'"]+)''', field.group(0))
                    match1 = re.search(r'''value\s*=\s*['"]([^'"]*)''', field.group(0))
                    if match and match1:
                        hidden[match.group(1)] = match1.group(1)

                if include_submit:
                    match = re.search('''<input [^>]*type=['"]?submit['"]?[^>]*>''', form.group(1))
                    if match:
                        name = re.search(r'''name\s*=\s*['"]([^'"]+)''', match.group(0))
                        value = re.search(r'''value\s*=\s*['"]([^'"]*)''', match.group(0))
                        if name and value:
                            hidden[name.group(1)] = value.group(1)
        return hidden
    
    @staticmethod
    def get_packed_data(html):
        """Extract packed JavaScript data"""
        # Simple fallback - return empty string for now
        # Full implementation would require jsunpack module
        return ''
    
    @staticmethod
    def get_redirect_url(url, headers=None, form_data=None):
        """Get redirect URL"""
        try:
            import requests
            if form_data:
                response = requests.post(url, data=form_data, headers=headers or {}, allow_redirects=False, timeout=10)
            else:
                response = requests.get(url, headers=headers or {}, allow_redirects=False, timeout=10)
            return response.headers.get('Location', url)
        except:
            return url
    
    @staticmethod
    def get_media_url(web_url, patterns=None, generic_patterns=True, referer=None, **kwargs):
        """Generic media URL extraction"""
        try:
            import requests
            headers = {'User-Agent': MockHelpers.get_ua()}
            if referer:
                headers['Referer'] = referer
            
            response = requests.get(web_url, headers=headers, timeout=10)
            html = response.text
            
            # Try to find video URLs
            video_patterns = patterns or []
            if generic_patterns:
                video_patterns.extend([
                    r'"(https?://[^"]+\.mp4[^"]*)"',
                    r'"file":\s*"([^"]+\.mp4[^"]*)"',
                    r'"url":\s*"([^"]+\.mp4[^"]*)"',
                ])
            
            for pattern in video_patterns:
                matches = re.findall(pattern, html, re.I)
                for match in matches:
                    if match.startswith('http'):
                        return match + MockHelpers.append_headers(headers)
            
            return False
        except:
            return False
    
    @staticmethod
    def pick_source(sources, auto_pick=True):
        """Pick the best source from a list"""
        if not sources:
            return False
        if len(sources) == 1:
            return sources[0][1]
        # Auto-pick the first (usually highest quality)
        return sources[0][1]
    
    @staticmethod
    def scrape_subtitles(html, web_url):
        """Extract subtitles from HTML"""
        return {}  # Simple fallback
    
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
    
    class ControlImage:
        def __init__(self, x, y, w, h, filename):
            self.x = x
            self.y = y 
            self.w = w
            self.h = h
            self.filename = filename
    
    class WindowDialog:
        def __init__(self):
            self.controls = []
        
        def addControl(self, control):
            self.controls.append(control)
        
        def show(self):
            pass
        
        def close(self):
            pass

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
    'xbmc': MockXBMC(),
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

# Mock JavaScript processing modules
class MockJSUnpack:
    """Mock JavaScript unpacking functionality"""
    @staticmethod
    def unpack(packed_js):
        return packed_js  # Return unpacked or original JS
    
    @staticmethod
    def detect(packed_js):
        return "eval" in packed_js.lower()

class MockJSUnhunt:
    """Mock JavaScript unhunting functionality"""
    @staticmethod
    def unhunt(js):
        return js  # Return processed or original JS

class MockJSUnfuck:
    """Mock JavaScript unfucking functionality"""
    @staticmethod  
    def unfuck(js):
        return js  # Return processed or original JS

class MockJJDecode:
    """Mock JJ decoding functionality"""
    @staticmethod
    def decode(encoded):
        return encoded  # Return decoded or original string

class MockAADecode:
    """Mock AA decoding functionality"""
    @staticmethod
    def decode(encoded):
        return encoded  # Return decoded or original string

class MockUnjuice:
    """Mock unjuice functionality"""
    @staticmethod
    def unjuice(js):
        return js  # Return processed or original JS

class MockUnwise:
    """Mock unwise functionality"""
    @staticmethod 
    def unwise(js):
        return js  # Return processed or original JS

class MockRijndael:
    """Mock Rijndael encryption"""
    @staticmethod
    def decrypt(data, key):
        return data  # Return dummy decrypted data
    
    @staticmethod
    def encrypt(data, key):
        return data  # Return dummy encrypted data

class MockRC4:
    """Mock RC4 encryption"""
    @staticmethod
    def decrypt(data, key):
        return data  # Return dummy decrypted data
    
    @staticmethod
    def encrypt(data, key):
        return data  # Return dummy encrypted data

class MockPBKDF2:
    """Mock PBKDF2 key derivation"""
    @staticmethod
    def pbkdf2(password, salt, iterations=1000, dklen=32):
        return b'dummy_key' * (dklen // 9 + 1)[:dklen]

class MockStrings:
    """Mock strings module"""
    @staticmethod
    def encode(s):
        return s.encode('utf-8') if isinstance(s, str) else s
    
    @staticmethod
    def decode(b):
        return b.decode('utf-8') if isinstance(b, bytes) else b

class MockRecaptchaV2:
    """Mock Recaptcha V2"""
    @staticmethod
    def solve_recaptcha(site_key, page_url):
        return "dummy_recaptcha_response"

class MockCaptchaWindow:
    """Mock captcha window"""
    @staticmethod
    def show_captcha(image_data):
        return "dummy_captcha_response"

class MockCustomProgressDialog:
    """Mock custom progress dialog"""
    def __init__(self):
        pass
    
    def update(self, percent, message=""):
        pass
    
    def close(self):
        pass

class MockPNG:
    """Mock PNG handling"""
    @staticmethod
    def decode(data):
        return data
    
    @staticmethod
    def encode(data):
        return data

class MockURLDispatcher:
    """Mock URL dispatcher"""
    @staticmethod
    def register(pattern, func):
        pass

class MockJSCrypto:
    """Mock JavaScript crypto functionality"""
    @staticmethod
    def jscrypto():
        return MockJSCrypto()
    
    @staticmethod
    def decrypt(data, key):
        return data  # Return dummy decrypted data
    
    @staticmethod
    def encrypt(data, key):
        return data  # Return dummy encrypted data

class MockWebSocket:
    """Mock WebSocket functionality"""
    def __init__(self, url):
        self.url = url
    
    def send(self, data):
        pass
    
    def recv(self):
        return "dummy_response"
    
    def close(self):
        pass

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

# Mock CAPTCHA functionality
class MockCaptchaLib:
    """Mock captcha_lib module"""
    @staticmethod
    def get_response(img, x=450, y=225, w=400, h=130):
        # Return dummy response for standalone mode
        return "dummy_captcha_response"
    
    @staticmethod
    def write_img(url=None, bin=None):
        # Return dummy image path
        return "/tmp/dummy_captcha.gif"
        
    @staticmethod
    def resolve_text_captcha(url):
        # Return dummy text captcha response
        return "dummy_text_response"

# Mock additional modules that may be needed - make it a proper module
class MockLibModule:
    """Mock lib module that behaves like a package"""
    def __init__(self):
        self.kodi = MockKodi()
        self.net = type('MockNetModule', (), {
            'Net': MockNet,
            'get_ua': MockHelpers.get_ua
        })()
        self.cache = MockCache()
        self.helpers = MockHelpers()
        self.log_utils = type('MockLogUtils', (), {
            'Logger': type('Logger', (), {
                'get_logger': lambda name=None: MockLogger()
            })
        })()
        self.pyaes = MockPyAES()
        self.captcha_lib = MockCaptchaLib()
        self.jsunpack = MockJSUnpack()
        self.jsunhunt = MockJSUnhunt() 
        self.jsunfuck = MockJSUnfuck()
        self.jjdecode = MockJJDecode()
        self.aadecode = MockAADecode()
        self.unjuice = MockUnjuice()
        self.unjuice2 = MockUnjuice()
        self.unwise = MockUnwise()
        self.rijndael = MockRijndael()
        self.rc4 = MockRC4()
        self.pbkdf2 = MockPBKDF2()
        self.strings = MockStrings()
        self.recaptcha_v2 = MockRecaptchaV2()
        self.captcha_window = MockCaptchaWindow()
        self.CustomProgressDialog = MockCustomProgressDialog
        self.png = MockPNG()
        self.url_dispatcher = MockURLDispatcher()
        self.jscrypto = type('JSCryptoModule', (), {
            'jscrypto': MockJSCrypto()
        })()
        self.websocket = type('WebSocketModule', (), {
            'WebSocket': MockWebSocket
        })()
        
        # Set __path__ to make it look like a package
        self.__path__ = ['/dummy/lib/path']

sys.modules['resolveurl.lib'] = MockLibModule()

sys.modules['pyaes'] = MockPyAES()

# Add individual module references 
mock_lib = sys.modules['resolveurl.lib']
sys.modules['resolveurl.lib.kodi'] = mock_lib.kodi
sys.modules['resolveurl.lib.net'] = mock_lib.net  
sys.modules['resolveurl.lib.cache'] = mock_lib.cache
sys.modules['resolveurl.lib.helpers'] = mock_lib.helpers
sys.modules['resolveurl.lib.log_utils'] = mock_lib.log_utils
sys.modules['resolveurl.lib.captcha_lib'] = mock_lib.captcha_lib
sys.modules['resolveurl.lib.jsunpack'] = mock_lib.jsunpack
sys.modules['resolveurl.lib.jsunhunt'] = mock_lib.jsunhunt
sys.modules['resolveurl.lib.jsunfuck'] = mock_lib.jsunfuck
sys.modules['resolveurl.lib.jjdecode'] = mock_lib.jjdecode
sys.modules['resolveurl.lib.aadecode'] = mock_lib.aadecode
sys.modules['resolveurl.lib.unjuice'] = mock_lib.unjuice
sys.modules['resolveurl.lib.unjuice2'] = mock_lib.unjuice2
sys.modules['resolveurl.lib.unwise'] = mock_lib.unwise
sys.modules['resolveurl.lib.rijndael'] = mock_lib.rijndael
sys.modules['resolveurl.lib.rc4'] = mock_lib.rc4
sys.modules['resolveurl.lib.pbkdf2'] = mock_lib.pbkdf2
sys.modules['resolveurl.lib.strings'] = mock_lib.strings
sys.modules['resolveurl.lib.recaptcha_v2'] = mock_lib.recaptcha_v2
sys.modules['resolveurl.lib.captcha_window'] = mock_lib.captcha_window
sys.modules['resolveurl.lib.CustomProgressDialog'] = mock_lib.CustomProgressDialog
sys.modules['resolveurl.lib.png'] = mock_lib.png
sys.modules['resolveurl.lib.url_dispatcher'] = mock_lib.url_dispatcher
sys.modules['resolveurl.lib.jscrypto'] = mock_lib.jscrypto
sys.modules['resolveurl.lib.websocket'] = mock_lib.websocket
sys.modules['resolveurl.lib.pyaes'] = mock_lib.pyaes

# Mock subdirectory modules
sys.modules['resolveurl.lib.jscrypto.jscrypto'] = mock_lib.jscrypto.jscrypto
sys.modules['resolveurl.lib.websocket.WebSocket'] = mock_lib.websocket.WebSocket

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