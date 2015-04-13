__version__ = '2.0.0'

class Console(object):
    
    def __init__(self):
        super(Console, self).__init__()
        
    def printDebug(self, message):
        print message
        
    def printVerbose(self, message):
        print message