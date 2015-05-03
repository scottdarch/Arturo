#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from abc import ABCMeta
import errno
import os

from ano.Arturo2 import Runnable, ArgumentVisitor


def mkdirs(path):
    '''
    Thanks (stack overflow)[https://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python]
    '''
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
            
# +---------------------------------------------------------------------------+
# | Command
# +---------------------------------------------------------------------------+
class Command(ArgumentVisitor, Runnable):
    '''
    Abstract base class for all arturo commands.
    '''
    
    __metaclass__ = ABCMeta
        
    def __init__(self, environment, console):
        super(Command, self).__init__()
        self._env = environment
        self._console = console

    def getConsole(self):
        return self._console

    def getEnvironment(self):
        return self._env

    # +-----------------------------------------------------------------------+
    # | ARGPARSE API
    # +-----------------------------------------------------------------------+
    def getHelpText(self):
        return None

# +---------------------------------------------------------------------------+
# | ProjectCommand
# +---------------------------------------------------------------------------+
class ProjectCommand(Command):
    '''
    Abstract base class for all arturo commands that are project specific but which may
    or may not have a configuration.
    '''
    
    __metaclass__ = ABCMeta
        
    def __init__(self, environment, project, console):
        super(ProjectCommand, self).__init__(environment, console)
        self._project = project

    def getProject(self):
        return self._project

# +---------------------------------------------------------------------------+
# | ConfiguredCommand
# +---------------------------------------------------------------------------+

class ConfiguredCommand(ProjectCommand):
    '''
    Abstract base class for arturo commands that require a Configuration.
    '''
    
    __metaclass__ = ABCMeta
        
    def __init__(self, environment, project, configuration, console):
        super(ConfiguredCommand, self).__init__(environment, project, console)
        self._configuration = configuration

    def getConfiguration(self):
        return self._configuration

