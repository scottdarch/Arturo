#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import json
import os

from ano.Arduino15.hardware import Platform


# +---------------------------------------------------------------------------+
# | Package
# +---------------------------------------------------------------------------+
class Package(object):
    
    HARDWARE_DIR = "hardware"
    TOOLS_DIR = "tools"
    
    def __init__(self, rootPath, searchPath, console, packageMetaData):
        super(Package, self).__init__()
        self._packagePath = os.path.join(rootPath, packageMetaData['name'])
        self._searchPath = searchPath
        self._console = console
        self._packageMetadata = packageMetaData

        if not os.path.isdir(self._packagePath):
            raise Exception("%s was not found" % (self._packagePath))

        self._hardwareDir = os.path.join(self._packagePath, Package.HARDWARE_DIR)
        self._platformIndex = None
    
    def getPlatforms(self):
        if self._platformIndex is None:
            self._platformIndex = dict()
            for platformMetadata in self._packageMetadata['platforms']:
                platform = Platform(self._hardwareDir, self._searchPath, self._console, platformMetadata)
                self._platformIndex[platformMetadata['name']] = platform
        return self._platformIndex
    
    # +-----------------------------------------------------------------------+
    # | PYTHON DATA MODEL
    # +-----------------------------------------------------------------------+
    def __getitem__(self, key):
        return self.getPlatforms()[key]
    
# +---------------------------------------------------------------------------+
# | Packages
# +---------------------------------------------------------------------------+
class Packages(object):
    
    PACKAGES_PATH = "packages"
    PACKAGE_INDEX_NAMES = ['package_index.json']
    
    def __init__(self, searchPath, console):
        super(Packages, self).__init__()
        self._searchPath = searchPath
        self._console = console
        self._packageRootPath = None
        self._packageMetadataIndex = None
        self._packageIndex = None

    def getPackage(self, packageName):
        return self.getPackages()[packageName]

    def getPackages(self):
        if self._packageIndex is None:
            self._packageIndex = dict()
            for packageName, packageMetadata in self._getPackageMetadata().iteritems():
                self._packageIndex[packageName] = Package(self._packageRootPath, self._searchPath, self._console, packageMetadata)

        return self._packageIndex
        
    def __getitem__(self, key):
        return self.getPackages()[key]

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+

    def _getPackageMetadata(self):
        if self._packageMetadataIndex is not None:
            return self._packageMetadataIndex
        
        packageMetadataPath = self._searchPath.findFirstFileOfNameOrThrow(Packages.PACKAGE_INDEX_NAMES)
        
        # the package folders are found under a folder Packages.PACKAGES_PATH next to the packages index file
        self._packageRootPath = os.path.join(os.path.dirname(packageMetadataPath), Packages.PACKAGES_PATH)
        
        with open(packageMetadataPath, 'r') as packageMetadataFile:
            packageMetadataCollection = json.load(packageMetadataFile)

        packageMetadataList = packageMetadataCollection['packages']
        self._packageMetadataIndex = dict()
        for packageMetadata in packageMetadataList:
            self._packageMetadataIndex[packageMetadata['name']] = packageMetadata
        
        return self._packageMetadataIndex;
