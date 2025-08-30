"""
Module patches for standalone operation
This module sets up monkey patches to replace Kodi dependencies
"""
import sys
import os
import json

# Mock kodi_six modules
class MockXBMC:
    LOGDEBUG = 0
    LOGINFO = 1
    LOGWARNING = 2
    LOGERROR = 3
    
    @staticmethod
    def log(message, level=1):
        print(f"[LOG {level}] {message}")
    
    @staticmethod
    def sleep(ms):
        import time
        time.sleep(ms / 1000.0)
    
    @staticmethod
    def executebuiltin(command):
        pass
    
    @staticmethod
    def executeJSONRPC(command):
        return '{"result": {}}'
    
    @staticmethod
    def getInfoLabel(label):
        return "21.0.0"
    
    @staticmethod
    def translatePath(path):
        import tempfile
        if path.startswith('special://'):
            return path.replace('special://home/', os.path.expanduser('~/.kodi/'))
        return path

class MockXBMCVFS:
    @staticmethod
    def exists(path):
        return os.path.exists(path)
    
    @staticmethod
    def listdir(path):
        try:
            items = os.listdir(path)
            dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
            files = [item for item in items if os.path.isfile(os.path.join(path, item))]
            return [dirs, files]
        except OSError:
            return [[], []]
    
    @staticmethod
    def mkdirs(path):
        os.makedirs(path, exist_ok=True)
        return True
    
    @staticmethod
    def translatePath(path):
        return MockXBMC.translatePath(path)

class MockDialog:
    def select(self, heading, options):
        return 0 if options else -1
    
    def ok(self, heading, line1='', line2='', line3=''):
        return True
    
    def yesno(self, heading, line1='', line2='', line3='', nolabel='No', yeslabel='Yes'):
        return True

class MockXBMCGUI:
    Dialog = MockDialog
    
    class DialogProgress:
        def create(self, heading='', line1='', line2='', line3=''):
            pass
        def update(self, percent, line1='', line2='', line3=''):
            pass
        def iscanceled(self):
            return False
        def close(self):
            pass

class MockXBMCAddon:
    def __init__(self, addon_id='script.module.resolveurl'):
        self.addon_id = addon_id
        self.settings = {}
        import tempfile
        self.addon_info = {
            'path': os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'profile': os.path.join(tempfile.gettempdir(), 'resolveurl'),
            'version': '6.0.0',
            'name': 'ResolveURL',
            'id': addon_id
        }
        os.makedirs(self.addon_info['profile'], exist_ok=True)
    
    def getSetting(self, key):
        return self.settings.get(key, '')
    
    def setSetting(self, key, value):
        self.settings[key] = str(value)
    
    def openSettings(self):
        pass
    
    def getAddonInfo(self, info_type):
        return self.addon_info.get(info_type, '')

class MockXBMCPlugin:
    @staticmethod
    def setContent(handle, content):
        pass
    
    @staticmethod
    def endOfDirectory(handle, succeeded=True, updateListing=False, cacheToDisc=True):
        pass

# Patch the modules before any imports
def apply_patches():
    # Create mock modules
    mock_xbmc = MockXBMC()
    mock_xbmcvfs = MockXBMCVFS()
    mock_xbmcgui = MockXBMCGUI()
    mock_xbmcaddon = MockXBMCAddon
    mock_xbmcplugin = MockXBMCPlugin()
    
    # Mock kodi_six
    class MockKodiSix:
        xbmc = mock_xbmc
        xbmcvfs = mock_xbmcvfs
        xbmcgui = mock_xbmcgui
        xbmcaddon = mock_xbmcaddon
        xbmcplugin = mock_xbmcplugin
    
    # Apply patches to sys.modules
    sys.modules['kodi_six'] = MockKodiSix()
    sys.modules['xbmc'] = mock_xbmc
    sys.modules['xbmcvfs'] = mock_xbmcvfs
    sys.modules['xbmcgui'] = mock_xbmcgui
    sys.modules['xbmcaddon'] = mock_xbmcaddon
    sys.modules['xbmcplugin'] = mock_xbmcplugin

# Apply patches immediately when imported
apply_patches()