#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from __builtin__ import classmethod
import os
import re

from arturo import SearchPathAgent, SearchPath, Arduino15PackageSearchPathAgent, parsers, \
    ConfigurationHeaderAggregator, ConfigurationSourceAggregator

# +---------------------------------------------------------------------------+
# | LibrarySearchAggregator
# +---------------------------------------------------------------------------+
class LibrarySearchAggregator(Arduino15PackageSearchPathAgent):

    def __init__(self, console):
        super(LibrarySearchAggregator, self).__init__(SearchPath.ARTURO2_HEADER_FILEEXT, console, followLinks=True)
        self._console = console

    def onVisitPackage(self, parentPath, rootPath, packageName, filename):
        self._addResult([parentPath, packageName, filename])
        return SearchPathAgent.KEEP_GOING


# +---------------------------------------------------------------------------+
# | Library
# +---------------------------------------------------------------------------+
class Library(object):
    
    PROPERTIES_FILE = "library.properties"
    # Pattern to match a string which is either a major.minor version or a major.minor.patch version.
    VERSION_NUMBER_PATTERN = re.compile('^(\d+\.){1,2}\d$')
    
    IMPLIED_LIBRARY_VERSION = "1.0"

    @classmethod
    def libNameHasVersion(cls, libraryName):
        if not libraryName:
            return False
        
        lastDash = libraryName.rfind('-')
        return lastDash != -1 and Library.VERSION_NUMBER_PATTERN.match(libraryName[lastDash+1:])
            
    @classmethod
    def libNameAndVersion(cls, libraryName):
        if not libraryName:
            raise RuntimeError("None passed in for libraryName")
        
        lastDash = libraryName.rfind('-')
        if lastDash == -1:
            return (libraryName, cls.IMPLIED_LIBRARY_VERSION)
        else:
            if Library.VERSION_NUMBER_PATTERN.match(libraryName[lastDash+1:]):
                return (libraryName[:lastDash], libraryName[lastDash+1:])
            else:
                return (libraryName, cls.IMPLIED_LIBRARY_VERSION)

    @classmethod
    def libNameFromNameAndVersion(cls, name, version):
        if version is None or not Library.VERSION_NUMBER_PATTERN.match(version):
            return name
        else:
            return "{}-{}".format(name, version)

    @classmethod
    def fromDir(cls, environment, fqLibraryDir, console, platform):
        
        libraryName = os.path.basename(fqLibraryDir)
        for sourceFolder in SearchPath.ARTURO2_PROJECT_SOURCE_FOLDERS:
            for headerExt in SearchPath.ARTURO2_HEADER_FILEEXT:
                libraryHeader = os.path.abspath(os.path.join(fqLibraryDir, sourceFolder, "{}.{}".format(libraryName, headerExt)))
                if os.path.isfile(libraryHeader):
                    propertiesFilePath = os.path.join(fqLibraryDir, Library.PROPERTIES_FILE)
                    if os.path.isfile(propertiesFilePath):
                        libraryVersion = parsers.ArduinoKeyValueParser.parse(propertiesFilePath, dict(), console=console)['version']
                    else:
                        libraryVersion = None
                    return Library(libraryName, environment, console, libraryVersion, os.path.dirname(libraryHeader), libraryPlatform=platform)

        raise ValueError(_("{0} is not a well formed library.".format(fqLibraryDir)))

    def __init__(self, libraryName, environment, console, libraryVersion=None, libraryPath=None, libraryPlatform=None):
        super(Library, self).__init__()
        if libraryName is None or len(libraryName) == 0:
            raise ValueError("Library name cannot be empty or missing.")
            
        self._headers = None
        self._headerPaths = None
        self._sources = None
        self._environment = environment
        self._console = console
        nameAndVersion = Library.libNameAndVersion(libraryName)
        self._name = nameAndVersion[0]
        self._libraryVersion = nameAndVersion[1] if libraryVersion is None else libraryVersion
        self._name_and_version = self.libNameFromNameAndVersion(self._name, self._libraryVersion)
        self._path = libraryPath
        self._platform = libraryPlatform

    def __str__(self):
        return self._name_and_version

    def getName(self):
        return self._name
    
    def getVersion(self):
        return self._libraryVersion
    
    def getNameAndVersion(self):
        return self._name_and_version
    
    def getEnvironment(self):
        return self._environment

    def getPath(self):
        return self._path
    
    def getPlatform(self):
        return self._platform
    
    def getHeaders(self, dirnameonly=False):
        headers = self._headerPaths if (dirnameonly) else self._headers
        if headers is None and self._path is not None:
            if self._headers is None:
                self._headers = self.getEnvironment().getSearchPath().scanDirs(
                        self._path, 
                        ConfigurationHeaderAggregator(self, 
                                                      self._console,
                                                      exclusions=SearchPath.ARTURO2_LIBRARY_EXAMPLE_FOLDERS)).getResults()
            if dirnameonly and self._headerPaths is None:
                paths = set()
                for header in self._headers:
                    paths.add(os.path.dirname(header))
                self._headerPaths = list(paths)

            headers = self._headerPaths if (dirnameonly) else self._headers

        return headers

    def hasSource(self):
        return (len(self.getSources()) > 0)

    def getSources(self):
        if self._sources is None:
            self._sources = self.getEnvironment().getSearchPath().scanDirs(
                 self._path, ConfigurationSourceAggregator(self, self._console, exclusions=SearchPath.ARTURO2_LIBRARY_EXAMPLE_FOLDERS)).getResults()
        return self._sources
