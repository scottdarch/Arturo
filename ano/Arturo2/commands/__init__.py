#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

import inspect
import string
import sys
import textwrap

from ano import Arturo2
import ano
from ano.Arturo2.commands.automation import Cmd_source_headers, Cmd_source_files
from ano.Arturo2.commands.base import Command
from ano.Arturo2.commands.build import Preprocess
from ano.Arturo2.commands.makegen import Make_gen
from ano.Arturo2.commands.prebuild import Init, Version
from ano.Arturo2.commands.query import List_boards, List_tools


def _is_command_subclass(commandClass):
    if inspect.isclass(commandClass) and issubclass(commandClass, Command) and commandClass != Command:
        return True
    else:
        return False

def _class_to_commandname(className):
    lowername = string.lower(className)
    return lowername.replace('_', '-')
    

def getAllCommands():
    '''
    Returns a dictionary of class names to class objects for all Command subclasses in the commands module.
    '''
    # commands is a list of name, value pairs sorted by name
    commands = inspect.getmembers(sys.modules[__name__], _is_command_subclass)
    return {_class_to_commandname(name): commandClass for name, commandClass in commands}
