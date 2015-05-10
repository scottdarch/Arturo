#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from __builtin__ import classmethod
import os

from ano.Arturo2 import SearchPathAgent, SearchPath, Arduino15PackageSearchPathAgent, KeySortedDict, parsers, \
    ConfigurationHeaderAggregator


# +---------------------------------------------------------------------------+
# | LibrarySearchAggregator
# +---------------------------------------------------------------------------+
class LibrarySearchAggregator(Arduino15PackageSearchPathAgent):

    def __init__(self, console):
        super(LibrarySearchAggregator, self).__init__(SearchPath.ARTURO2_HEADER_FILEEXT, console, followLinks=True)
        self._console = console
        self._headers = list()

    def getResults(self):
        return self._libraryRoots

    def onVisitPackage(self, parentPath, rootPath, packageName, filename):
        self._libraryRoots.append([parentPath, packageName, filename])
        return SearchPathAgent.KEEP_GOING


# +---------------------------------------------------------------------------+
# | Library
# +---------------------------------------------------------------------------+
class Library(object):
    
    PROPERTIES_FILE = "library.properties"
    SOURCE_FOLDERS = ("src", ".")
    EXAMPLE_FOLDERS = ("examples")

    @classmethod
    def fromDir(cls, environment, fqLibraryDir, console):
        
        libraryName = os.path.basename(fqLibraryDir)
        for sourceFolder in cls.SOURCE_FOLDERS:
            for headerExt in SearchPath.ARTURO2_HEADER_FILEEXT:
                libraryHeader = os.path.abspath(os.path.join(fqLibraryDir, sourceFolder, "{}.{}".format(libraryName, headerExt)))
                if os.path.isfile(libraryHeader):
                    libraryVersions = KeySortedDict()
                    propertiesFilePath = os.path.join(fqLibraryDir, Library.PROPERTIES_FILE)
                    if os.path.isfile(propertiesFilePath):
                        libraryVersion = parsers.ArduinoKeyValueParser.parse(propertiesFilePath, dict(), console=console)
                        libraryVersions[libraryVersion['version']] = libraryVersion
                    else:
                        libraryVersions['1.0'] = {'version' : 1.0, "syntheticVersion": True}

                    return Library(libraryName, environment, console, libraryVersions, os.path.dirname(libraryHeader))

        raise ValueError(_("{0} is not a well formed library.".format(fqLibraryDir)))

    def __init__(self, libraryName, environment, console, libraryVersions, libraryPath=None):
        super(Library, self).__init__()
        self._headers = None
        self._environment = environment
        self._console = console
        self._name = libraryName
        self._libraryVersions = libraryVersions
        self._path = libraryPath

    def getName(self):
        return self._name
    
    def getEnvironment(self):
        return self._environment
    
    def getVersions(self):
        return self._libraryVersions

    def getHeaders(self):
        if self._headers is None:
            self._headers = self.getEnvironment().getSearchPath().scanDirs(
                 self._path, ConfigurationHeaderAggregator(self, self._console)).getResults()
        return self._headers


