# -*- coding: utf-8; -*-

from ano import __version__
from ano.commands.base import Command

class Version(Command):

    """
    Print the version of ano.
    """

    name = 'version'
    help_line = "Print the current version of ano."

    def run(self, args):
        print "ano {}".format(__version__)
