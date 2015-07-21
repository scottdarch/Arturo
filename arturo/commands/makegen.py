#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

import os
import re

from arturo import __app_name__, i18n
from arturo.commands import build
from arturo.commands.base import ConfiguredCommand, mkdirs
from arturo.hardware import BoardMacroResolver
from arturo.templates import JinjaTemplates


_ = i18n.language.ugettext

# +---------------------------------------------------------------------------+
# | Makegen_lib
# +---------------------------------------------------------------------------+
class Makegen_lib(ConfiguredCommand):
    '''
    (Re)Generate makefile for a given library.
    '''
    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Generate {} makefile for a library.'.format(__app_name__)))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument("-p", "--path")
    
    def onVisitArgs(self, args):
        setattr(self, "_path", args.path)

    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        configuration = self.getConfiguration()
        jinjaEnv = configuration.getJinjaEnvironment()
        makefileTemplate = JinjaTemplates.getTemplate(jinjaEnv, 'make_lib')
        library_name = self._library_name_from_path(self._path)
        
        if not library_name:
            raise RuntimeError("Unable to determine library from path {}".format(self._path))
        
        initRenderParams = self.appendCommandTemplates()
        initRenderParams['library'] = { 'name': library_name }
        
        mkdirs(os.path.dirname(self._path))
        
        makefileTemplate.renderTo(self._path, initRenderParams)
        
    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _library_name_from_path(self, path):
        matchobj = re.search("/([\w\-\d\.]+)/[\w\.]+$", path)
        if matchobj:
            return matchobj.group(1)
        else:
            return None
    
# +---------------------------------------------------------------------------+
# | Makegen_targets
# +---------------------------------------------------------------------------+
class Makegen_targets(ConfiguredCommand, BoardMacroResolver):
    '''
    (Re)Generate makefiles for a given configuration.
    '''
    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Generate {} makefiles for the project.'.format(__app_name__)))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument("-p", "--path")
    
    def onVisitArgs(self, args):
        setattr(self, "_path", args.path)
        
    # +-----------------------------------------------------------------------+
    # | BoardMacroResolver
    # +-----------------------------------------------------------------------+
    def __call__(self, namespace, macro):
        if macro == "build.project_name":
            return "$(PROJECT_NAME)"
        elif macro == "build.path":
            return "$(DIR_BUILD)/$(BOARD)"
        elif macro.startswith("runtime.tools."):
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
        makefileTemplate = JinjaTemplates.getTemplate(jinjaEnv, 'make_targets')

        # directories and paths
        builddir                = project.getBuilddir()
        projectPath             = project.getPath()
        localpath               = os.path.relpath(builddir, projectPath)
        rootdir                 = os.path.relpath(projectPath, builddir)
        targetsMakefilePath     = self._path
        toolchainMakefilePath   = os.path.join(builddir, JinjaTemplates.TEMPLATES['make_toolchain'])
        
        mkdirs(builddir)
        
        # arturo commands
        listHeadersCommand = __app_name__ + " cmd-source-headers"
        listSourceCommand = __app_name__ + " cmd-source-files"
        listLibraryDepsCommand = __app_name__ + " cmd-source-libraries --ppath"
        sketchPreprocessCommand = __app_name__ + " preprocess"
        dToPCommand = __app_name__ + " cmd-d-to-p --dpath"
        mkdirsCommand = "mkdir -p "
        makeGenCommand = __app_name__ + " make-gen"

        # makefile rendering params
        self._requiredLocalPaths = dict()
        boardBuildInfo = board.processBuildInfo(self)
        
        initRenderParams = {
                            "local" : { "dir"                 : localpath,
                                        "rootdir"             : rootdir,
                                    },
                            "command" : { "source_headers"    : listHeadersCommand,
                                          "source_files"      : listSourceCommand,
                                          "source_lib_deps"   : listLibraryDepsCommand,
                                          "preprocess_sketch" : sketchPreprocessCommand,
                                          "cmd_d_to_p"        : dToPCommand,
                                          "pfile_ext"         : build.Cmd_d_to_p.PFILE_EXTENSION,
                                          "mkdirs"            : mkdirsCommand,
                                          "make_gen"          : makeGenCommand,
                                    },
                            "argument" : { "dp_file_path"     : "--dpath",
                                    },
                            "platform" : boardBuildInfo,
                            }
        
        self.appendCommandTemplates(initRenderParams)
        
        makefileTemplate.renderTo(targetsMakefilePath, initRenderParams)
        
        if len(self._requiredLocalPaths):
            self._console.printVerbose("This makefile requires local paths.")
            
            toolchainTemplate = JinjaTemplates.getTemplate(jinjaEnv, JinjaTemplates.TEMPLATES['make_toolchain'])
            
            toolchainRenderParams = {
                                     "local" : self._requiredLocalPaths,
                                    }

            toolchainTemplate.renderTo(toolchainMakefilePath, toolchainRenderParams)

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
        elif recipe == "ar":
            if macro == "object_file":
                return "$(strip $(OBJ_FILES))"
            elif macro == "archive_file":
                return "$(notdir $@)"
        elif recipe == "c.combine":
            if macro == "object_files":
                return "$(strip $(OBJ_FILES))"
            elif macro == "archive_file":
                return "$(notdir $<)"

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

