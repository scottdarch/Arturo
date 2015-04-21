#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from ano import __app_name__, __version__
from ano.Arturo2.commands.base import Command, ProjectCommand


# +---------------------------------------------------------------------------+
# | Version
# +---------------------------------------------------------------------------+
class Version(Command):
    '''
    Get versioning information for Arturo/ano.
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
        self.getConsole().printToUserFromCommand(self, _('{} {}'.format(__app_name__, __version__)))
        
# +---------------------------------------------------------------------------+
# | Init
# +---------------------------------------------------------------------------+
class Init(ProjectCommand):
    '''
    Safe initialization of a project with the Arturo generated makefile. Once this command completes
    the project should be buildable using make.
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
        self.getProject().initProjectDir()
