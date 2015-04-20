#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from abc import ABCMeta, abstractmethod


class Command(object):
    '''
    Abstract base class for all arturo commands.
    '''
    
    __metaclass__ = ABCMeta
        
    def __init__(self, environment):
        super(Command, self).__init__()
        self._env = environment

    def getEnvironment(self):
        return self._env

    @abstractmethod
    def run(self, args):
        None
    
    # +-----------------------------------------------------------------------+
    # | ARGPARSE API
    # +-----------------------------------------------------------------------+
    @abstractmethod
    def getHelpText(self):
        return None
    
    def onVisitArgParser(self, parser):
        None
