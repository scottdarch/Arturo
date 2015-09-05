#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
from abc import ABCMeta, abstractmethod
import errno
import os
import string
import sys

from arturo import Runnable, ArgumentVisitor, __app_name__

class UnknownUserInputException(Exception):
    '''
    Thrown when input provided from command arguments is unknown, malformed, or out-of-context.
    '''
    pass


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
    
    @staticmethod
    def usesCommand(commandClass):
        def appendCommandTemplatesDecorator(func):
            def appendCommandTemplatesWrapper(self, inoutTemplates):
                commandName = Command.command_class_to_commandname(commandClass)
                try:
                    inoutTemplates['commands'][commandName] = __app_name__ + " " + commandName
                except KeyError:
                    inoutTemplates['commands'] = { commandName : __app_name__ + " " + commandName }
            
                try:
                    return func(self, getattr(commandClass, "appendCommandTemplate")(inoutTemplates))
                except:
                    return func(self, inoutTemplates)
                
            return appendCommandTemplatesWrapper
        return appendCommandTemplatesDecorator

    @classmethod
    def command_class_to_commandname(cls, commandType):
        return string.lower(commandType.__name__)

    @classmethod
    def appendCommandHelper(cls, subcls, arguments, inoutTemplates):
        try:
            inoutTemplates['arguments'].update(arguments)
        except KeyError:
            inoutTemplates['arguments'] = arguments
        
        return inoutTemplates
        
    def __init__(self, environment, console):
        super(Command, self).__init__()
        self._env = environment
        self._console = console

    def getCommandName(self):
        return Command.command_class_to_commandname(self.__class__)

    def appendCommandTemplates(self, outTemplates):
        # Always append the current command.
        commandName = self.getCommandName()
        try:
            outTemplates['commands'][commandName] = __app_name__ + " " + commandName
        except KeyError:
            outTemplates['commands'] = { commandName : __app_name__ + " " + commandName }
        try:
            return getattr(self.__class__, "appendCommandTemplate")(outTemplates)
        except:
            return outTemplates
     
    @abstractmethod
    def add_parser(self, subparsers):
        pass

    def getConsole(self):
        return self._console

    def getEnvironment(self):
        return self._env

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

    def getCommand(self, commandClass):
        return getattr(sys.modules["arturo.commands"], 'getDefaultCommand')(self._env, self.command_class_to_commandname(commandClass), self._console)
   
    def getConfiguration(self):
        return self._configuration

