#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from __builtin__ import classmethod
import os
import re

from arturo import SearchPathAgent, SearchPath, Arduino15PackageSearchPathAgent, KeySortedDict, parsers, \
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
    # Pattern to match a string which is either a major.minor version or a major.minor.patch version.
    VERSION_NUMBER_PATTERN = re.compile('^(\d+\.){1,2}\d$')
    
    IMPLIED_LIBRARY_VERSION = "1.0"

    @classmethod
    def libNameAndVersion(cls, libraryName):
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
    def fromDir(cls, environment, fqLibraryDir, console):
        
        libraryName = os.path.basename(fqLibraryDir)
        for sourceFolder in SearchPath.ARTURO2_PROJECT_SOURCE_FOLDERS:
            for headerExt in SearchPath.ARTURO2_HEADER_FILEEXT:
                libraryHeader = os.path.abspath(os.path.join(fqLibraryDir, sourceFolder, "{}.{}".format(libraryName, headerExt)))
                if os.path.isfile(libraryHeader):
                    propertiesFilePath = os.path.join(fqLibraryDir, Library.PROPERTIES_FILE)
                    if os.path.isfile(propertiesFilePath):
                        libraryVersions = KeySortedDict()
                        libraryVersion = parsers.ArduinoKeyValueParser.parse(propertiesFilePath, dict(), console=console)
                        libraryVersions[libraryVersion['version']] = libraryVersion
                    else:
                        libraryVersions = None
                    return Library(libraryName, environment, console, libraryVersions, os.path.dirname(libraryHeader))

        raise ValueError(_("{0} is not a well formed library.".format(fqLibraryDir)))

    def __init__(self, libraryName, environment, console, libraryVersions=None, libraryPath=None):
        super(Library, self).__init__()
        if libraryName is None or len(libraryName) == 0:
            raise ValueError("Library name cannot be empty or missing.")
            
        self._headers = None
        self._environment = environment
        self._console = console
        nameAndVersion = Library.libNameAndVersion(libraryName)
        self._name = nameAndVersion[0]
        synthenticVersion = nameAndVersion[1]
            
        if libraryVersions is None:
            self._libraryVersions = KeySortedDict()
            self._libraryVersions[synthenticVersion] = {'version' : synthenticVersion, "syntheticVersion": True}
        else:
            self._libraryVersions = libraryVersions
        self._path = libraryPath

    def getName(self):
        return self._name
    
    def getEnvironment(self):
        return self._environment
    
    def getVersions(self):
        return self._libraryVersions

    def hasVersion(self, version):
        return self._libraryVersions.has_key(version)

    def getHeaders(self, version):
        if self._headers is None:
            if self._path is None:
                self._headers = []
            else:
                self._headers = self.getEnvironment().getSearchPath().scanDirs(
                        self._path, ConfigurationHeaderAggregator(self, self._console, exclusions=SearchPath.ARTURO2_LIBRARY_EXAMPLE_FOLDERS)).getResults()
        return self._headers


