#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from collections import OrderedDict
import os

from ano.Arduino15 import NamedOrderedDict
from ano.Arduino15.parsers import KeyValueParser

# +---------------------------------------------------------------------------+
# | Board
# +---------------------------------------------------------------------------+
class Board(NamedOrderedDict):
    
    PLATFORM_FILENAME = "platform.txt"
    
    def __init__(self, name, platform, console):
        super(Board, self).__init__(name)
        self._platform = platform
        self._console = console
        self._boardBuildMetadata = None
        #TODO: populate this
        self._buildVariables = dict()

    def getBuildInfo(self, extraArgs=None):
        '''
        Returns an OrdredDict of platform data for the board
        '''
        if self._boardBuildMetadata is not None:
            return self._boardBuildMetadata
    
        platform = OrderedDict()
        
        platformMacros = self._buildVariables.copy()
        platformMacros.update(self)
        
        if extraArgs is not None:
            platformMacros.update(extraArgs)
        
        KeyValueParser.parse(os.path.join(self._platform.getPlatformPath(), Board.PLATFORM_FILENAME), platform, None, self._console)
        
        for key, value in platform.items():
            platform[key] = KeyValueParser.expandMacros(platformMacros, key, value, False, self._console)
        
        self._boardBuildMetadata = platform
        return platform

# +---------------------------------------------------------------------------+
# | Platform
# +---------------------------------------------------------------------------+
class PlatformBoardFactory(object):
    def __init__(self, platform, console):
        super(PlatformBoardFactory, self).__init__()
        self._platform = platform
        self._console = console
        
    def __call__(self, name):
        return Board(name, self._platform, self._console)
        
class Platform(object):
    
    BOARDS_FILENAME = "boards.txt"
    PROGRAMMERS_FILENAME = "programmers.txt"
    
    def __init__(self, rootPath, searchPath, console, platformMetadata):
        super(Platform, self).__init__()
        
        self._platformPath = os.path.join(rootPath, platformMetadata['architecture'], platformMetadata['version'])
        self._searchPath = searchPath
        self._console = console
        self._platformMetadata = platformMetadata
        self._boards = None
        self._programmers = None
        self._platformBoardFactory = PlatformBoardFactory(self, console)
        
        if not os.path.isdir(self._platformPath):
            raise Exception("%s was not found" % (self._platformPath))

    def getPlatformPath(self):
        return self._platformPath
    
    def getBoards(self):
        if self._boards is None:
            self._boards = KeyValueParser.parse(os.path.join(self._platformPath, Platform.BOARDS_FILENAME), OrderedDict(), self._platformBoardFactory, self._console)
        return self._boards
    
    def getProgrammers(self):
        '''
        Returns an OrderedDict of Programmer objects read from the programmers text file.
        '''
        if self._programmers is None:
            self._programmers = KeyValueParser.parse(os.path.join(self._platformPath, Platform.PROGRAMMERS_FILENAME), OrderedDict(), NamedOrderedDict, self._console)
        return self._programmers
        
    # +-----------------------------------------------------------------------+
    # | PYTHON DATA MODEL
    # +-----------------------------------------------------------------------+
    def __getitem__(self, key):
        return self.getBoards()[key]
