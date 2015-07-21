#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import os

from arturo import __app_name__, __version__, __lib_name__, i18n, MissingRequiredFileException
from arturo.commands.base import Command, ProjectCommand
from arturo.templates import JinjaTemplates


_ = i18n.language.ugettext

# +---------------------------------------------------------------------------+
# | Version
# +---------------------------------------------------------------------------+
class Version(Command):
    '''
    Get versioning information for Arturo/arturo.
    '''

    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Print {} version information then exit.'.format(__app_name__)))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        None

    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        self.getConsole().printInfo(_('{0} {1} (using lib{2})'.format(__app_name__, __version__, __lib_name__)))
        
# +---------------------------------------------------------------------------+
# | Init
# +---------------------------------------------------------------------------+
class Init(ProjectCommand):
    '''
    Safe initialization of a project with the Arturo generated makefile. Once this command completes
    the project should be buildable using make.
    '''
    LEGACY_SOURCEFOLDER_NAMES = ["src"]
    
    def __init__(self, environment, project, console):
        super(Init, self).__init__(environment, project, console)
        self._force = False

    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Initialize a project for use with {} and its makefiles.'.format(__app_name__)))

    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument("-f", "--force", action="store_true")
    
    def onVisitArgs(self, args):
        self._force = args.force

    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        project = self.getProject()
        console = self.getConsole()
        
        # first choose a project "main"
        # TODO: allow commandline arguments to force project folders to be treated as source folders.
        sourceRoots = project.getSourceRoots(Init.LEGACY_SOURCEFOLDER_NAMES)
        sourceRoot = None
        if len(sourceRoots) > 1:
            projectList = list()
            for rootPath, rootName, mainSource in sourceRoots:  # @UnusedVariable
                projectList.append([rootName, mainSource])
            #TODO: handle invalid input
            sourceRoot = sourceRoots[console.askPickOneFromList(_("Which project?"), projectList)]
        elif (len(sourceRoots) == 1):
            sourceRoot = sourceRoots[0]
        else:
            raise MissingRequiredFileException(self.getEnvironment().getSearchPath(), Init.LEGACY_SOURCEFOLDER_NAMES, "Source root folders")
            

        # next use the IDE's preferences to populate our makefile
        preferences = project.getEnvironment().getPreferences()
        
        # setup the top level makefile
        makefilePath = project.getMakefilePath()
        sourcePath = os.path.relpath(os.path.join(sourceRoot[0], sourceRoot[1]), os.path.dirname(makefilePath))
        projectName = sourceRoot[1] if sourceRoot[1] not in Init.LEGACY_SOURCEFOLDER_NAMES else os.path.basename(sourceRoot[0])
        
        if os.path.exists(makefilePath):
            if self._force:
                makeFileGen = True
            else:
                makeFileGen = console.askYesNoQuestion(_('%s exists. Overwrite?' % (makefilePath)))
        else:
            makeFileGen = True

        if makeFileGen:
            self._generateMakefile(makefilePath, preferences, projectName, sourcePath)

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _generateMakefile(self, makefilePath, preferences, projectName, sourcePath):
        jinjaEnv = self.getProject().getJinjaEnvironment()
        makefileTemplate = JinjaTemplates.getTemplate(jinjaEnv, 'makefile')
        initRenderParams = {
                            'source' : { 'dir' : sourcePath,
                                         'name' : projectName,
                                    },
                            'arguments' : { 'path' : '--path',
                                    },
                            'preferences' : preferences,
                        }
        
        self.appendCommandTemplates(initRenderParams)
        
        makefileTemplate.renderTo(makefilePath, initRenderParams)
