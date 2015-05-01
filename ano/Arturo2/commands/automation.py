#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import os

from ano.Arturo2.commands.base import ConfiguredCommand


# +---------------------------------------------------------------------------+
# | List_source_headers
# +---------------------------------------------------------------------------+
class Cmd_source_headers(ConfiguredCommand):
    
    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        None
    
    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        headers = self.getConfiguration().getHeaders()
        projectPath = self.getProject().getPath()
        relativeHeaders = [os.path.relpath(headers[x], projectPath) for x in range(len(headers))]
        self.getConsole().stdout(*relativeHeaders)
