#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from ano import i18n
from ano.Arturo2.commands.base import Command


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
                toolchains = package.getToolChains()
                for name, toolchain in toolchains.iteritems():  # @UnusedVariable
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
class List_boards(Command):
    '''
    List all known board types.
    This command will probably go away. We are working towards a more complete
    query syntax that may be encapsulated in a single Query command.
    '''
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
