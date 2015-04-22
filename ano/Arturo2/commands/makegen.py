#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

import errno
import os

from ano.Arturo2.commands.base import ConfiguredCommand
from ano.Arturo2.templates import JinjaTemplates


# +---------------------------------------------------------------------------+
# | Make_gen
# +---------------------------------------------------------------------------+
class Make_gen(ConfiguredCommand):
    '''
    (Re)Generate makefiles for a given configuration.
    '''
    
    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        None
    
    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        configuration = self.getConfiguration()
        jinjaEnv = configuration.getJinjaEnvironment()
        template = JinjaTemplates.getTemplate(jinjaEnv, JinjaTemplates.MAKEFILE_TARGETS)
        builddir = configuration.getBuilddir()
        makefilePath = os.path.join(builddir, JinjaTemplates.MAKEFILE_TARGETS)
        self._mkdirs(builddir)
        with open(makefilePath, 'wt') as f:
            f.write(template.render())
            
    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _mkdirs(self, path):
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
