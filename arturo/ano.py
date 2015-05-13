#!/usr/bin/env python2

#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

import argparse
import sys

from arturo import i18n, __app_name__, ArgumentVisitor, Runnable
from arturo.commands import getAllCommands
from arturo.commands.base import UnknownUserInputException, ProjectCommand, ConfiguredCommand
from arturo.display import Console
from arturo.environment import Environment


_ = i18n.language.ugettext

class ArturoCommandLine(ArgumentVisitor, Runnable):
    '''
    Object representing a command-line invokation of Arturo
    '''
    
    def __init__(self, console):
        super(ArturoCommandLine, self).__init__()
        self._commandName = None
        self._command = None
        self._console = console
        self._env = None
        self._commands = None
        
    def getEnvironment(self):
        if self._env is None:
            self._env = Environment(self._console)
        return self._env
    
    def getCommands(self):
        if self._commands is None:
            self._commands = getAllCommands()
        return self._commands
    
    def getCommandLineDescription(self):
        return _("""\
Arturo is a command-line toolkit for working with MCU prototype hardware adhering
to the Arduino15 IDE specification for 3rp party hardware:

https://github.com/arduino/Arduino/wiki/Arduino-IDE-1.5---3rd-party-Hardware-specification

TODO: more about gnu make and the core functionality provided by arturo.

--help to get further help. E.g.:

    ano build --help
""")

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        commands = self.getCommands()
        for arg in sys.argv:
            if arg in commands:
                self._commandName = arg
                break;
        try:
            commandClass = commands[self._commandName]
        except KeyError:
            raise UnknownUserInputException()

        subparsers = parser.add_subparsers()
        environment = self.getEnvironment()
        
        if issubclass(commandClass, ProjectCommand):
            #TODO: allow explicit project to be provided
            project = environment.getInferredProject()

            if issubclass(commandClass, ConfiguredCommand):
                #TODO: allow explicit configuration to be provided
                command = commandClass(environment, project, project.getLastConfiguration(), self._console)
            else:
                command = commandClass(environment, project, self._console)
        else:
            command = commandClass(environment, self._console)
            
        p = command.add_parser(subparsers)
        command.onVisitArgParser(p)
        p.set_defaults(func=command.run)
        
        self._command = command

    def onVisitArgs(self, args):
        if self._command is not None:
            self._command.onVisitArgs(args)
        
    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        parser = argparse.ArgumentParser(prog=__app_name__, description=self.getCommandLineDescription())
    
        try:
            self._console.onVisitArgParser(parser)
            self.onVisitArgParser(parser)

            args = parser.parse_args()

            self.onVisitArgs(args)
            self._console.onVisitArgs(args)

            args.func()

        except UnknownUserInputException:
            parser.print_help()

# +---------------------------------------------------------------------------+
# | ARTURO MAIN
# +---------------------------------------------------------------------------+
def main():
    ArturoCommandLine(Console()).run()
        
if __name__ == "__main__" :
    main()
