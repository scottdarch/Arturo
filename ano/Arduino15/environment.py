#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import os

from ano import Console
from ano.Arduino15 import SearchPath, Preferences
from ano.Arduino15.vendors import Packages

from ano.Arduino15.make import MakefileGenerator


class Environment(object):
    
    BUILDDIR = ".build_ano"
    
    def __init__(self):
        super(Environment, self).__init__()
        self._console = Console()
        self._searchPath = None
        self._packages = None
        self._preferences = None
        self._makefileGenerator = None
        self._builddir = None
        
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
    
    def getBuilddir(self):
        if self._builddir is None:
            self._builddir = os.path.join(os.getcwd(), Environment.BUILDDIR)
        return self._builddir
    
    def getMakefileGenerator(self, package, platformName, boardName):
        if self._makefileGenerator is None:
            self._makefileGenerator = MakefileGenerator(self.getBuilddir(), self.getPackages()[package], platformName, boardName, self.getConsole())
        return self._makefileGenerator
    