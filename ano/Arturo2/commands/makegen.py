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
        targetsMakefilePath     = JinjaTemplates.MAKEFILE_TARGETS
        toolchainMakefilePath   = os.path.join(builddir, JinjaTemplates.MAKEFILE_LOCALPATHS)
        
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
                                        "toolchainmakefile" : JinjaTemplates.MAKEFILE_LOCALPATHS
                                    },
                            "command" : { "source_headers" : listHeadersCommand,
                                          "source_files"   : listSourceCommand,
                                          "preprocess_sketch" : sketchPreprocessCommand
                                    },
                            'platform' : boardBuildInfo,
                            }

        with open(targetsMakefilePath, 'wt') as f:
            f.write(makefileTemplate.render(initRenderParams))
        
        if len(self._requiredLocalPaths):
            self._console.printVerbose("This makefile requires local paths.")
            
            toolchainTemplate = JinjaTemplates.getTemplate(jinjaEnv, JinjaTemplates.MAKEFILE_LOCALPATHS)
            
            toolchainRenderParams = {
                                     "local" : self._requiredLocalPaths,
                                }

            with open(toolchainMakefilePath, 'wt') as f:
                f.write(toolchainTemplate.render(toolchainRenderParams))

        elif os.path.exists(toolchainMakefilePath):
            if self._console.askYesNoQuestion(_("Local paths makefile {0} appears to be obsolete. Delete it?".format(toolchainMakefilePath))):
                os.remove(toolchainMakefilePath)

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _resolveRecipeMacros(self, recipe, macro):
        if macro == "includes":
            if recipe.startswith("cpp."):
                return "$(CPP_HEADERS_W_I)"
            elif recipe.startswith("c."):
                return "$(C_HEADERS_W_I)"
            else:
                raise KeyError()

        if recipe == "cpp.o":
            if macro == "object_file":
                return "$@"
            elif macro == "source_file":
                return "$<"

        raise KeyError()
            
    def _resolveToolsMacro(self, macro):
        if macro.endswith(".path"):
            package = self.getConfiguration().getPackage()
            key = macro[:-5]
            makeKey = "LOCAL_TOOLCHAIN_PATH_{}".format(key.upper().replace('-', '_'))
            try:
                toolchain = package.getToolChainByNameAndVerison(key)
            except (KeyError, ValueError):
                toolchain = package.getToolChainLatestAvailableVersion(key)

            hosttoolchain = toolchain.getHostToolChain()
            if hosttoolchain.exists():
                try:
                    toolchainsmake = self._requiredLocalPaths['toolchains']
                    toolchainsmake = "{}{}{}={}".format(toolchainsmake, "\n", makeKey, hosttoolchain.getPath())
                except KeyError:
                    toolchainsmake = "{}={}".format(makeKey, hosttoolchain.getPath())
                self._requiredLocalPaths['toolchains'] = toolchainsmake
            else:
                self.getConsole().printWarning(_("WARNING: No host tools installed for {0}-{1} on this platform. Builds will probably fail.").format(toolchain.getName(), toolchain.getVersion()))

            return "$({})".format(makeKey)
        else:
            raise KeyError()
