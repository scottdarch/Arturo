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
from ano import __app_name__


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

        # directories and paths
        builddir            = configuration.getBuilddir()
        projectPath         = self.getProject().getPath()
        localpath           = os.path.relpath(builddir, projectPath)
        rootdir             = os.path.relpath(projectPath, builddir)
        targetsMakefilePath = os.path.join(builddir, JinjaTemplates.MAKEFILE_TARGETS)
        
        self._mkdirs(builddir)

        # ano commands
        listHeadersCommand = __app_name__ + " cmd-source-headers"

        # makefile rendering params
        initRenderParams = {
                            "local" : { "dir" : localpath,
                                        "rootdir" : rootdir,
                                        "makefile" : JinjaTemplates.MAKEFILE,
                                    },
                            "command" : { "source_headers" : listHeadersCommand },
                            }

        with open(targetsMakefilePath, 'wt') as f:
            f.write(template.render(initRenderParams))
            
    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _fileListToWildcards(self, filelist):
        '''
        @param filelist: Given a list of files return a list of wildcard arguments to find
                         all files in the directories
        '''
        pass

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
