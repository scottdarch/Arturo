#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import os

from ano import Console, __version__, i18n
from ano.Arduino15 import SearchPath, Preferences
from ano.Arduino15.make import MakefileGenerator
from ano.Arduino15.templates import JinjaTemplates
from ano.Arduino15.vendors import Packages

_ = i18n.language.ugettext

class Configuration(object):
    '''
    An environment with package, platform, board, uploader, and other targeting parameters defined.
    '''
    
    def __init__(self, project, packageName, platformName, boardName, console):
        super(Configuration, self).__init__()
        self._project = project
        self._console = console
        self._packageName = packageName
        self._package = None
        self._platformName = platformName
        self._platform = None
        self._boardName = boardName
        self._board = None
        self._makefileGenerator = None
        self._jinjaEnv = None
        self._builddir = None
        
    def getJinjaEnvironment(self):
        if self._jinjaEnv is None:
            self._jinjaEnv = self._project.getJinjaEnvironment()
            self._jinjaEnv.globals['config'] = {
                'board': self._boardName,
                'target_platform' : self._platformName,
                'target_package' : self._packageName
            }
        return self._jinjaEnv
    
    def getPackage(self):
        if self._package is None:
            self._package = self._project.getEnvironment().getPackage()[self._packageName]
        return self._package
    
    def getPlatform(self):
        if self._platform is None:
            self._platform = self.getPackage().getPlatforms()[self._platformName]
        return self._platform

    def getBoard(self):
        if self._board is None:
            self._board = self.getPlatform().getBoards()[self._boardName]
        return self._board
    
    def getBuilddir(self):
        if self._builddir is None:
            self._builddir = os.path.join(self._project.getBuilddir(), self._boardName)
        return self._builddir
    
    def getMakefileGenerator(self):
        if self._makefileGenerator is None:
            self._makefileGenerator = MakefileGenerator(self, self._console)
        return self._makefileGenerator
        
    
class Project(object):
    
    CONFIG_FILE = "preferences.txt.jinja"
    BUILDDIR = ".build_ano"
    TOPLEVEL_MAKE = "Makefile"
        
    @classmethod
    def infer(cls, environment):
        currentDir = os.getcwd()
        os.path.basename(currentDir)
        return Project(os.path.basename(currentDir), currentDir, environment, environment.getConsole())
    
    def __init__(self, name, path, environment, console):
        super(Project, self).__init__()
        self._env = environment
        self._console = console
        self._path = path
        self._name = name;
        self._builddir = None
        self._jinjaEnv = None
     
    def getEnvironment(self):
        return self._env

    def getJinjaEnvironment(self):
        if self._jinjaEnv is None:
            self._jinjaEnv = JinjaTemplates.createJinjaEnvironmentForTemplates()
            self._jinjaEnv.globals['env'] = {
                'version':__version__
            }
            self._jinjaEnv.globals['project'] = {
                'builddir':os.path.relpath(self.getBuilddir())
            }
        return self._jinjaEnv
    
    def getBuilddir(self):
        if self._builddir is None:
            self._builddir = os.path.join(self._path, Project.BUILDDIR)
        return self._builddir
       
    def initProjectDir(self):
        makefilePath = os.path.join(self._path, Project.TOPLEVEL_MAKE)
        if os.path.exists(makefilePath):
            message = _('%s exists. Overwrite? ' % (makefilePath))
            if not self._console.askYesNoQuestion(message):
                return
        jinjaEnv = self.getJinjaEnvironment()
        makefileTemplate = jinjaEnv.get_template(Project.TOPLEVEL_MAKE + ".jinja")
        with open(makefilePath, 'wt') as makefile:
            makefile.write(makefileTemplate.render())
        
    def getName(self):
        return self._name
    
    def getLastConfiguration(self):
        '''
        The configuration as last specified in preferences.
        '''
        preferences = self._env.getPreferences();
        packageName = preferences['target_package']
        platformName = preferences['target_platform']
        boardName = preferences['board']
        return self.getConfiguration(packageName, platformName, boardName)
    
    def getConfiguration(self, packageName, platformName, boardName):
        return Configuration(self, packageName, platformName, boardName, self._env.getConsole())
        
class Environment(object):
    '''
    All available configurations for the given project.
    '''
    
    def __init__(self):
        super(Environment, self).__init__()
        self._console = Console()
        self._searchPath = None
        self._packages = None
        self._preferences = None
        self._inferredProject = None
        
    def getConsole(self):
        return self._console
    
    def getSearchPath(self):
        if self._searchPath is None:
            self._searchPath = SearchPath()
        return self._searchPath
    
    def getPackages(self):
        if self._packages is None:
            self._packages = Packages(self.getSearchPath(), self.getConsole())
        return self._packages
    
    def getPreferences(self):
        if self._preferences is None:
            self._preferences = Preferences(self.getSearchPath(), self.getConsole())
        return self._preferences
    
    def getInferredProject(self):
        if self._inferredProject is None:
            self._inferredProject = Project.infer(self)
        return self._inferredProject
    