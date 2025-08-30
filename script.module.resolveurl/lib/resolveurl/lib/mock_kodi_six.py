"""
Mock kodi_six module for standalone operation
"""
import os
import shutil
import tempfile
from urllib.parse import urlencode

class MockXBMC:
    LOGDEBUG = 0
    LOGINFO = 1
    LOGWARNING = 2
    LOGERROR = 3
    LOGFATAL = 4
    
    @staticmethod
    def log(message, level=LOGINFO):
        import logging
        log_levels = {0: logging.DEBUG, 1: logging.INFO, 2: logging.WARNING, 3: logging.ERROR, 4: logging.CRITICAL}
        logging.getLogger('xbmc').log(log_levels.get(level, logging.INFO), message)
    
    @staticmethod
    def sleep(ms):
        import time
        time.sleep(ms / 1000.0)
    
    @staticmethod
    def executebuiltin(command):
        print(f"Executing builtin: {command}")
    
    @staticmethod
    def executeJSONRPC(command):
        return '{"result": {}}'
    
    @staticmethod
    def getInfoLabel(label):
        if label == "System.BuildVersion":
            return "21.0.0"
        return ""
    
    @staticmethod
    def translatePath(path):
        if path.startswith('special://home'):
            return path.replace('special://home/', os.path.expanduser('~/.kodi/'))
        elif path.startswith('special://profile'):
            return path.replace('special://profile/', os.path.join(tempfile.gettempdir(), 'resolveurl/'))
        elif path.startswith('special://temp'):
            return path.replace('special://temp/', tempfile.gettempdir() + '/')
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
    def copy(src, dst):
        try:
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False
    
    @staticmethod
    def delete(path):
        try:
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            return True
        except Exception:
            return False
    
    @staticmethod
    def translatePath(path):
        return MockXBMC.translatePath(path)

class MockDialog:
    def select(self, heading, options):
        # In standalone mode, return first option
        return 0 if options else -1
    
    def ok(self, heading, line1='', line2='', line3=''):
        print(f"OK Dialog: {heading}")
        return True
    
    def yesno(self, heading, line1='', line2='', line3='', nolabel='No', yeslabel='Yes'):
        # Default to yes in standalone mode
        return True

class MockXBMCGUI:
    Dialog = MockDialog
    
    class DialogProgress:
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
    
    class DialogBusy:
        def __init__(self):
            self.canceled = False
        
        def create(self):
            pass
        
        def update(self, percent):
            pass
        
        def iscanceled(self):
            return self.canceled
        
        def close(self):
            pass

class MockXBMCAddon:
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
        os.makedirs(self.addon_info['profile'], exist_ok=True)
    
    def getSetting(self, key):
        return self.settings.get(key, '')
    
    def setSetting(self, key, value):
        self.settings[key] = str(value)
    
    def openSettings(self):
        print(f"Settings would open for {self.addon_id}")
    
    def getAddonInfo(self, info_type):
        return self.addon_info.get(info_type, '')

class MockXBMCPlugin:
    SORT_METHOD_UNSORTED = 0
    SORT_METHOD_VIDEO_SORT_TITLE_IGNORE_THE = 1
    SORT_METHOD_VIDEO_YEAR = 2
    
    @staticmethod
    def addSortMethod(handle, sortMethod):
        pass
    
    @staticmethod
    def setContent(handle, content):
        pass
    
    @staticmethod
    def endOfDirectory(handle, succeeded=True, updateListing=False, cacheToDisc=True):
        pass

# Export the mock classes
xbmc = MockXBMC()
xbmcvfs = MockXBMCVFS()
xbmcgui = MockXBMCGUI()
xbmcaddon = MockXBMCAddon
xbmcplugin = MockXBMCPlugin()