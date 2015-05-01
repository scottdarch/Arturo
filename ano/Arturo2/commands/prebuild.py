#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import os

from ano import __app_name__, __version__
from ano.Arturo2.commands.base import Command, ProjectCommand
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
        
        # first choose a project "main"
        sourceRoots = project.getSourceRoots()
        sourceRoot = None
        if len(sourceRoots) > 0:
            projectList = list()
            for rootPath, rootName, mainSource in sourceRoots:  # @UnusedVariable
                projectList.append([rootName, mainSource])
            sourceRoot = sourceRoots[self._console.askPickOneFromList(_("Which project?"), projectList)]
        else:
            sourceRoot = sourceRoots[0]
            
        # next use the IDE's preferences to populate our makefile
        preferences = project.getEnvironment().getPreferences()
        
        # finally setup the top level makefile
        makefilePath = project.getMakefilePath()
        sourcePath = os.path.relpath(os.path.join(sourceRoot[0], sourceRoot[1]), os.path.dirname(makefilePath))
        
        if os.path.exists(makefilePath):
            message = _('%s exists. Overwrite? ' % (makefilePath))
            if not self._console.askYesNoQuestion(message):
                return
        jinjaEnv = project.getJinjaEnvironment()
        makefileTemplate = JinjaTemplates.getTemplate(jinjaEnv, JinjaTemplates.MAKEFILE)
        initRenderParams = {
                            'source' : { 'dir' : sourcePath,
                                         'name' : sourceRoot[1],
                                    },
                            'preferences' : preferences,
                        }
        with open(makefilePath, 'wt') as makefile:
            makefile.write(makefileTemplate.render(initRenderParams))
            