#  _____     _
# |  _  |___| |_ _ _ ___ ___
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import os
import re

from arturo import parsers


__app_name__ = 'ano'
__lib_name__ = 'arturo'
__version__ = '2.0.0'
# some libraries have coded against -DARDUINO as an integer. We use this both to supply an integer
# and to use newer branches where the "1.0.x" line was handled by this
# macro (e.g. #if ARDUINO > 100).
__version_num__ = 200


# +---------------------------------------------------------------------------+
# | Runnable
# +---------------------------------------------------------------------------+
class Runnable(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def run(self):
        None

# +---------------------------------------------------------------------------+
# | ArgumentVisitor
# +---------------------------------------------------------------------------+


class ArgumentVisitor(object):

    __metaclass__ = ABCMeta

    @abstractmethod
    def onVisitArgParser(self, subparsers):
        None

    def onVisitArgs(self, args):
        None

# +---------------------------------------------------------------------------+
# | COMMON TYPES
# +---------------------------------------------------------------------------+


class MissingRequiredFileException(BaseException):

    def __init__(self, searchPath, filenames, genericName):
        super(MissingRequiredFileException, self).__init__(genericName)
        # TODO: format a "looked in [searchPath] for [filenames]" message


class NamedOrderedDict(OrderedDict):

    def __init__(self, name):
        super(NamedOrderedDict, self).__init__()
        self['name'] = name

    def getName(self):
        return self['name']

    def __str__(self):
        return self.getName()


class KeySortedDict(OrderedDict):
    '''
    TODO: implement me
    '''

    def __init__(self, ascending=True):
        super(KeySortedDict, self).__init__()
        self._ascending = ascending


# +---------------------------------------------------------------------------+
# | SearchPathAgent
# +---------------------------------------------------------------------------+
class SearchPathAgent(object):

    KEEP_GOING = 1
    DONE = 0
    DONE_WITH_THIS_DIR = 2

    __metaclass__ = ABCMeta

    def __init__(self, console, exclusions=None, useDefaultExcludes=True, followLinks=False):
        super(SearchPathAgent, self).__init__()
        self._console = console
        self._visitedDirMemopad = set()
        self._followLinks = followLinks
        self._useDefaultExcludes = useDefaultExcludes
        self._exclusions = exclusions
        self._resultList = list()
        self._resultSet = set()

    def getFollowLinks(self):
        return self._followLinks

    def getUseDefaultExcludes(self):
        return self._useDefaultExcludes

    def getVisitedDirMemopad(self):
        return self._visitedDirMemopad

    def getExclusions(self):
        return self._exclusions

    def onVisitFile(self, parentPath, rootPath, containingFolderName, filename, fqFilename):
        return SearchPathAgent.KEEP_GOING

    def onVisitDir(self, parentPath, rootPath, foldername, fqFolderName, canonicalPath, depth):
        return SearchPathAgent.KEEP_GOING

    def getResults(self, ordered=True):
        if ordered:
            return self._resultList
        else:
            return self._resultSet

    def hasResult(self, result):
        return (result in self._resultSet)

    # +-----------------------------------------------------------------------+
    # | PROTECTED
    # +-----------------------------------------------------------------------+
    def _getConsole(self):
        return self._console

    def _addResult(self, result):
        result_hashable = str(result)
        if result_hashable not in self._resultSet:
            self._resultSet.add(result_hashable)
            self._resultList.append(result)

# +---------------------------------------------------------------------------+
# | UTILITY AGENTS AND AGGREGATORS
# +---------------------------------------------------------------------------+


class Arduino15PackageSearchPathAgent(SearchPathAgent):
    '''
    SearchPathAgent that looks for the Arduino15 standard "[token]/[token].[extension]" pattern
    used to signify both sketch folders (e.g. sketch/sketch.ino) or library folders
    (e.g. library/library.h).
    '''

    __metaclass__ = ABCMeta

    def __init__(self, extensionSet, console, exclusions=None, useDefaultExcludes=True, followLinks=False):
        super(Arduino15PackageSearchPathAgent, self).__init__(
            console, exclusions, useDefaultExcludes, followLinks)
        self._extensionSet = extensionSet

    def onVisitFile(self, parentPath, rootPath, containingFolderName, filename, fqFilename):
        splitName = filename.split('.')
        if len(splitName) == 2 and splitName[1] in self._extensionSet:
            if containingFolderName == splitName[0]:
                return self.onVisitPackage(parentPath, rootPath, containingFolderName, filename)
        return SearchPathAgent.KEEP_GOING

    @abstractmethod
    def onVisitPackage(self, parentPath, rootPath, packageName, filename):
        pass


class ConfigurationHeaderAggregator(SearchPathAgent):

    def __init__(self, configuration, console, exclusions=None):
        super(ConfigurationHeaderAggregator, self).__init__(
            console, exclusions=exclusions, followLinks=True)
        self._configuration = configuration

    def onVisitFile(self, parentPath, rootPath, containingFolderName, filename, fqFilename):
        splitName = filename.split('.')
        if len(splitName) == 2 and splitName[1] in SearchPath.ARTURO2_HEADER_FILEEXT:
            self._addResult(fqFilename)

        return SearchPathAgent.KEEP_GOING


class ConfigurationSourceAggregator(SearchPathAgent):

    def __init__(self, configuration, console, exclusions=None):
        super(ConfigurationSourceAggregator, self).__init__(
            console, exclusions=exclusions, followLinks=True)
        self._configuration = configuration

    def onVisitFile(self, parentPath, rootPath, containingFolderName, filename, fqFilename):
        splitName = filename.split('.')
        if len(splitName) == 2 and splitName[1] in SearchPath.ARTURO2_SOURCE_FILEEXT:
            self._addResult(fqFilename)
        return SearchPathAgent.KEEP_GOING


# +---------------------------------------------------------------------------+
# | SearchPath
# +---------------------------------------------------------------------------+
class SearchPath(object):

    ARDUINO15_PACKAGES_PATH = "packages"
    ARDUINO15_TOOLS_PATH = "tools"
    ARDUINO15_HARDWARE_PATH = "hardware"
    ARDUINO15_PATH = [os.path.expanduser("~/Library/Arduino15"),
                      os.path.expanduser("~/Documents/Arduino"),
                      os.path.expanduser("~/Arduino"),
                      os.path.expanduser(
                          os.path.join("~", "My Documents", "Arduino"))
                      ]

    ARDUINO15_LIBRARY_FOLDER_NAMES = ("lib", "libraries")

    ARTURO2_BUILDDIR_NAME = ".build_ano2"

    ARTURO2_SOURCE_FILEEXT = ("cpp", "c", "ino")
    ARTURO2_HEADER_FILEEXT = ("h", "hpp")
    ARTURO2_PROJECT_SOURCE_FOLDERS = ("src", ".")
    ARTURO2_LIBRARY_EXAMPLE_FOLDERS = ("examples")

    ARTURO2_DEFAULT_SCM_EXCLUDE_PATTERNS = ["\..+",
                                            ARTURO2_BUILDDIR_NAME,
                                            ]

    def __init__(self, console):
        super(SearchPath, self).__init__()
        self._envpath = list(SearchPath.ARDUINO15_PATH)
        self._envpath += os.environ['PATH'].split(":")
        self._compiledScmExcludes = []
        self._console = console
        for patternString in SearchPath.ARTURO2_DEFAULT_SCM_EXCLUDE_PATTERNS:
            self._compiledScmExcludes.append(re.compile(patternString))

    def __str__(self):
        return str(self._envpath)

    def getPaths(self):
        return self._envpath

    def findFirstFileOfNameOrThrow(self, fileNames, genericName):
        for name in fileNames:
            packageIndexPath = self._findFirstOrNone(name, os.path.isfile)
            if packageIndexPath is not None:
                return packageIndexPath

        raise MissingRequiredFileException(
            self._searchPath, fileNames, genericName)

    def findFile(self, filename):
        return self._findFirstOrNone(filename, os.path.isfile)

    def findDir(self, relativepath):
        return self._findFirstOrNone(relativepath, os.path.isdir)

    def scanDirs(self, path, searchAgent):
        if searchAgent is None or not isinstance(searchAgent, SearchPathAgent):
            raise ValueError(
                "You must provide a SearchPathAgent object to use the scanDirs method.")
        parentPath = os.path.realpath(os.path.join(path, os.path.pardir))
        canonicalPath = os.path.realpath(path)
        self._scanDirsRecursive(
            parentPath, path, os.path.basename(path), canonicalPath, searchAgent, 0)
        return searchAgent

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _isExcludedByDefault(self, name):
        for matcher in self._compiledScmExcludes:
            if matcher.match(name):
                return True
        return False

    def _scanDirsRecursive(self, parentPath, folderPath, folderName, canonicalRoot, searchAgent, folderDepth):
        '''
        Cycle safe, recursive file tree search function.
        '''
        visitedMemopad = searchAgent.getVisitedDirMemopad()
        visitedMemopad.add(canonicalRoot)

        dirThings = os.listdir(folderPath)
        exclusions = searchAgent.getExclusions()
        useDefaultExcludes = searchAgent.getUseDefaultExcludes()

        dirsToTraverse = []
        for name in dirThings:
            if useDefaultExcludes and self._isExcludedByDefault(name):
                if self._console is not None:
                    self._console.printVerbose(
                        "Skipping {} by default.".format(name))
                continue

            if exclusions is not None and name in exclusions:
                if self._console is not None:
                    self._console.printVerbose(
                        "Skipping {} by exclusion rule.".format(name))
                continue

            fullPath = os.path.join(folderPath, name)
            if os.path.isdir(fullPath):
                canonicalDir = os.path.realpath(fullPath)
                resultOfVisit = searchAgent.onVisitDir(
                    parentPath, folderPath, name, fullPath, canonicalDir, folderDepth)
                if resultOfVisit != SearchPathAgent.KEEP_GOING:
                    return resultOfVisit

                if (searchAgent.getFollowLinks() or not os.path.islink(fullPath)) and canonicalDir not in visitedMemopad:
                    dirsToTraverse.append([fullPath, name, canonicalDir])

            else:
                resultOfVisit = searchAgent.onVisitFile(
                    parentPath, folderPath, folderName, name, fullPath)
                if resultOfVisit != SearchPathAgent.KEEP_GOING:
                    return resultOfVisit

        for dirPath, dirName, canonicalDirPath in dirsToTraverse:
            result = self._scanDirsRecursive(
                folderPath, dirPath, dirName, canonicalDirPath, searchAgent, folderDepth + 1)
            if result == SearchPathAgent.DONE:
                return result

        return SearchPathAgent.KEEP_GOING

    def _findFirstOrNone(self, pathelement, compariator):
        if pathelement is None:
            raise ValueError("pathelement argument is required.")

        foundPath = None
        for place in self._envpath:
            possiblePath = os.path.join(place, pathelement)
            if compariator(possiblePath):
                foundPath = possiblePath
                break

        return foundPath

# +---------------------------------------------------------------------------+
# | Preferences
# +---------------------------------------------------------------------------+


class Preferences(object):

    PREFERENCE_FILE_NAMES = ["preferences.txt", "arturo.ini", ".anorc"]

    def __init__(self, searchPath, console):
        super(Preferences, self).__init__()
        self._searchPath = searchPath
        self._console = console
        self._prefs = None

    def get(self, key, defaultValue):
        return self._getPreferences().get(key, defaultValue)

    # +-----------------------------------------------------------------------+
    # | PYTHON DATA MODEL
    # +-----------------------------------------------------------------------+
    def __getitem__(self, key):
        return self._getPreferences()[key]

    def __setitem__(self, key, value):
        self._getPreferences()[key] = value

    def __iter__(self):
        return self._getPreferences().__iter__()

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _getPreferences(self):
        if self._prefs is not None:
            return self._prefs

        preferenceFilePath = self._searchPath.findFirstFileOfNameOrThrow(
            Preferences.PREFERENCE_FILE_NAMES, "preferences")
        self._prefs = parsers.ArduinoKeyValueParser.parse(
            preferenceFilePath, dict(), None, None, self._console)

        return self._prefs
