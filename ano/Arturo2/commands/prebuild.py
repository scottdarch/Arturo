#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import os

from ano import __app_name__, __version__
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
        self.getConsole().printInfo(_('{} {}'.format(__app_name__, __version__)))
        
# +---------------------------------------------------------------------------+
# | Init
# +---------------------------------------------------------------------------+
class Init(ProjectCommand):
    '''
    Safe initialization of a project with the Arturo generated makefile. Once this command completes
    the project should be buildable using make.
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
        project = self.getProject()
        console = self.getConsole()
        
        # first choose a project "main"
        sourceRoots = project.getSourceRoots()
        sourceRoot = None
        if len(sourceRoots) > 0:
            projectList = list()
            for rootPath, rootName, mainSource in sourceRoots:  # @UnusedVariable
                projectList.append([rootName, mainSource])
            sourceRoot = sourceRoots[console.askPickOneFromList(_("Which project?"), projectList)]
        else:
            sourceRoot = sourceRoots[0]
            

        # next use the IDE's preferences to populate our makefile
        preferences = project.getEnvironment().getPreferences()
        
        # setup the top level makefile
        makefilePath = project.getMakefilePath()
        sourcePath = os.path.relpath(os.path.join(sourceRoot[0], sourceRoot[1]), os.path.dirname(makefilePath))
        projectName = sourceRoot[1]
        
        if os.path.exists(makefilePath):
            message = _('%s exists. Overwrite?' % (makefilePath))
            if console.askYesNoQuestion(message):
                self._generateMakefile(makefilePath, preferences, projectName, sourcePath)

        # finally ask if we want to (re)generate the project makefiles
        if console.askYesNoQuestion(_("Do you want to (re)generate the project makefiles?")):
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
