"""
Standalone logging module
This module provides logging functionality without requiring Kodi/XBMC
"""
import logging
import sys
import os

# Set up basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.expanduser('~'), 'resolveurl.log'))
    ]
)

# Log level constants for compatibility
LOGDEBUG = logging.DEBUG
LOGERROR = logging.ERROR
LOGWARNING = logging.WARNING
LOGINFO = logging.INFO

def execute_jsonrpc(command):
    """Mock JSONRPC execution"""
    return {'result': {}}

def _is_debugging():
    """Check if debugging is enabled"""
    return True

class Logger(object):
    __loggers = {}
    __name = 'ResolveURL'
    
    def __init__(self, name=None):
        self.name = name or self.__name
        self.logger = logging.getLogger(self.name)
    
    @classmethod
    def get_logger(cls, name=None):
        if name is None:
            name = cls.__name
        
        if name not in cls.__loggers:
            cls.__loggers[name] = cls(name)
        
        return cls.__loggers[name]
    
    def log(self, message, level=LOGINFO):
        self.logger.log(level, message)
    
    def log_debug(self, message):
        self.logger.debug(message)
    
    def log_info(self, message):
        self.logger.info(message)
    
    def log_warning(self, message):
        self.logger.warning(message)
    
    def log_error(self, message):
        self.logger.error(message)
    
    def disable(self):
        self.logger.disabled = True
    
    def enable(self):
        self.logger.disabled = False