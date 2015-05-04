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
from ano.Arturo2.hardware import BoardMacroResolver


# +---------------------------------------------------------------------------+
# | Make_gen
# +---------------------------------------------------------------------------+
class Make_gen(ConfiguredCommand, BoardMacroResolver):
    '''
    (Re)Generate makefiles for a given configuration.
    '''
    
    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        None
    
    # +-----------------------------------------------------------------------+
    # | BoardMacroResolver
    # +-----------------------------------------------------------------------+
    def __call__(self, namespace, macro):
        if macro.startswith("runtime.tools."):
            return self._resolveToolsMacro(macro[14:])
        elif namespace.startswith("recipe.") and namespace.endswith(".pattern"):
            return self._resolveRecipeMacros(namespace[7:-8], macro)
        else:
            raise KeyError()

    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        configuration = self.getConfiguration()
        board = configuration.getBoard()
        project = self.getProject()
        jinjaEnv = configuration.getJinjaEnvironment()
        makefileTemplate = JinjaTemplates.getTemplate(jinjaEnv, JinjaTemplates.MAKEFILE_TARGETS)

        # directories and paths
        builddir                = project.getBuilddir()
        projectPath             = project.getPath()
        localpath               = os.path.relpath(builddir, projectPath)
        rootdir                 = os.path.relpath(projectPath, builddir)
        targetsMakefilePath     = os.path.join(builddir, JinjaTemplates.MAKEFILE_TARGETS)
        toolchainMakefilePath   = os.path.join(builddir, JinjaTemplates.MAKEFILE_TOOLCHAIN)
        
        mkdirs(builddir)
        
        # ano commands
        listHeadersCommand = __app_name__ + " cmd-source-headers"
        listSourceCommand = __app_name__ + " cmd-source-files"
        sketchPreprocessCommand = __app_name__ + " preprocess"

        # makefile rendering params
        self._requiredLocalPaths = dict()
        boardBuildInfo = board.processBuildInfo(self)
        
        initRenderParams = {
                            "local" : { "dir" : localpath,
                                        "rootdir" : rootdir,
                                        "makefile" : JinjaTemplates.MAKEFILE,
                                        "toolchainmakefile" : JinjaTemplates.MAKEFILE_TOOLCHAIN
                                    },
                            "command" : { "source_headers" : listHeadersCommand,
                                          "source_files"   : listSourceCommand,
                                          "preprocess_sketch" : sketchPreprocessCommand,
                                    },
                            'platform' : boardBuildInfo,
                            }

        with open(targetsMakefilePath, 'wt') as f:
            f.write(makefileTemplate.render(initRenderParams))
        
        if len(self._requiredLocalPaths):
            # TODO: message this to the user. They have to understand not to checkin the toolchain makefile
            # as it is highly host environment specific.
            self._console.printVerbose("This makefile requires local paths.")
            
            toolchainTemplate = JinjaTemplates.getTemplate(jinjaEnv, JinjaTemplates.MAKEFILE_TOOLCHAIN)
            
            toolchainRenderParams = {
                                     "local" : self._requiredLocalPaths,
                                }

            with open(toolchainMakefilePath, 'wt') as f:
                f.write(toolchainTemplate.render(toolchainRenderParams))

        elif os.path.exists(toolchainMakefilePath):
            if self._console.askYesNoQuestion(_("Toolchain makefile {0} appears to be obsolete. Delete it?".format(toolchainMakefilePath))):
                os.remove(toolchainMakefilePath)

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _resolveRecipeMacros(self, recipe, macro):
        if macro == "includes":
            #TODO return list of "-I include.h"
            raise KeyError()
        
        if recipe == "cpp.o":
            if macro == "object_file":
                return "$@"
            elif macro == "source_file":
                return "$<"

        raise KeyError()
            
    def _resolveToolsMacro(self, macro):
        if macro.endswith(".path"):
            self._requiredLocalPaths['toolchainpath'] = self.getConfiguration().getPackage().getToolChainByNameAndVerison(macro[:-5]).getHostToolChain().getPath()
            return "$(LOCAL_TOOLCHAIN_PATH)"
        else:
            raise KeyError()
    