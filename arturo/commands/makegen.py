#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

import os

from arturo import __app_name__, i18n
from arturo.commands.base import Command
from arturo.commands.base import ConfiguredCommand, mkdirs
from arturo.commands.build import Cmd_lib_source_files, Cmd_lib_source_headers,\
    Cmd_source_headers, Cmd_source_files, Cmd_mkdirs, Cmd_source_libs, Cmd_d_to_p
from arturo.hardware import BoardMacroResolver
from arturo.libraries import Library
from arturo.templates import JinjaTemplates


_ = i18n.language.ugettext

# +---------------------------------------------------------------------------+
# | Cmd_makegen_noexpand
# +---------------------------------------------------------------------------+
class Cmd_makegen_noexpand(ConfiguredCommand):
    '''
    Generates makefiles but does not provide macro expansion.
    '''

    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    @classmethod
    def appendCommandTemplateForClass(cls, inoutTemplates):
        return Command.appendCommandHelper(cls, 
                { 
                    'path'       : '--path',
                    'template'   : '--template',
                }, inoutTemplates)

    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Generate {} makefiles.'.format(__app_name__)))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument("-p", "--path", required=True)
        parser.add_argument('-t', '--template', required=True)\
    
    def onVisitArgs(self, args):
        setattr(self, "_path", args.path)
        setattr(self, '_template', args.template)

    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        jinjaEnv = self.getConfiguration().getJinjaEnvironment()
        makefileTemplate = JinjaTemplates.getTemplate(jinjaEnv, self._template) 
        
        mkdirs(os.path.dirname(self._path))
        
        makefileTemplate.renderTo(self._path, self.getInitRenderParams())

    # +-----------------------------------------------------------------------+
    # | PROTECTED
    # +-----------------------------------------------------------------------+
    def getInitRenderParams(self):
        return dict()

# +---------------------------------------------------------------------------+
# | Cmd_makegen
# +---------------------------------------------------------------------------+
class Cmd_makegen(Cmd_makegen_noexpand, BoardMacroResolver):
    '''
    Common logic for generating makefiles and expanding makefile jinja 2 macros.
    '''
    
    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    @classmethod
    def appendCommandTemplateForClass(cls, inoutTemplates):
        return Command.appendCommandHelper(cls, 
                {
                    'islibrary'  : '--islibrary',
                }, inoutTemplates)

    @Command.usesCommand(Cmd_source_libs)
    @Command.usesCommand(Cmd_source_headers)
    @Command.usesCommand(Cmd_source_files)
    @Command.usesCommand(Cmd_mkdirs)
    @Command.usesCommand(Cmd_d_to_p)
    @Command.usesCommand(Cmd_lib_source_files)
    @Command.usesCommand(Cmd_lib_source_headers)
    def appendCommandTemplates(self, outTemplates):
        return super(Cmd_makegen, self).appendCommandTemplates(outTemplates)
    
    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        super(Cmd_makegen, self).onVisitArgParser(parser)
        parser.add_argument('--islibrary', default=False, action='store_true')
    
    def onVisitArgs(self, args):
        super(Cmd_makegen, self).onVisitArgs(args)
        setattr(self, '_islibrary', args.islibrary)
        
    # +-----------------------------------------------------------------------+
    # | BoardMacroResolver
    # +-----------------------------------------------------------------------+
    def __call__(self, namespace, macro):
        if macro == "build.project_name":
            return "$(PROJECT_NAME)"
        elif macro == "build.path":
            return "$(DIR_BUILD_PATH)"
        elif macro.startswith("runtime.tools."):
            return self._resolveToolsMacro(macro[14:])
        elif namespace.startswith("recipe.") and namespace.endswith(".pattern"):
            return self._resolveRecipeMacros(namespace[7:-8], macro)
        else:
            raise KeyError()

    # +-----------------------------------------------------------------------+
    # | PROTECTED
    # +-----------------------------------------------------------------------+
    def getInitRenderParams(self):
        initRenderParams = super(Cmd_makegen, self).getInitRenderParams()
        
        configuration = self.getConfiguration()
        board = configuration.getBoard()
        project = self.getProject()

        # directories and paths
        builddir                = project.getBuilddir()
        projectPath             = project.getPath()
        localpath               = os.path.relpath(builddir, projectPath)
        rootdir                 = os.path.relpath(projectPath, builddir)

        # makefile rendering params
        self._requiredLocalPaths = dict()
        boardBuildInfo = board.processBuildInfo(self)
        
        initRenderParams.update({
                            "local" : { "dir"                 : localpath,
                                        "rootdir"             : rootdir,
                                    },
                            "platform" : boardBuildInfo,
                            })

        initRenderParams['local'].update(self._requiredLocalPaths)
        
        self.appendCommandTemplates(initRenderParams)
        
        if self._islibrary:
            libraries = configuration.getLibraries()
            library = self._find_library_in_path(self._path, libraries)
            
            if not library:
                raise RuntimeError(_("Unable to determine library from path {}".format(self._path)))
        
            initRenderParams['library'] = { 
                                           'name'       : library.getNameAndVersion(),
                                           }

        return initRenderParams
        
    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _resolveRecipeMacros(self, recipe, macro):
        if macro == "includes":
            if recipe.startswith("cpp."):
                return "$(addprefix -I,$|)"
            elif recipe.startswith("c."):
                return "$(addprefix -I,$|)"
            else:
                raise KeyError()

        if recipe == "cpp.o" or recipe == "c.o":
            if macro == "object_file":
                return "$@"
            elif macro == "source_file":
                return "$<"
        elif recipe == "ar":
            if macro == "object_file":
                return "$(OBJECT_FILE)"
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
