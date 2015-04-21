#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from distutils.util import strtobool
import string

from ano.Arturo2 import ArgumentVisitor


# +---------------------------------------------------------------------------+
# | Console
# +---------------------------------------------------------------------------+
class Console(ArgumentVisitor):
    
    def __init__(self):
        super(Console, self).__init__()
        self._loglevel = 0
        
    def printDebug(self, message):
        if self._loglevel > 0:
            print message
        
    def printVerbose(self, message):
        if self._loglevel > 1:
            print message
        
    def printToUserFromCommand(self, commandObject, message):
        print message
        
    def askYesNoQuestion(self, question):
        response = raw_input(self._colourize(question, 'red'))
        return strtobool(response)

    # +---------------------------------------------------------------------------+
    # | ArgumentVisitor
    # +---------------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument('-v', '--verbose',
                            default=False,
                            action='store_true',
                            help=_('Enable verbose logging.'))

    def onVisitArgs(self, args):
        if getattr(args, "verbose"):
            self._loglevel = 2
            self.printVerbose(_('enabling verbose logging.'))
    
    # +---------------------------------------------------------------------------+
    # | PRIVATE
    # +---------------------------------------------------------------------------+
    def _colourize(self, text, colour):
        if string.lower(colour) in ('red'):
            return "\x1b[31m" + text + "\x1b[0m"
        return text