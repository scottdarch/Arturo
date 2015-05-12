#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import os

from ano import __app_name__, __version__, __lib_name__
from ano.Arturo2 import MissingRequiredFileException
from ano.Arturo2.commands.base import Command, ProjectCommand
from ano.Arturo2.commands.makegen import Make_gen
from ano.Arturo2.templates import JinjaTemplates


# +---------------------------------------------------------------------------+
# | Version
# +---------------------------------------------------------------------------+
class Version(Command):
    '''
    Get versioning information for Arturo/ano.
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
        # TODO: allow commandline arguments to force paroject folders to be treated as source folders.
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

        # finally ask if we want to (re)generate the project makefiles
        if self._force or console.askYesNoQuestion(_("Do you want to (re)generate the project makefiles?")):
            # generate the configuration
            config = project.getConfiguration(preferences['target_package'], 
                                              preferences['target_platform'], 
                                              preferences['board'],
                                              projectName,
                                              sourcePath
                                              )
            makeGenCommand = Make_gen(self.getEnvironment(), project, config, console)
            makeGenCommand.run()

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _generateMakefile(self, makefilePath, preferences, projectName, sourcePath):
        
        
        jinjaEnv = self.getProject().getJinjaEnvironment()
        makefileTemplate = JinjaTemplates.getTemplate(jinjaEnv, JinjaTemplates.MAKEFILE)
        initRenderParams = {
                            'source' : { 'dir' : sourcePath,
                                         'name' : projectName,
                                    },
                            'preferences' : preferences,
                        }
        with open(makefilePath, 'wt') as makefile:
            makefile.write(makefileTemplate.render(initRenderParams))
