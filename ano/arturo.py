#!/usr/bin/env python2

#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

import argparse
import string
import sys

from ano import i18n, __app_name__
from ano.Arduino15.commands import getAllCommands
from ano.Arduino15.environment import Environment
from ano.argparsing import FlexiFormatter


_ = i18n.language.ugettext

class ArturoSession(object):
    '''
    Object representing an interactive session using Arturo
    '''
    
    def __init__(self, command):
        super(ArturoSession, self).__init__()
        self._sessionCommand = command
        self._env = None
        self._commands = None
        
    def getEnvironment(self):
        if self._env is None:
            self._env = Environment()
        return self._env
    
    def getCommands(self):
        if self._commands is None:
            self._commands = dict()
            commands = getAllCommands()
            environment = self.getEnvironment()
            for name, commandClass in commands:
                self._commands[string.lower(name)] = commandClass(environment)
        return self._commands
    
    def onVisitArgParser(self, parser):
        subparsers = parser.add_subparsers()
        commands = self.getCommands()
        for commandName, command in commands.iteritems():
            p = subparsers.add_parser(commandName, formatter_class=FlexiFormatter, help=command.getHelpText())
            if self._sessionCommand != commandName:
                continue
            command.onVisitArgParser(p)
            p.set_defaults(func=command.run)

    def run(self):
        parser = argparse.ArgumentParser(prog=__app_name__, formatter_class=FlexiFormatter, description=self.getCommandLineDescription())
    
        self.onVisitArgParser(parser)
        
        args = parser.parse_args()
        
        try:
            args.func(args)
        except KeyboardInterrupt:
            print 'Terminated by user'

    def getCommandLineDescription(self):
        return _("""\
Arturo is a command-line toolkit for working with MCU prototype hardware adhering
to the Arduino15 IDE specification for 3rp party hardware:

https://github.com/arduino/Arduino/wiki/Arduino-IDE-1.5---3rd-party-Hardware-specification

TODO: more about gnu make and the core functionality provided by arturo.

--help to get further help. E.g.:

    ano build --help
""")

    
# +---------------------------------------------------------------------------+
# | ARTURO MAIN
# +---------------------------------------------------------------------------+
def main():
    try:
        command = sys.argv[1]
    except IndexError:
        command = None

    ArturoSession(command).run()
        
if __name__ == "__main__" :
    main()
