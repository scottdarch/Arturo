#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import json
import os

from arturo import SearchPath, Preferences, SearchPathAgent, Arduino15PackageSearchPathAgent, \
    ConfigurationHeaderAggregator, ConfigurationSourceAggregator, __lib_name__
from arturo import __version__, i18n, __app_name__
from arturo.libraries import Library
from arturo.parsers import MakefilePropertyParser
from arturo.templates import JinjaTemplates
from arturo.vendors import Package


_ = i18n.language.ugettext

# +---------------------------------------------------------------------------+
# | Configuration
# +---------------------------------------------------------------------------+
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
        self._headerPaths = None
        self._sources = None
        self._libraries = None
        
    def getJinjaEnvironment(self):
        if self._jinjaEnv is None:
            self._jinjaEnv = self._project.getJinjaEnvironment()
            self._jinjaEnv.globals['config'] = {
                'board': self._boardName,
                'target_platform' : self._platformName,
                'target_package' : self._packageName,
                'preferences' : self._prefs,
            }
        return self._jinjaEnv

    def getEnvironment(self):
        return self._project.getEnvironment()

    def getProject(self):
        return self._project

    def getProjectName(self):
        return self._projectName
    
    def getPackage(self):
        if self._package is None:
            self._package = self._project.getEnvironment().getPackages()[self._packageName]
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

    def getHeaders(self, dirnameonly=False):
        headers = self._headerPaths if (dirnameonly) else self._headers
        if headers is None and self._sourcePath is not None:
            if self._headers is None:
                self._headers = self.getProject().getEnvironment().getSearchPath().scanDirs(
                     self._sourcePath, ConfigurationHeaderAggregator(self, self._console)).getResults()
            
            if dirnameonly and self._headerPaths is None:
                paths = set()
                for header in self._headers:
                    paths.add(os.path.dirname(header))
                self._headerPaths = list(paths)

            headers = self._headerPaths if (dirnameonly) else self._headers

        return headers

    def getSources(self):
        if self._sources is None:
            self._sources = self.getProject().getEnvironment().getSearchPath().scanDirs(
                 self._sourcePath, ConfigurationSourceAggregator(self, self._console)).getResults()
        return self._sources

    def getLibraries(self):
        if self._libraries is None:
            self._libraries = dict()
            self._libraries.update(self.getEnvironment().getLibraries())
            self._libraries.update(self.getPlatform().getLibraries())
            self._libraries.update(self.getProject().getLibraries())
        return self._libraries

# +---------------------------------------------------------------------------+
# | Project
# +---------------------------------------------------------------------------+
class ProjectSourceRootAggregator(Arduino15PackageSearchPathAgent):
    '''
    SearchPathAgent that looks for the Arduino15 "[token]/[token].[extension]" pattern
    used to signify both sketch folders (e.g. sketch/sketch.ino) or library folders
    (e.g. library/library.h).
    '''
    
    def __init__(self, project, console, exclusions=None):
        super(ProjectSourceRootAggregator, self).__init__(SearchPath.ARTURO2_SOURCE_FILEEXT, console, exclusions=exclusions, followLinks=True)
        self._project = project

    def onVisitPackage(self, parentPath, rootPath, packageName, filename):
        if os.path.basename(parentPath) not in SearchPath.ARDUINO15_LIBRARY_FOLDER_NAMES:
            self._addResult([parentPath, packageName, filename])
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
        self._libraries = None
        
     
    def getEnvironment(self):
        return self._env

    def getJinjaEnvironment(self):
        if self._jinjaEnv is None:
            self._jinjaEnv = JinjaTemplates.createJinjaEnvironmentForTemplates()
            #TODO: inject app name since apps other than ano might use arturo
            self._jinjaEnv.globals['env'] = {
                'version':__version__,
                'app_name':__app_name__,
                'lib_name':__lib_name__
            }
            self._jinjaEnv.globals['project'] = {
                'builddir':os.path.relpath(self.getBuilddir())
            }
        return self._jinjaEnv
    
    def getBuilddir(self):
        if self._builddir is None:
            self._builddir = os.path.join(self._path, SearchPath.ARTURO2_BUILDDIR_NAME)
        return self._builddir

    def getMakefilePath(self):
        return os.path.join(self._path, JinjaTemplates.TEMPLATES['makefile'])

    def getPath(self):
        return self._path

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
        mergedPreferences = MakefilePropertyParser.parse(os.path.join(self._path, JinjaTemplates.TEMPLATES['makefile']), preferences, self._console);
        
        packageName = mergedPreferences['target_package']
        platformName = mergedPreferences['target_platform']
        boardName = mergedPreferences['board']
        projectName = mergedPreferences['project_name']
        sourceRoot = mergedPreferences['dir_source']
        
        return Configuration(self, packageName, platformName, boardName, projectName, sourceRoot, mergedPreferences, self._env.getConsole())
    
    def getConfiguration(self, packageName, platformName, boardName, projectName, sourceRoot):
        return Configuration(self, packageName, platformName, boardName, projectName, sourceRoot, None, self._env.getConsole())
    
    def getSourceRoots(self, treatAsSourceFolders=None):
        sourceRoots = self.getEnvironment().getSearchPath().scanDirs(
                 self._path, ProjectSourceRootAggregator(self, self._console, exclusions=SearchPath.ARDUINO15_LIBRARY_FOLDER_NAMES)).getResults()
        if treatAsSourceFolders is not None:
            for forcedSource in treatAsSourceFolders:
                forcedSourceProjectPath = os.path.join(self._path, forcedSource)
                if os.path.isdir(forcedSourceProjectPath):
                    sourceRoots.append([self._path, forcedSource, None])
        return sourceRoots

    def getLibraries(self):
        if self._libraries is None:
            # treat anything in a "library" folder under the project path as a library
            projectPath = self.getPath()
            forceTreatAsLibraries = list()
            for folderName in SearchPath.ARDUINO15_LIBRARY_FOLDER_NAMES:
                forceTreatAsLibraries.append(os.path.join(projectPath, folderName))
            self._libraries = self.getEnvironment().getLibrariesFor(projectPath, forceTreatAsLibraries)

        return self._libraries


# +---------------------------------------------------------------------------+
# | Environment
# +---------------------------------------------------------------------------+

class Environment(object):
    '''
    All available configurations for the given project.
    '''
    
    PACKAGE_INDEX_NAMES = ['package_index.json']
    LIBRARY_INDEX_NAMES = ['library_index.json']
    
    def __init__(self, console):
        super(Environment, self).__init__()
        self._console = console
        self._searchPath = None
        self._packages = None
        self._preferences = None
        self._inferredProject = None
        self._packageRootPath = None
        self._packageMetadataIndex = None
        self._libraryMetadataIndex = None
        self._packageIndex = None
        self._libraryIndex = None


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

    def getLibraries(self):
        #TODO: search environment for any libraries on the system path
        if self._libraryIndex is None:
            self._libraryIndex = dict()
            for meta_data in self._getLibraryMetadata().itervalues():
                libraryName = meta_data['name']
                libraryVersion = meta_data['version']
                library = Library(libraryName, self, self._console, libraryVersion)
                if not self._libraryIndex.has_key(libraryName):
                    self._libraryIndex[libraryName] = dict()
                self._libraryIndex[libraryName][libraryVersion] = library

            for searchPath in self.getSearchPath().getPaths():
                self._libraryIndex.update(self.getLibrariesFor(searchPath, continueOnError=True))

        return self._libraryIndex
    
    def getLibrariesFor(self, path, forcedLibrariesPaths=None, continueOnError=False, platform=None):
        libraries = dict()
        for foldername in SearchPath.ARDUINO15_LIBRARY_FOLDER_NAMES:
            librariesDir = os.path.join(path, foldername)
            if os.path.isdir(librariesDir):
                for item in os.listdir(librariesDir):
                    libraryDir = os.path.join(librariesDir, item)
                    if os.path.isdir(libraryDir):
                        try:
                            library = Library.fromDir(self, libraryDir, self._console, platform)
                        except ValueError as e:
                            if forcedLibrariesPaths:
                                prefixList = list(forcedLibrariesPaths)
                                prefixList.append(libraryDir)
                                if os.path.commonprefix(prefixList) in forcedLibrariesPaths:
                                    # Any folder under a "forced path" is considered a library.
                                    library = Library(os.path.basename(libraryDir), self, self._console, libraryPath=libraryDir, libraryPlatform=platform)

                            elif continueOnError:
                                self.getConsole().printDebug(_("{} was not a well-formed library.".format(libraryDir)))
                                continue
                            else:
                                raise e
                        if not libraries.has_key(library.getName()):
                            libraries[library.getName()] = dict()
                        libraries[library.getName()][library.getVersion()] = library

        return libraries

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _getLibraryMetadata(self):
        if self._libraryMetadataIndex is not None:
            return self._libraryMetadataIndex
        
        libraryMetadataPath = self.getSearchPath().findFirstFileOfNameOrThrow(Environment.LIBRARY_INDEX_NAMES, 'library index')
        
        # the package folders are found under a folder ARDUINO15_PACKAGES_PATH next to the packages index file
        if self._packageRootPath is None:
            self._packageRootPath = os.path.join(os.path.dirname(libraryMetadataPath), SearchPath.ARDUINO15_PACKAGES_PATH)
        
        with open(libraryMetadataPath, 'r') as libraryMetadataFile:
            libraryMetadataCollection = json.load(libraryMetadataFile)

        libraryMetadataList = libraryMetadataCollection['libraries']
        self._libraryMetadataIndex = dict()
        for libraryMetadata in libraryMetadataList:
            library_name_and_version = Library.libNameFromNameAndVersion(libraryMetadata['name'], libraryMetadata['version'])
            self._libraryMetadataIndex[library_name_and_version] = libraryMetadata
        
        return self._libraryMetadataIndex;


    def _getPackageMetadata(self):
        if self._packageMetadataIndex is not None:
            return self._packageMetadataIndex
        
        packageMetadataPath = self.getSearchPath().findFirstFileOfNameOrThrow(Environment.PACKAGE_INDEX_NAMES, 'package index')
        
        # the package folders are found under a folder ARDUINO15_PACKAGES_PATH next to the packages index file
        if self._packageRootPath is None:
            self._packageRootPath = os.path.join(os.path.dirname(packageMetadataPath), SearchPath.ARDUINO15_PACKAGES_PATH)
        
        with open(packageMetadataPath, 'r') as packageMetadataFile:
            packageMetadataCollection = json.load(packageMetadataFile)

        packageMetadataList = packageMetadataCollection['packages']
        self._packageMetadataIndex = dict()
        for packageMetadata in packageMetadataList:
            self._packageMetadataIndex[packageMetadata['name']] = packageMetadata
        
        return self._packageMetadataIndex;
