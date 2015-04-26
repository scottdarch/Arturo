#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import os

from ano import i18n
from ano.Arturo2.hardware import Platform
from ano.Arturo2.tools import ToolChain


_ = i18n.language.ugettext
# +---------------------------------------------------------------------------+
# | Package
# +---------------------------------------------------------------------------+
class Package(object):
    
    HARDWARE_DIR = "hardware"
    TOOLS_DIR = "tools"
    
    @classmethod
    def makeToolChainMultikey(cls, name, version):
        return "{}-{}".format(name.lower(), version.lower())
    
    def __init__(self, environment, rootPath, searchPath, console, packageMetaData):
        super(Package, self).__init__()
        self._environment = environment
        self._packagePath = os.path.join(rootPath, packageMetaData['name'])
        self._searchPath = searchPath
        self._console = console
        self._packageMetadata = packageMetaData
        self._toolChainsDict = None

        if not os.path.isdir(self._packagePath):
            raise Exception("%s was not found" % (self._packagePath))

        self._hardwareDir = os.path.join(self._packagePath, Package.HARDWARE_DIR)
        self._platformIndex = None
        
    def getName(self):
        return self._packageMetadata['name']
    
    def getEnvironment(self):
        return self._environment

    def getToolChains(self):
        if not self._toolChainsDict:
            self._toolChainsDict = dict()
            for toolchainMetadata in self._packageMetadata['tools']:
                self._toolChainsDict[Package.makeToolChainMultikey(toolchainMetadata['name'], toolchainMetadata['version'])] = \
                    ToolChain(self, toolchainMetadata, self._console)
        return self._toolChainsDict
    
    def getToolChain(self, name, version):
        return self.getToolChains()[Package.makeToolChainMultikey(name, version)]
    
    def getPlatforms(self):
        if self._platformIndex is None:
            self._platformIndex = dict()
            for platformMetadata in self._packageMetadata['platforms']:
                platform = Platform.ifExistsPlatform(self, self._hardwareDir, self._searchPath, self._console, platformMetadata)
                if platform:
                    if self._console:
                        self._console.printDebug('Found platform "{0}" ({1} version{2})'.format(platformMetadata['name'], 
                            platformMetadata['architecture'], 
                            platformMetadata['version']))
                    self._platformIndex[platformMetadata['name']] = platform
                else:
                    #TODO: store missing platforms for a future "download-platform" command.
                    if self._console:
                        self._console.printWarning(_("Missing platform \"{0}\" ({1} verison {2}). You can download this platform from {3}".format(
                            platformMetadata['name'], 
                            platformMetadata['architecture'], 
                            platformMetadata['version'], 
                            platformMetadata['url'])))
        return self._platformIndex
