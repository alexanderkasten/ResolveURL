"""
Standalone common module for ResolveURL
This module provides common functionality without requiring Kodi/XBMC
"""
import os
import hashlib
import tempfile
from random import choice

# Import standalone modules instead of Kodi ones
from resolveurl.lib.standalone_log_utils import Logger
from resolveurl.lib.net import Net, get_ua
from resolveurl.lib import cache
from resolveurl.lib import pyaes

logger = Logger.get_logger()

# Path configurations for standalone operation
addon_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
plugins_path = os.path.join(addon_path, 'plugins')
profile_path = os.path.join(tempfile.gettempdir(), 'resolveurl')
os.makedirs(profile_path, exist_ok=True)

settings_file = os.path.join(addon_path, 'resources', 'settings.xml')
settings_path = os.path.join(addon_path, 'resources')
user_settings_file = os.path.join(profile_path, 'settings.xml')
addon_version = '6.0.0'
kodi_version = 21.0

# Settings storage for standalone operation
_settings = {
    'allow_universal': 'true',
    'allow_popups': 'true',
    'auto_pick': 'true',
    'use_cache': 'true'
}

def get_setting(key):
    return _settings.get(key, '')

def set_setting(key, value):
    _settings[key] = str(value)

def open_settings():
    print("Settings would open here")

def has_addon(addon_id):
    return False

def i18n(string_id):
    # Simple i18n replacement
    translations = {
        'priority': 'Priority',
        'enabled': 'Enabled',
        'login': 'Login',
        'settings_cleaned': 'Settings cleaned',
        'cache_reset': 'Cache reset',
        'cache_reset_failed': 'Cache reset failed',
        'enable_universal': 'Enable Universal Resolvers',
        'enable_popups': 'Enable Popup Resolvers',
        'auto_pick': 'Auto Pick Best Quality',
        'use_function_cache': 'Use Function Cache',
        'reset_function_cache': 'Reset Function Cache',
        'clean_settings': 'Clean Settings',
        'universal_resolvers': 'Universal Resolvers',
        'resolvers': 'Resolvers',
        'resolver_updated': 'Resolver Updated'
    }
    return translations.get(string_id, string_id)

# Supported video formats
VIDEO_FORMATS = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mpg', '.mpeg']

# User agents
IE_USER_AGENT = 'User-Agent: Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'
FF_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0'
OPERA_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 OPR/119.0.0.0'
IOS_USER_AGENT = 'Mozilla/5.0 (iPhone17,1; CPU iPhone OS 18_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Mohegan Sun/4.7.4'
IPAD_USER_AGENT = 'Mozilla/5.0 (iPad16,3; CPU OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Tropicana_NJ/5.7.1'
ANDROID_USER_AGENT = 'Mozilla/5.0 (Linux; Android 15; SM-S931U Build/AP3A.240905.015.A2; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/132.0.6834.163 Mobile Safari/537.36'
EDGE_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0'
CHROME_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
SAFARI_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.4 Safari/605.1.15'
SMR_USER_AGENT = 'ResolveURL for Kodi/%s' % (addon_version)

_USER_AGENTS = [FF_USER_AGENT, OPERA_USER_AGENT, EDGE_USER_AGENT, CHROME_USER_AGENT, SAFARI_USER_AGENT]
RAND_UA = choice(_USER_AGENTS)

def log_file_hash(path):
    try:
        with open(path, 'r') as f:
            py_data = f.read()
    except:
        py_data = ''
    
    logger.log('%s hash: %s' % (os.path.basename(path), hashlib.md5(py_data.encode()).hexdigest()))

def file_length(py_path, key=''):
    try:
        with open(py_path, 'r') as f:
            old_py = f.read()
        if key:
            old_py = encrypt_py(old_py, key)
        old_len = len(old_py)
    except:
        old_len = -1
    
    return old_len

def decrypt_py(cipher_text, key):
    if cipher_text:
        try:
            scraper_key = hashlib.sha256(key.encode()).digest()
            IV = b'\0' * 16
            decrypter = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(scraper_key, IV))
            plain_text = decrypter.feed(cipher_text)
            plain_text += decrypter.feed()
            if b'import' not in plain_text:
                plain_text = b''
            return plain_text.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.log_warning('Exception during Py Decrypt: %s' % (e))
            plain_text = ''
    else:
        plain_text = ''
    
    return plain_text

def encrypt_py(plain_text, key):
    if plain_text:
        try:
            scraper_key = hashlib.sha256(key.encode()).digest()
            IV = b'\0' * 16
            encrypter = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(scraper_key, IV))
            cipher_text = encrypter.feed(plain_text.encode())
            cipher_text += encrypter.feed()
        except Exception as e:
            logger.log_warning('Exception during Py Encrypt: %s' % (e))
            cipher_text = b''
    else:
        cipher_text = b''
    
    return cipher_text