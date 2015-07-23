#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

import distutils.version
import re

from arturo import i18n
from arturo.commands.base import Command, ProjectCommand, ConfiguredCommand


_ = i18n.language.ugettext

# +---------------------------------------------------------------------------+
# | list-tools
# +---------------------------------------------------------------------------+
class List_tools(Command):
    '''
    List all known board types.
    This command will probably go away. We are working towards a more complete
    query syntax that may be encapsulated in a single Query command.
    '''
    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('List all known tools available in the environment.'))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        None
    
    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        console = self.getConsole()
        try:
            console.pushContext()
            environment = self.getEnvironment()
            packages = environment.getPackages()
            for package in packages.itervalues():
                console.printInfo(package.getName())
                console.shift()
                toolchains = package.getToolChains()
                for versions in toolchains.itervalues():
                    for toolchain in versions.itervalues():
                        console.printInfo(_("{0} from {1}, version {2}.".format(toolchain.getName(), package.getName(), toolchain.getVersion())))
                        console.shift()
                        system = toolchain.getHostToolChain()
                        if system:
                            localpath = system.getPath()
                            if localpath is None:
                                console.printInfo(_("{0} tools are available from {1}.".format(system.getHost(), system.getUrl())))
                            else:
                                console.printInfo(_("{0} tools are installed under {1}".format(system.getHost(), localpath)))
                        else:
                            console.printInfo(_("No known tools for host {0}.".format(toolchain.getCurrentHostName())))
                        console.unshift()
                console.unshift()
        finally:
            console.popContext()

# +---------------------------------------------------------------------------+
# | list-boards
# +---------------------------------------------------------------------------+
class List_libraries(ConfiguredCommand):
    '''
    List all known libraries
    '''
    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('List all known Arduino libraries available in the environment.'))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        None
    
    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        config = self.getConfiguration()
        console = self.getConsole()
        try:
            console.pushContext()

            console.printInfo(_("System Libraries"))
            console.shift()
            self._emitLibraryList(self.getEnvironment().getLibraries())
            console.unshift()

            console.printInfo(_("Platform Libraries"))
            console.shift()
            self._emitLibraryList(config.getPlatform().getLibraries())
            console.unshift()

            console.printInfo(_("Project Libraries"))
            console.shift()
            self._emitLibraryList(config.getProject().getLibraries())
        finally:
            console.popContext()

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _emitLibraryList(self, librariesDict):
        console = self.getConsole()
        for libraryVersions in librariesDict.itervalues():
            for libraryVersion in sorted(libraryVersions, distutils.version.LooseVersion, reverse=True):
                library = libraryVersions[libraryVersion]
                platform = library.getPlatform()
                if platform:
                    console.printInfo(_("{} -> {}".format(library.getNameAndVersion(), platform.getName())))
                else:
                    console.printInfo(_("{} -> {}".format(library.getNameAndVersion(), library.getPath())))


# +---------------------------------------------------------------------------+
# | list-boards
# +---------------------------------------------------------------------------+
class List_boards(Command):
    '''
    List all known board types.
    This command will probably go away. We are working towards a more complete
    query syntax that may be encapsulated in a single Query command.
    '''
    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('List all known board types defined in the environment.'))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        None
    
    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        console = self.getConsole()
        try:
            console.pushContext()
            environment = self.getEnvironment()
            packages = environment.getPackages()
            for name, package in packages.iteritems():  # @UnusedVariable
                console.printInfo(package.getName())
                console.shift()
                platforms = package.getPlatforms()
                for name, platform in platforms.iteritems():  # @UnusedVariable
                    console.printInfo(platform.getName())
                    console.shift()
                    console.printInfo(_("Tools"))
                    console.shift()
                    for tools in platform.getToolChain():
                        console.printInfo(_("{0} from {1}, version {2}.".format(tools.getName(), tools.getPackage().getName(), tools.getVersion())))
                    console.unshift()
                    console.printInfo(_("Boards"))
                    boards = platform.getBoards()
                    console.shift()
                    for name, board in boards.iteritems():  # @UnusedVariable
                        console.printInfo(board.getName())
                    console.unshift()
                    console.unshift()
                console.unshift()
        finally:
            console.popContext()

# +---------------------------------------------------------------------------+
# | list-platform-data
# +---------------------------------------------------------------------------+
class List_platform_data(ProjectCommand):
    '''
    List all known board types.
    This command will probably go away. We are working towards a more complete
    query syntax that may be encapsulated in a single Query command.
    '''
    def __init__(self, environment, project, console):
        super(List_platform_data, self).__init__(environment, project, console)
        self._filter = None
        self._package = None
        self._platform = None
        self._board = None

    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Interactive query to list build data available for boards.'))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument("--filter")
        parser.add_argument("--package")
        parser.add_argument("--platform")
        parser.add_argument("--board")

    def onVisitArgs(self, args):
        self._filter = re.compile(args.filter) if args.filter else None
        self._package = args.package.lower() if args.package else None
        self._platform = args.platform.lower() if args.platform else None
        self._board = args.board.lower() if args.board else None

    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        console = self.getConsole()
        try:
            console.pushContext()
            environment = self.getEnvironment()
            packages = environment.getPackages()
            packageList = [[key] for key in packages.keys()]
            package = console.askPickOneFromList(_("Select a package"), packageList, responseList=packages.values()) \
                if self._package is None else packages[self._package]
            
            platforms = package.getPlatforms()
            platformList = [[platform] for platform in platforms.keys()]
            
            platform = console.askPickOneFromList(_("Select a platform"), platformList, responseList=platforms.values()) \
                if self._platform is None else platforms[self._platform]
            
            boards = platform.getBoards()
            
            boardList = [[board] for board in boards.keys()]
            
            board = console.askPickOneFromList(_("Select a board"), boardList, responseList=boards.values()) \
                if self._board is None else boards[self._board]
            
            buildInfo = board.processBuildInfo()
            console.printInfo(board.getPath())
            for key, value in buildInfo.iteritems():
                if self._filter is None or self._filter.search(key):
                    console.printInfo(_("{0:<40} - {1}".format(key, value)))
        finally:
            console.popContext()
