#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

import os

from ano import __app_name__
from ano.Arturo2.commands.base import ConfiguredCommand, mkdirs
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
        project = self.getProject()
        jinjaEnv = configuration.getJinjaEnvironment()
        template = JinjaTemplates.getTemplate(jinjaEnv, JinjaTemplates.MAKEFILE_TARGETS)

        # directories and paths
        builddir            = project.getBuilddir()
        projectPath         = project.getPath()
        localpath           = os.path.relpath(builddir, projectPath)
        rootdir             = os.path.relpath(projectPath, builddir)
        targetsMakefilePath = os.path.join(builddir, JinjaTemplates.MAKEFILE_TARGETS)
        
        mkdirs(builddir)

        # ano commands
        listHeadersCommand = __app_name__ + " cmd-source-headers"
        listSourceCommand = __app_name__ + " cmd-source-files"
        sketchPreprocessCommand = __app_name__ + " preprocess"

        # makefile rendering params
        initRenderParams = {
                            "local" : { "dir" : localpath,
                                        "rootdir" : rootdir,
                                        "makefile" : JinjaTemplates.MAKEFILE,
                                    },
                            "command" : { "source_headers" : listHeadersCommand,
                                          "source_files"   : listSourceCommand,
                                          "preprocess_sketch" : sketchPreprocessCommand,
                                    },
                            }

        with open(targetsMakefilePath, 'wt') as f:
            f.write(template.render(initRenderParams))

