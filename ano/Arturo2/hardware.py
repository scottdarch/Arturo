#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from _pyio import __metaclass__
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import os
from string import upper

from ano import __lib_name__, __version__
from ano.Arturo2 import NamedOrderedDict, SearchPathAgent, SearchPath
from ano.Arturo2.parsers import ArduinoKeyValueParser


# +---------------------------------------------------------------------------+
# | BoardMacroResolver
# +---------------------------------------------------------------------------+
class BoardMacroResolver:
    '''
    Functor type used by the Board's processBuildInfo method to expand Arduino15 style macro strings.
    '''
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def __call__(self, namespace, macro):
        '''
        Invoked by a macro expansion routine with an Arduino15 style macro (e.g.
        {compiler.path}).
        
        @param namespace: A namespace within which the macro is unique.
        @param macro: The macro name without the enclosing curly braces.
        @return: text to replace the macro with.
        @raise KeyError: If this resolver could not expand the macro.
        '''
        pass
    
# +---------------------------------------------------------------------------+
# | Board
# +---------------------------------------------------------------------------+

class Board(NamedOrderedDict):
    
    PLATFORM_FILENAME = "platform.txt"
    
    def __init__(self, name, platform, console):
        super(Board, self).__init__(name)
        self._platform = platform
        self._console = console
        self._rawPlatformData = None
        self._core = None
        self._variant = None

    def getPlatform(self):
        return self._platform

    def getCore(self):
        if self._core is None:
            coreName = self['build.core']
            self._core = self.getPlatform().getCores()[coreName]
        return self._core
    
    def getVariant(self):
        if self._variant == -1:
            return None
        if self._variant is None:
            try:
                variantName = self['build.variant']
            except KeyError:
                self._console.printVerbose("Board {} does not have a variant.".format(self.getName()))
                self._variant = -1
                return None
            self._variant = self.getPlatform().getVariants()[variantName]
        return self._variant

    def processBuildInfo(self, unexpandedMacroResolver=None, elideKeysForMissingValues=False):
        '''
        Process the key/value data found in this board's platform.txt file expanding the Arduino15 style
        macros (e.g. {this.is.a.macro}) using a chain of macro resolvers.
        
        @param unexpandedMacroResolver: A BoardMacroResolver to be invoked if the build-in resolver
                                        is unable to expand a macro.
        @param elideKeysForMissingValues: If True then any macros that are not expanded will have the macro
                                          keys removed from the final output. If False then the macro keys
                                          will remain unexpanded (i.e. "{not.found.macro}" if not elideKeysForMissingValues else "")
        '''
        if self._rawPlatformData is None:
            self._rawPlatformData = OrderedDict()
            ArduinoKeyValueParser.parse(os.path.join(self._platform.getPlatformPath(), Board.PLATFORM_FILENAME), self._rawPlatformData, None, None, self._console)

        boardBuildMetadata = OrderedDict(self._rawPlatformData)
        macroResolverChain = BoardPlatformMacroResolver(self, boardBuildMetadata, unexpandedMacroResolver, self._console)
        
        for key, value in boardBuildMetadata.items():
            boardBuildMetadata[key] = ArduinoKeyValueParser.expandMacros(key, macroResolverChain, value, elideKeysForMissingValues, self._console)
        
        return boardBuildMetadata


class BoardPlatformMacroResolver(BoardMacroResolver):
    '''
    BoardMacroResolver used as the first responder for all Arduino15 style macros found by the Board::processBuildInfo
    method.
    '''
    def __init__(self, board, boardBuildMetadata, nextResolver=None, console=None):
        self._boardBuildMetadata = boardBuildMetadata
        self._board = board
        self._nextResolver = nextResolver
        self._console = console

    def __call__(self, namespace, macro):
        if macro == "software":
            return __lib_name__.upper()
        
        if macro == "runtime.ide.version":
            return __version__

        try:
            return self._board[macro]
        except KeyError:
            pass

        try:
            return self._boardBuildMetadata[macro]
        except KeyError:
            pass

        try:
            return self._board.getPlatform().getMetaData(macro)
        except KeyError:
            pass
        
        # Anything prefixed with "build" should either be handled in platform.txt itself or should
        # come from the configured platform metadata.
        if macro.startswith('build.'):
            try:
                return self._board.getPlatform().getMetaData(macro[6:])
            except KeyError:
                pass

        if self._nextResolver is not None:
            return self._nextResolver(namespace, macro)
        else:
            raise KeyError()

# +---------------------------------------------------------------------------+
# | Core
# +---------------------------------------------------------------------------+
class CoreHeaderAggregator(SearchPathAgent):

    def __init__(self, configuration, console):
        super(CoreHeaderAggregator, self).__init__(console, followLinks=True)
        self._configuration = configuration
        self._console = console
        self._headers = list()

    def getResults(self):
        return self._headers

    def onVisitFile(self, parentPath, rootPath, containingFolderName, filename, fqFilename):
        splitName = filename.split('.')
        if len(splitName) == 2 and splitName[1] in SearchPath.ARTURO2_HEADER_FILEEXT:
            self._headers.append(fqFilename)
        return SearchPathAgent.KEEP_GOING
    
class Core(object):
    
    def __init__(self, name, path, platform, console):
        super(Core, self).__init__()
        self._name = name
        self._path = path
        self._console = console
        self._platform = platform
        self._headers = None

    def getName(self):
        return self._name

    def getPlatform(self):
        return self._platform

    def getPath(self):
        return self._path
    
    def getHeaders(self):
        if self._headers is None:
            self._headers = self.getPlatform().getPackage().getEnvironment().getSearchPath().scanDirs(
                 self._path, CoreHeaderAggregator(self, self._console)).getResults()
        return self._headers

# +---------------------------------------------------------------------------+
# | Variant
# +---------------------------------------------------------------------------+
class Variant(Core):
    
    def __init__(self, name, path, platform, console):
        super(Variant, self).__init__(name, path, platform, console)

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
    CORES_FOLDER = "cores"
    VARIANTS_FOLDER = "variants"
    ARDUINO15_KNOWN_METADATA_ALIASES = { 
                                        "arch": ("architecture", upper),
                                    }
    
    @classmethod
    def _makePlatformPath(cls, rootPath, platformMetadata):
        return os.path.join(rootPath, platformMetadata['architecture'], platformMetadata['version'])
    
    @classmethod
    def ifExistsPlatform(cls, package, rootPath, searchPath, console, platformMetadata):
        platformPath = cls._makePlatformPath(rootPath, platformMetadata)
        if not os.path.isdir(platformPath):
            return None
        else:
            return cls(package, rootPath, searchPath, console, platformMetadata, platformPath)
            
    def __init__(self, package, rootPath, searchPath, console, platformMetadata, platformPath=None):
        super(Platform, self).__init__()
        self._package = package
        self._platformPath = Platform._makePlatformPath(rootPath, platformMetadata) if platformPath is None else platformPath
        self._searchPath = searchPath
        self._console = console
        self._platformMetadata = platformMetadata
        self._boards = None
        self._programmers = None
        self._platformBoardFactory = PlatformBoardFactory(self, console)
        self._toolsList = None
        self._cores = None
        self._variants = None
        self._libraries = None
        
        if not os.path.isdir(self._platformPath):
            if console:
                console.printDebug(platformMetadata)
            raise Exception("%s was not found" % (self._platformPath))

    def getPackage(self):
        return self._package

    def getToolChain(self):
        if self._toolsList is None:
            self._toolsList = list()
            for tooldeps in self._platformMetadata['toolsDependencies']:
                package = self._package.getEnvironment().getPackages()[tooldeps['packager']]
                self._toolsList.append(package.getToolChain(tooldeps['name'], tooldeps['version']))
        return self._toolsList

    def getName(self):
        return self._platformMetadata['name']

    def getArchitecture(self):
        return self._platformMetadata['architecture']

    def getPlatformPath(self):
        return self._platformPath
    
    def getBoards(self):
        if self._boards is None:
            self._boards = ArduinoKeyValueParser.parse(os.path.join(self._platformPath, Platform.BOARDS_FILENAME), 
                                                OrderedDict(), 
                                                self._platformBoardFactory, 
                                                console=self._console)
        return self._boards
    
    def getProgrammers(self):
        '''
        Returns an OrderedDict of Programmer objects read from the programmers text file.
        '''
        if self._programmers is None:
            self._programmers = ArduinoKeyValueParser.parse(os.path.join(self._platformPath, Platform.PROGRAMMERS_FILENAME), 
                                                     OrderedDict(), 
                                                     NamedOrderedDict, 
                                                     console=self._console)
        return self._programmers

    def getMetaData(self, key):
        try:
            return self._platformMetadata[key]
        except KeyError as e:
            alias = Platform.ARDUINO15_KNOWN_METADATA_ALIASES.get(key)
            if alias is not None:
                value = self._platformMetadata[alias[0]]
                transform = alias[1]
                if transform is None:
                    return value
                else:
                    return transform(value)
                
            else:
                raise e

    def getCores(self):
        if self._cores is None:
            self._cores = dict()
            coresdir = os.path.join(self.getPlatformPath(), Platform.CORES_FOLDER)
            for item in os.listdir(coresdir):
                coreitempath = os.path.join(coresdir, item)
                if os.path.isdir(coreitempath):
                    self._cores[item] = Core(item, coreitempath, self, self._console)

        return self._cores

    def getVariants(self):
        if self._variants is None:
            self._variants = dict()
            variantsdir = os.path.join(self.getPlatformPath(), Platform.VARIANTS_FOLDER)
            for item in os.listdir(variantsdir):
                variantitempath = os.path.join(variantsdir, item)
                if os.path.isdir(variantitempath):
                    self._variants[item] = Variant(item, variantitempath, self, self._console)

        return self._variants

    def getLibraries(self):
        if self._libraries is None:
            self._libraries = self._package.getEnvironment().getLibrariesFor(self._platformPath)

        return self._libraries

