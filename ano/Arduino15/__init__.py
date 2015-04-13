#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from collections import OrderedDict
import os

from ano.Arduino15.parsers import KeyValueParser


class MissingRequiredFileException(BaseException):
    
    def __init__(self, searchPath, filenames, genericName):
        super(MissingRequiredFileException, self).__init__(genericName)
        # TODO: format a "looked in [searchPath] for [filenames]" message

class NamedOrderedDict(OrderedDict):

    def __init__(self, name):
        super(NamedOrderedDict, self).__init__()
        self._name = name;
        
    def __str__(self):
        return self._name

# +---------------------------------------------------------------------------+
# | SearchPath
# +---------------------------------------------------------------------------+
class SearchPath(object):
    
    def __init__(self):
        super(SearchPath, self).__init__()
        self._envpath = [os.path.expanduser("~/Library/Arduino15")]
        self._envpath += os.environ['PATH'].split(":")
        
    def findFirstFileOfNameOrThrow(self, fileNames):
        for name in fileNames:
            packageIndexPath = self.findFile(name)
            if packageIndexPath is not None:
                return packageIndexPath

        raise MissingRequiredFileException(self._searchPath, fileNames, "package index")

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

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _getPreferences(self):
        if self._prefs is not None:
            return self._prefs
        
        preferenceFilePath = self._searchPath.findFirstFileOfNameOrThrow(Preferences.PREFERENCE_FILE_NAMES)
        self._prefs = KeyValueParser.parse(preferenceFilePath, dict(), None, self._console)
        
        return self._prefs
