#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

import os

from arturo import __app_name__, i18n
from arturo.commands import build
from arturo.commands.base import Command
from arturo.commands.base import ConfiguredCommand, mkdirs
from arturo.commands.build import Cmd_source_libs, Cmd_lib_source_files, Cmd_lib_source_headers
from arturo.hardware import BoardMacroResolver
from arturo.libraries import Library
from arturo.templates import JinjaTemplates


_ = i18n.language.ugettext


# +---------------------------------------------------------------------------+
# | Makegen_targets
# +---------------------------------------------------------------------------+
class Makegen_targets(ConfiguredCommand, BoardMacroResolver):
    '''
    Common logic for generating makefiles with build targets.
    '''
    
    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    @classmethod
    def appendCommandTemplate(cls, inoutTemplates):
        return Command.appendCommandHelper(cls, 
                { 
                    'path'     : '--path',
                    'template'   : '--template',
                }, inoutTemplates)

    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Generate {} makefile for a makefile that contains Arduino build targets.'.format(__app_name__)))

    def appendCommandTemplates(self, outTemplates):
        return super(Makegen_targets, self).appendCommandTemplates(outTemplates)
    
    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument("-p", "--path", required=True)
        parser.add_argument('-t', '--template', required=True)
    
    def onVisitArgs(self, args):
        setattr(self, "_path", args.path)
        setattr(self, '_template', args.template)
        
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
        makefileTemplate = JinjaTemplates.getTemplate(jinjaEnv, self._template)

        # directories and paths
        builddir                = project.getBuilddir()
        projectPath             = project.getPath()
        localpath               = os.path.relpath(builddir, projectPath)
        rootdir                 = os.path.relpath(projectPath, builddir)
        targetsMakefilePath     = self._path
        toolchainMakefilePath   = os.path.join(builddir, JinjaTemplates.TEMPLATES['make_toolchain'])
        
        mkdirs(os.path.dirname(targetsMakefilePath))
        
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
            
            toolchainTemplate = JinjaTemplates.getTemplate(jinjaEnv, 'make_toolchain')
            
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

# +---------------------------------------------------------------------------+
# | Makegen_lib
# +---------------------------------------------------------------------------+
class Makegen_lib(Makegen_targets):
    '''
    (Re)Generate makefile for a given library.
    '''
    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    @classmethod
    def appendCommandTemplate(cls, inoutTemplates):
        return Command.appendCommandHelper(cls, 
                { 
                    'path'     : '--path',
                }, inoutTemplates)
    
    @Command.usesCommand(Cmd_lib_source_files)
    @Command.usesCommand(Cmd_lib_source_headers)
    def appendCommandTemplates(self, inoutTemplates):
        return super(Makegen_lib, self).appendCommandTemplates(inoutTemplates)
    
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Generate {} makefile for a library.'.format(__app_name__)))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument("-p", "--path", required=True)
    
    def onVisitArgs(self, args):
        setattr(self, "_path", args.path)

    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        configuration = self.getConfiguration()
        jinjaEnv = configuration.getJinjaEnvironment()
        makefileTemplate = JinjaTemplates.getTemplate(jinjaEnv, 'make_lib')
        libraries = self.getConfiguration().getLibraries()
        library = self._find_library_in_path(self._path, libraries)
        
        if not library:
            raise RuntimeError(_("Unable to determine library from path {}".format(self._path)))
        
        initRenderParams = self.appendCommandTemplates(dict())
        initRenderParams['library'] = { 
                                       'name'       : library.getNameAndVersion(),
                                       }
        initRenderParams["local"] = { "dir"                 : "foo",
                                    }
        
        mkdirs(os.path.dirname(self._path))
        
        makefileTemplate.renderTo(self._path, initRenderParams)
        
    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _find_library_in_path(self, path, libraries):
        libDirName = os.path.basename(os.path.dirname(path))
        console = self.getConsole()
        if console.willPrintVerbose():
            console.printVerbose("Using folder name {} as the name of the library.".format(libDirName))
        libNameAndVersion = Library.libNameAndVersion(libDirName)
        libraryversions = libraries.get(libNameAndVersion[0])
        if libraryversions:
            library = libraryversions.get(libNameAndVersion[1])
            if not library:
                raise RuntimeError(_("Version {} of library {} was not available.".format(libNameAndVersion[1], libNameAndVersion[0])))
            else:
                return library


# +---------------------------------------------------------------------------+
# | MetaMake_libs
# +---------------------------------------------------------------------------+
class Metamakegen_libs(ConfiguredCommand):
    
    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    @classmethod
    def appendCommandTemplate(cls, inoutTemplates):
        return Command.appendCommandHelper(cls, 
                { 
                    'path'     : '--path',
                }, inoutTemplates)
        
    @Command.usesCommand(Makegen_targets)
    @Command.usesCommand(Makegen_lib)
    def appendCommandTemplates(self, inoutTemplates):
        return super(Metamakegen_libs, self).appendCommandTemplates(inoutTemplates)
    
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Generate {} meta-makefiles for the project.'.format(__app_name__)))
    
    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument("-p", "--path", default=None)
        
    def onVisitArgs(self, args):
        if args.path is None:
            self._path = self.getProject().getBuilddir() + JinjaTemplates.TEMPLATES['metamake_libs']
        else:
            self._path = args.path
        
    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        configuration           = self.getConfiguration()
        jinjaEnv                = configuration.getJinjaEnvironment()
        makefileTemplate        = JinjaTemplates.getTemplate(jinjaEnv, 'metamake_libs')
        builddir                = os.path.dirname(self._path)
        targetsMakefilePath     = self._path
        
        mkdirs(builddir)
        
        initRenderParams = self.appendCommandTemplates(dict())
        
        sourceLibsCommand = self.getCommand(Cmd_source_libs)
        
        libraries = ""
        sources   = ""
        
        for libraryNameAndVersion in sourceLibsCommand.getAllPossibleLibsForProject().iterkeys():
            libraries += libraryNameAndVersion
            libraries += " "
        
        for source in sourceLibsCommand.getAllSources():
            sources += source
            sources += " "
        
        initRenderParams['source'] = {'libs': libraries, 'files': sources}
        
        makefileTemplate.renderTo(targetsMakefilePath, initRenderParams)
