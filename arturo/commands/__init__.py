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

import arturo
from arturo.commands.base import Command
from arturo.commands.build import Preprocess, Cmd_source_headers, Cmd_source_files, Cmd_d_to_p, Cmd_source_libraries, Cmd_mkdirs
from arturo.commands.makegen import Make_gen
from arturo.commands.prebuild import Init, Version
from arturo.commands.query import List_boards, List_tools, List_platform_data, List_libraries


def _is_command_subclass(commandClass):
    if inspect.isclass(commandClass) and issubclass(commandClass, Command) and commandClass != Command:
        return True
    else:
        return False


def getAllCommands():
    '''
    Returns a dictionary of class names to class objects for all Command subclasses in the commands module.
    '''
    # commands is a list of name, value pairs sorted by name
    commands = inspect.getmembers(sys.modules[__name__], _is_command_subclass)
    return {Command.command_class_to_commandname(commandClass): commandClass for name, commandClass in commands}  # @UnusedVariable
