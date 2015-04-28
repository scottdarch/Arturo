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
# | SearchPath
# +---------------------------------------------------------------------------+
def fileFilterAllFiles(fqfilepath):
        return True
    
def dirFilterNoDirs(fqdirpath):
    return False
    
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

    def findAll(self, path, fileFilter=fileFilterAllFiles, directoryFilter=dirFilterNoDirs, defaultExcludes=True, followlinks=False):
        return self._findAllRecursive(set(), path, fileFilter, directoryFilter, defaultExcludes, followlinks)

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _isExcludedByDefault(self, name):
        for matcher in self._compiledScmExcludes:
            if matcher.match(name):
                return True
        return False

    def _findAllRecursive(self, inoutResultSet, root, fileFilter, directoryFilter, defaultExcludes, followlinks, visitedMemopad=set()):
        '''
        Cycle safe, recursive file tree search function.
        '''
        visitedMemopad.add(os.path.realpath(root))

        dirThings = os.listdir(root)

        dirsToTraverse = []
        for name in dirThings:
            if self._isExcludedByDefault(name):
                if self._console is not None:
                    self._console.printVerbose("Skipping {} by default.".format(name))
                continue

            fullPath = os.path.join(root, name)
            if os.path.isdir(fullPath):
                if directoryFilter is None or directoryFilter(fullPath):
                    inoutResultSet.add(fullPath)

                if (followlinks or not os.path.islink(fullPath)) and os.path.realpath(fullPath) not in visitedMemopad:
                    dirsToTraverse.append(fullPath)

            elif fileFilter is None or fileFilter(fullPath):
                inoutResultSet.add(fullPath)

        for subdir in dirsToTraverse:
            self._findAllRecursive(inoutResultSet, subdir, fileFilter, directoryFilter, defaultExcludes, followlinks, visitedMemopad)

        return inoutResultSet
    
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
