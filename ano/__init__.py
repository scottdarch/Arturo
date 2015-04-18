
from distutils.util import strtobool
import os
import string

__app_name__ = 'ano'
__version__ = '2.0.0'

# +---------------------------------------------------------------------------+
# | Console
# +---------------------------------------------------------------------------+
class Console(object):
    
    def __init__(self):
        super(Console, self).__init__()
        
    def printDebug(self, message):
        print message
        
    def printVerbose(self, message):
        print message
        
    def askYesNoQuestion(self, question):
        response = raw_input(self.colourize(question, 'red'))
        return strtobool(response)
    
    def colourize(self, text, colour):
        if string.lower(colour) in ('red'):
            return "\x1b[31m" + text + "\x1b[0m"
        return text