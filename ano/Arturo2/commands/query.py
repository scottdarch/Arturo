#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from ano.Arturo2.commands.base import Command


# +---------------------------------------------------------------------------+
# | Boards
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
        environment = self.getEnvironment()
        packages = environment.getPackages()
        for _, package in packages.iteritems():
            platforms = package.getPlatforms()
            for _, platform in platforms.iteritems():
                boards = platform.getBoards()
                for board in boards:
                    console.printToUserFromCommand(self, str(board))
