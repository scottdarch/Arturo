#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import json
import os

from ano import __version__, i18n
from ano.Arturo2 import SearchPath, Preferences, SearchPathAgent
from ano.Arturo2.parsers import MakefilePropertyParser
from ano.Arturo2.templates import JinjaTemplates
from ano.Arturo2.vendors import Package


_ = i18n.language.ugettext

# +---------------------------------------------------------------------------+
# | Configuration
# +---------------------------------------------------------------------------+
class ConfigurationHeaderAggregator(SearchPathAgent):
    
    ARTURO2_HEADER_FILEEXT = ("h", "hpp")
    
    def __init__(self, configuration, console):
        super(ConfigurationHeaderAggregator, self).__init__(console, followLinks=True)
        self._configuration = configuration
        self._console = console
        self._headers = list()

    def getResults(self):
        return self._headers

    def onVisitFile(self, parentPath, rootPath, containingFolderName, filename, fqFilename):
        splitName = filename.split('.')
        if len(splitName) == 2 and splitName[1] in ConfigurationHeaderAggregator.ARTURO2_HEADER_FILEEXT:
            self._headers.append(fqFilename)
        return SearchPathAgent.KEEP_GOING
    
class Configuration(object):
    '''
    An environment with package, platform, board, uploader, and other targeting parameters defined.
    '''
    
    def __init__(self, project, packageName, platformName, boardName, projectName, sourceRoot, preferences=None, console=None):
        super(Configuration, self).__init__()
        self._project = project
        self._console = console
        self._packageName = packageName
        self._projectName = projectName
        self._prefs = preferences
        self._platformName = platformName
        self._boardName = boardName
        self._sourcePath = os.path.join(project.getPath(), sourceRoot)
        self._package = None
        self._platform = None
        self._board = None
        self._jinjaEnv = None
        self._builddir = None
        self._headers = None
        
    def getJinjaEnvironment(self):
        if self._jinjaEnv is None:
            self._jinjaEnv = self._project.getJinjaEnvironment()
            self._jinjaEnv.globals['config'] = {
                'board': self._boardName,
                'target_platform' : self._platformName,
                'target_package' : self._packageName,
                'preferences' : self._prefs
            }
        return self._jinjaEnv

    def getProject(self):
        return self._project

    def getProjectName(self):
        return self._projectName
    
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
    
    def getSourcePath(self):
        return self._sourcePath

    def getHeaders(self):
        if self._headers is None:
            self._headers = self.getProject().getEnvironment().getSearchPath().scanDirs(
                 self._sourcePath, ConfigurationHeaderAggregator(self, self._console)).getResults()
        return self._headers

# +---------------------------------------------------------------------------+
# | Project
# +---------------------------------------------------------------------------+
class ProjectSourceRootAggregator(SearchPathAgent):
    
    ARTURO2_MAIN_FILEEXT = ("cpp", "c", "ino")
    
    def __init__(self, project, console):
        super(ProjectSourceRootAggregator, self).__init__(console, followLinks=True)
        self._project = project
        self._console = console
        self._sourceRoots = []

    def getResults(self):
        return self._sourceRoots

    def onVisitFile(self, parentPath, rootPath, containingFolderName, filename, fqFilename):
        splitName = filename.split('.')
        if len(splitName) == 2 and splitName[1] in ProjectSourceRootAggregator.ARTURO2_MAIN_FILEEXT:
            if containingFolderName == splitName[0]:
                self._sourceRoots.append([parentPath, containingFolderName, filename])
        return SearchPathAgent.KEEP_GOING
    
class Project(object):
    
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
            self._builddir = os.path.join(self._path, SearchPath.ARTURO2_BUILDDIR_NAME)
        return self._builddir

    def getPath(self):
        return self._path

    def getMakefilePath(self):
        return os.path.join(self._path, JinjaTemplates.MAKEFILE)
        
    def getName(self):
        return self._name
    
    def getLastConfiguration(self):
        '''
        The configuration as last specified in preferences.
        '''
        
        #TODO: handle missing preferences
        preferences = self._env.getPreferences();
        
        #TODO: handle missing makefile error
        #TODO: check makefile version against Arturo version.
        mergedPreferences = MakefilePropertyParser.parse(os.path.join(self._path, JinjaTemplates.MAKEFILE), preferences, self._console);
        
        packageName = mergedPreferences['target_package']
        platformName = mergedPreferences['target_platform']
        boardName = mergedPreferences['board']
        projectName = mergedPreferences['project_name']
        sourceRoot = mergedPreferences['dir_source']
        
        return Configuration(self, packageName, platformName, boardName, projectName, sourceRoot, mergedPreferences, self._env.getConsole())
    
    def getConfiguration(self, packageName, platformName, boardName, projectName, sourceRoot):
        return Configuration(self, packageName, platformName, boardName, projectName, sourceRoot, None, self._env.getConsole())
    
    def getSourceRoots(self):
        return self.getEnvironment().getSearchPath().scanDirs(
                 self._path, ProjectSourceRootAggregator(self, self._console)).getResults()
   
# +---------------------------------------------------------------------------+
# | Environment
# +---------------------------------------------------------------------------+

class Environment(object):
    '''
    All available configurations for the given project.
    '''
    
    PACKAGE_INDEX_NAMES = ['package_index.json']
    
    def __init__(self, console):
        super(Environment, self).__init__()
        self._console = console
        self._searchPath = None
        self._packages = None
        self._preferences = None
        self._inferredProject = None
        self._packageRootPath = None
        self._packageMetadataIndex = None
        self._packageIndex = None
        
    def getConsole(self):
        return self._console
    
    def getSearchPath(self):
        if self._searchPath is None:
            self._searchPath = SearchPath(self._console)
        return self._searchPath
    
    def getPackages(self):
        if self._packageIndex is None:
            self._packageIndex = dict()
            for packageName, packageMetadata in self._getPackageMetadata().iteritems():
                self._packageIndex[packageName] = Package(self, self._packageRootPath, self._searchPath, self._console, packageMetadata)

        return self._packageIndex
    
    def getPreferences(self):
        if self._preferences is None:
            self._preferences = Preferences(self.getSearchPath(), self.getConsole())
        return self._preferences
    
    def getInferredProject(self):
        if self._inferredProject is None:
            self._inferredProject = Project.infer(self)
        return self._inferredProject
    
    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+

    def _getPackageMetadata(self):
        if self._packageMetadataIndex is not None:
            return self._packageMetadataIndex
        
        packageMetadataPath = self.getSearchPath().findFirstFileOfNameOrThrow(Environment.PACKAGE_INDEX_NAMES, 'package index')
        
        # the package folders are found under a folder ARDUINO15_PACKAGES_PATH next to the packages index file
        self._packageRootPath = os.path.join(os.path.dirname(packageMetadataPath), SearchPath.ARDUINO15_PACKAGES_PATH)
        
        with open(packageMetadataPath, 'r') as packageMetadataFile:
            packageMetadataCollection = json.load(packageMetadataFile)

        packageMetadataList = packageMetadataCollection['packages']
        self._packageMetadataIndex = dict()
        for packageMetadata in packageMetadataList:
            self._packageMetadataIndex[packageMetadata['name']] = packageMetadata
        
        return self._packageMetadataIndex;
