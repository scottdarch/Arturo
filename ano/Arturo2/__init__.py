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

from ano.Arturo2.parsers import ArduinoKeyValueParser
from _pyio import __metaclass__


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
    def onVisitArgParser(self, parser):
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

# +---------------------------------------------------------------------------+
# | SearchPathAgent
# +---------------------------------------------------------------------------+
class SearchPathAgent(object):
    
    KEEP_GOING = 1
    DONE = 0
    DONE_WITH_THIS_DIR = 2
    
    __metaclass__ = ABCMeta
    
    def __init__(self, console, useDefaultExcludes=True, followLinks=False):
        super(SearchPathAgent, self).__init__()
        self._console = console
        self._visitedDirMemopad = set()
        self._followLinks = followLinks
        self._useDefaultExcludes = useDefaultExcludes
        
    def getFollowLinks(self):
        return self._followLinks

    def getUseDefaultExcludes(self):
        return self._useDefaultExcludes

    def getVisitedDirMemopad(self):
        return self._visitedDirMemopad
    
    def onVisitFile(self, parentPath, rootPath, containingFolderName, filename, fqFilename):
        return SearchPathAgent.KEEP_GOING
    
    def onVisitDir(self, parentPath, rootPath, foldername, fqFolderName, canonicalPath):
        return SearchPathAgent.KEEP_GOING
    
# +---------------------------------------------------------------------------+
# | SearchPath
# +---------------------------------------------------------------------------+
class SearchPath(object):
    
    ARDUINO15_PACKAGES_PATH = "packages"
    ARDUINO15_TOOLS_PATH = "tools"
    ARDUINO15_HARDWARE_PATH = "hardware"
    ARDUINO15_PATH = [os.path.expanduser("~/Library/Arduino15")]
    
    ARTURO2_BUILDDIR_NAME = ".build_ano2"
    
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

    def findFirstFileOfNameOrThrow(self, fileNames, genericName):
        for name in fileNames:
            packageIndexPath = self._findFirstOrNone(name, os.path.isfile)
            if packageIndexPath is not None:
                return packageIndexPath

        raise MissingRequiredFileException(self._searchPath, fileNames, genericName)

    def findFile(self, filename):
        return self._findFirstOrNone(filename, os.path.isfile)
    
    def findDir(self, relativepath):
        return self._findFirstOrNone(relativepath, os.path.isdir)

    def scanDirs(self, path, searchAgent):
        if searchAgent is None or not isinstance(searchAgent, SearchPathAgent):
            raise ValueError("You must provide a SearchPathAgent object to use the scanDirs method.")
        parentPath = os.path.realpath(os.path.join(path, os.path.pardir))
        canonicalPath = os.path.realpath(path)
        self._scanDirsRecursive(parentPath, path, os.path.basename(path), canonicalPath, searchAgent)
        return searchAgent

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _isExcludedByDefault(self, name):
        for matcher in self._compiledScmExcludes:
            if matcher.match(name):
                return True
        return False

    def _scanDirsRecursive(self, parentPath, folderPath, folderName, canonicalRoot, searchAgent):
        '''
        Cycle safe, recursive file tree search function.
        '''
        visitedMemopad = searchAgent.getVisitedDirMemopad()
        visitedMemopad.add(canonicalRoot)

        dirThings = os.listdir(folderPath)
        useDefaultExcludes = searchAgent.getUseDefaultExcludes()

        dirsToTraverse = []
        for name in dirThings:
            if useDefaultExcludes and self._isExcludedByDefault(name):
                if self._console is not None:
                    self._console.printVerbose("Skipping {} by default.".format(name))
                continue

            fullPath = os.path.join(folderPath, name)
            if os.path.isdir(fullPath):
                canonicalDir = os.path.realpath(fullPath)
                resultOfVisit = searchAgent.onVisitDir(parentPath, folderPath, name, fullPath, canonicalDir)
                if resultOfVisit != SearchPathAgent.KEEP_GOING:
                    return resultOfVisit

                if (searchAgent.getFollowLinks() or not os.path.islink(fullPath)) and canonicalDir not in visitedMemopad:
                    dirsToTraverse.append([fullPath, name, canonicalDir])

            else:
                resultOfVisit = searchAgent.onVisitFile(parentPath, folderPath, folderName, name, fullPath)
                if resultOfVisit != SearchPathAgent.KEEP_GOING:
                    return resultOfVisit

        for dirPath, dirName, canonicalDirPath in dirsToTraverse:
            result = self._scanDirsRecursive(folderPath, dirPath, dirName, canonicalDirPath, searchAgent)
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
    
    PREFERENCE_FILE_NAMES = ["preferences.txt", "ano.ini", ".anorc"]
    
    def __init__(self, searchPath, console):
        super(Preferences, self).__init__()
        self._searchPath = searchPath
        self._console = console
        self._prefs = None
        
    def get(self, key, defaultValue):
        return self._getPreferences().get(key, defaultValue)
    
    def __getitem__(self, key):
        return self._getPreferences()[key]

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _getPreferences(self):
        if self._prefs is not None:
            return self._prefs
        
        preferenceFilePath = self._searchPath.findFirstFileOfNameOrThrow(Preferences.PREFERENCE_FILE_NAMES, "preferences")
        self._prefs = ArduinoKeyValueParser.parse(preferenceFilePath, dict(), None, None, self._console)
        
        return self._prefs
