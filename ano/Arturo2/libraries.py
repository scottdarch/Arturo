#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from ano.Arturo2 import SearchPathAgent, SearchPath, Arduino15PackageSearchPathAgent


# 1. scan headers for include names
# 2. match include names to known libraries
# 1. search known library search paths for library/library.h
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
    
    def __init__(self, libraryName, environment, searchPath, console, libraryVersions):
        super(Library, self).__init__()
        self._environment = environment
        self._console = console
        self._name = libraryName
        self._searchPath = searchPath
        self._libraryVersions = libraryVersions

    def getName(self):
        return self._name
    
    def getEnvironment(self):
        return self._environment
    
    def getVersions(self):
        return self._libraryVersions

