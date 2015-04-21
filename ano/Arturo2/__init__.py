#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import os

from ano.Arturo2.parsers import KeyValueParser

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
        
    def __str__(self):
        return self['name']

# +---------------------------------------------------------------------------+
# | SearchPath
# +---------------------------------------------------------------------------+
class SearchPath(object):
    
    def __init__(self):
        super(SearchPath, self).__init__()
        self._envpath = [os.path.expanduser("~/Library/Arduino15")]
        self._envpath += os.environ['PATH'].split(":")
        
    def findFirstFileOfNameOrThrow(self, fileNames, genericName):
        for name in fileNames:
            packageIndexPath = self.findFile(name)
            if packageIndexPath is not None:
                return packageIndexPath

        raise MissingRequiredFileException(self._searchPath, fileNames, genericName)

    def findFile(self, filename):
        if filename is None:
            raise ValueError("filename argument is required.")

        fqfn = None
        for place in self._envpath:
            possibleFqfn = os.path.join(place, filename)
            if os.path.isfile(possibleFqfn):
                fqfn = possibleFqfn
                break

        return fqfn
    
    def __str__(self):
        return str(self._envpath)
    
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
        self._prefs = KeyValueParser.parse(preferenceFilePath, dict(), None, self._console)
        
        return self._prefs
