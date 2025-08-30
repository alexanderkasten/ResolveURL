"""
Standalone Kodi compatibility module
This module provides Kodi-compatible functionality without requiring Kodi/XBMC
"""
import os
import sys
import json
import tempfile
from urllib.parse import parse_qs, urlencode

# Mock addon for standalone operation
class MockAddon:
    def __init__(self, addon_id='script.module.resolveurl'):
        self.addon_id = addon_id
        self.settings = {}
        self.addon_info = {
            'path': os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'profile': os.path.join(tempfile.gettempdir(), 'resolveurl'),
            'version': '6.0.0',
            'name': 'ResolveURL',
            'id': addon_id
        }
        # Create profile directory if it doesn't exist
        os.makedirs(self.addon_info['profile'], exist_ok=True)
    
    def getSetting(self, key):
        return self.settings.get(key, '')
    
    def setSetting(self, key, value):
        self.settings[key] = str(value)
    
    def openSettings(self):
        print(f"Settings would open for {self.addon_id}")
    
    def getAddonInfo(self, info_type):
        return self.addon_info.get(info_type, '')

# Initialize mock addon
addon = MockAddon('script.module.resolveurl')

# Kodi function replacements
get_setting = addon.getSetting
show_settings = addon.openSettings
def sleep(ms):
    import time
    time.sleep(ms / 1000.0)

def _log(message, level=0):
    import logging
    log_levels = {0: logging.DEBUG, 1: logging.INFO, 2: logging.WARNING, 3: logging.ERROR}
    logging.getLogger('resolveurl').log(log_levels.get(level, logging.INFO), message)

py_ver = sys.version
py_info = sys.version_info

def get_path():
    return addon.getAddonInfo('path')

def get_profile():
    return addon.getAddonInfo('profile')

def translate_path(path):
    # Handle special paths
    if path.startswith('special://home'):
        return path.replace('special://home/', os.path.expanduser('~/.kodi/'))
    elif path.startswith('special://profile'):
        return path.replace('special://profile/', addon.getAddonInfo('profile') + '/')
    elif path.startswith('special://temp'):
        return path.replace('special://temp/', tempfile.gettempdir() + '/')
    return path

def set_setting(setting_id, value):
    addon.setSetting(setting_id, value)

def get_version():
    return addon.getAddonInfo('version')

def get_id():
    return addon.getAddonInfo('id')

def get_name():
    return addon.getAddonInfo('name')

def kodi_version():
    return 21.0  # Mock Kodi version

def supported_video_extensions():
    return ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp', '.mpg', '.mpeg']

def open_settings():
    addon.openSettings()

def get_keyboard(heading, default='', hide_input=False):
    # In standalone mode, return the default or get from environment
    return os.environ.get('RESOLVEURL_INPUT', default)

def i18n(string_id):
    # Simple i18n replacement - would normally use translation files
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
        'resolver_updated': 'Resolver Updated',
        'ub_authorized': 'UpToBox Authorized',
        'ub_auth_reset': 'UpToBox Authorization Reset'
    }
    return translations.get(string_id, string_id)

def get_plugin_url(queries):
    base_url = f"plugin://{get_id()}/"
    if queries:
        query_string = urlencode(queries)
        return f"{base_url}?{query_string}"
    return base_url

def parse_query(query_string):
    if query_string.startswith('?'):
        query_string = query_string[1:]
    return {k: v[0] if len(v) == 1 else v for k, v in parse_qs(query_string).items()}

def notify(header=None, msg='', duration=2000, sound=None):
    print(f"NOTIFICATION: {header}: {msg}")

def close_all():
    pass

def get_current_view():
    return None

def yesnoDialog(heading='', line1='', line2='', line3='', nolabel='', yeslabel=''):
    # In standalone mode, default to yes
    return True

class WorkingDialog:
    def __init__(self):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def is_canceled(self):
        return False
    
    def update(self, percent):
        pass

def has_addon(addon_id):
    return False  # In standalone mode, assume no other addons

class ProgressDialog:
    def __init__(self):
        self.canceled = False
    
    def create(self, heading='', line1='', line2='', line3=''):
        pass
    
    def update(self, percent, line1='', line2='', line3=''):
        pass
    
    def iscanceled(self):
        return self.canceled
    
    def close(self):
        pass

class CountdownDialog:
    def __init__(self):
        pass
    
    def start(self, func, args=None, kwargs=None):
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        return func(*args, **kwargs)

def end_of_directory(cache_to_disc=True):
    pass

def set_content(content):
    pass

def create_item(queries, label, thumb='', fanart='', is_folder=None, is_playable=None, total_items=0, menu_items=None, replace_menu=False):
    return {
        'label': label,
        'queries': queries,
        'thumb': thumb,
        'fanart': fanart,
        'is_folder': is_folder,
        'is_playable': is_playable
    }

def add_item(queries, list_item, fanart='', is_folder=None, is_playable=None, total_items=0, menu_items=None, replace_menu=False):
    pass