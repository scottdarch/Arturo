#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from ano.Arduino15.commands.base import Command


class Init(Command):
    '''
    Safe initialization of a project with the Arturo generated makefile. Once this command completes
    the project should be buildable using make.
    '''
    
    def __init__(self, environment):
        super(Init, self).__init__(environment)
        
    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def run(self, args):
        self.getEnvironment().getInferredProject().initProjectDir()
        
    # +-----------------------------------------------------------------------+
    # | Command : ARGPARSE API
    # +-----------------------------------------------------------------------+
    def getHelpText(self):
        return None
    
    def onVisitArgParser(self, parser):
        super(Init, self).onVisitArgParser(parser)
