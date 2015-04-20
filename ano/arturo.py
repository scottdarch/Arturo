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
    
    def __init__(self):
        super(ArturoSession, self).__init__()
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
    
    def getCommandLineDescription(self):
        return _("""\
Arturo is a command-line toolkit for working with Arduino hardware.

It is intended to replace Arduino IDE UI for those who prefer to work in
terminal or want to integrate Arduino development in a 3rd party IDE.

Arturo can build sketches, libraries, upload firmwares, establish
serial-communication. For this it is split in a bunch of subcommands, like git
or mercurial do. The full list is provided below. You may run any of them with
--help to get further help. E.g.:

    ano build --help
""")

    
    
    def main(self):
        try:
            current_command = sys.argv[1]
        except IndexError:
            current_command = None
    
        parser = argparse.ArgumentParser(prog=__app_name__, formatter_class=FlexiFormatter, description=self.getCommandLineDescription())
        subparsers = parser.add_subparsers()
        commands = self.getCommands()
        for commandName, command in commands.iteritems():
            p = subparsers.add_parser(commandName, formatter_class=FlexiFormatter, help=command.getHelpText())
            if current_command != commandName:
                continue
            command.setup_arg_parser(p)
            p.set_defaults(func=command.run)

        args = parser.parse_args()
        
        try:
            run_anywhere = "init clean list-models serial version"
    
#             if current_command not in run_anywhere:
#                 if os.path.isdir(e.output_dir):
#                     # we have an output dir so we'll pretend this is a project folder
#                     None
#                 elif e.src_dir is None or not os.path.isdir(e.src_dir):
#                     raise Abort("No project found in this directory.")
#     
#             if current_command not in run_anywhere:
#                 # For valid projects create .build & lib
#                 if not os.path.isdir(e.build_dir):                
#                     os.makedirs(e.build_dir)
#     
#                 if not os.path.isdir(e.lib_dir):
#                     os.makedirs(e.lib_dir)
#                     with open('lib/.holder', 'w') as f:
#                         f.write("")
    
            args.func(args)
        except KeyboardInterrupt:
            print 'Terminated by user'
        
if __name__ == "__main__" :
    ArturoSession().main()
