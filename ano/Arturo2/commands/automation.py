#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import os

from ano.Arturo2.commands.base import ConfiguredCommand


# +---------------------------------------------------------------------------+
# | Cmd_source_headers
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
        core = self.getConfiguration().getBoard().getCore();
        headers += core.getHeaders()

        projectPath = self.getProject().getPath()
        
        relativeHeaders = [os.path.relpath(headers[x], projectPath) for x in range(len(headers))]
        self.getConsole().stdout(*relativeHeaders)

# +---------------------------------------------------------------------------+
# | Cmd_source_files
# +---------------------------------------------------------------------------+
class Cmd_source_files(ConfiguredCommand):
    
    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        None
    
    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        sources = self.getConfiguration().getSources()
        projectPath = self.getProject().getPath()
        relativeSource = [os.path.relpath(sources[x], projectPath) for x in range(len(sources))]
        self.getConsole().stdout(*relativeSource)
