"""
Standalone ResolveURL module for web server operation
This module provides the main API without requiring Kodi/XBMC
"""
import re
import os
import sys
from six.moves import urllib_parse
import six

# Add the path to find our modules
current_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(current_dir, 'lib')
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)

# Mock kodi_six imports
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

class MockXBMCGUI:
    class Dialog:
        def select(self, heading, options):
            # Auto-select first option in standalone mode
            return 0 if options else -1

# Create mock objects
xbmcvfs = MockXBMCVFS()
xbmcgui = MockXBMCGUI()

# Import standalone common module
from resolveurl import standalone_common as common

# Import all plugins
try:
    from resolveurl.plugins import *  # NOQA
except Exception as e:
    common.logger.log_warning(f"Error importing plugins: {e}")

common.logger.log_debug('Initializing ResolveURL version: %s' % common.addon_version)
MAX_SETTINGS = 60

PLUGIN_DIRS = []
host_cache = {}

def add_plugin_dirs(dirs):
    global PLUGIN_DIRS
    if isinstance(dirs, six.string_types):
        PLUGIN_DIRS.append(dirs)
    else:
        PLUGIN_DIRS += dirs

def load_external_plugins():
    for d in PLUGIN_DIRS:
        common.logger.log_debug('Adding plugin path: %s' % d)
        sys.path.insert(0, d)
        for filename in xbmcvfs.listdir(d)[1]:
            if not filename.startswith('__') and filename.endswith('.py'):
                mod_name = filename[:-3]
                try:
                    imp = __import__(mod_name, globals(), locals())
                    sys.modules[mod_name] = imp
                    common.logger.log_debug('Loaded %s as %s from %s' % (imp, mod_name, filename))
                except Exception as e:
                    common.logger.log_warning('Failed to load plugin %s: %s' % (mod_name, e))

def relevant_resolvers(domain=None, include_universal=None, include_popups=None, include_external=False, include_disabled=False, order_matters=False):
    if include_external:
        load_external_plugins()

    if isinstance(domain, six.string_types):
        domain = domain.lower()

    if include_universal is None:
        include_universal = common.get_setting('allow_universal') == "true"

    if include_popups is None:
        include_popups = common.get_setting('allow_popups') == "true"
    if include_popups is False:
        common.logger.log_debug('Resolvers that require popups have been disabled')

    classes = ResolveUrl.__class__.__subclasses__(ResolveUrl) + ResolveUrl.__class__.__subclasses__(ResolveGeneric)
    relevant = []
    for resolver in classes:
        if include_disabled or resolver._is_enabled():
            if (include_universal or not resolver.isUniversal()) and (include_popups or not resolver.isPopup()):
                if domain is None or ((domain and any(domain in res_domain.lower() for res_domain in resolver.domains)) or '*' in resolver.domains):
                    relevant.append(resolver)

    if order_matters:
        relevant.sort(key=lambda x: x._get_priority())

    # Add attribute priority
    for i in relevant:
        i.priority = i._get_priority()

    common.logger.log_debug('Relevant Resolvers: %s' % relevant)
    return relevant

def resolve(web_url, return_all=False, subs=False):
    """
    Resolve a web page to a media stream.

    Args:
        web_url (str): A URL to a web page associated with a piece of media content.
        return_all (bool): Return all available streams instead of just one
        subs (bool): Include subtitles if available

    Returns:
        If the web_url could be resolved, a string containing the direct
        URL to the media file, if not, returns False.
    """
    if subs:
        source = HostedMediaFile(url=web_url, subs=subs)
    elif return_all:
        source = HostedMediaFile(url=web_url, return_all=return_all)
    else:
        source = HostedMediaFile(url=web_url)
    return source.resolve()

def filter_source_list(source_list):
    """
    Takes a list of HostedMediaFiles and removes those that can't be resolved.
    """
    return [source for source in source_list if source]

def choose_source(sources):
    """
    Given a list of HostedMediaFile representing web pages that are
    thought to be associated with media content this function checks which are
    playable and if there are more than one it automatically chooses the first one
    in standalone mode.
    """
    sources = filter_source_list(sources)
    if not sources:
        common.logger.log_warning('no playable streams found')
        return False
    elif len(sources) == 1:
        return sources[0]
    else:
        # In standalone mode, return the first source
        common.logger.log_debug('Multiple sources found, returning first one')
        return sources[0]

def scrape_supported(html, regex=None, host_only=False):
    """
    Returns a list of links scraped from the html that are supported by resolveurl

    Args:
        html: the html to be scraped
        regex: an optional argument to override the default regex
        host_only: an optional argument if true to do only host validation vs full url validation

    Returns:
        a list of links scraped from the html that passed validation
    """
    if regex is None:
        regex = r'''href\s*=\s*['"]([^'"]+)'''
    links = []
    for match in re.finditer(regex, html):
        stream_url = match.group(1)
        host = urllib_parse.urlparse(stream_url).hostname
        if host_only:
            if host is None:
                continue

            if host in host_cache:
                if host_cache[host]:
                    links.append(stream_url)
                continue
            else:
                hmf = HostedMediaFile(host=host, media_id='dummy')  # use dummy media_id to allow host validation
        else:
            hmf = HostedMediaFile(url=stream_url)

        is_valid = hmf.valid_url()
        host_cache[host] = is_valid
        if is_valid:
            links.append(stream_url)
    return links

def display_settings():
    """
    Opens the settings dialog for resolveurl and its plugins.
    In standalone mode, this just prints the current settings.
    """
    print("Current ResolveURL Settings:")
    for key, value in common._settings.items():
        print(f"  {key}: {value}")

def cleanup_settings():
    """
    Clean up old resolver settings that are no longer supported.
    """
    # In standalone mode, just return True
    return True