#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import os

from ano import i18n
from ano.Arturo2 import SearchPath
from ano.Arturo2.hardware import Platform
from ano.Arturo2.tools import ToolChain
from collections import OrderedDict


_ = i18n.language.ugettext
# +---------------------------------------------------------------------------+
# | Package
# +---------------------------------------------------------------------------+
class Package(object):
    
    def __init__(self, environment, rootPath, searchPath, console, packageMetaData):
        super(Package, self).__init__()
        self._environment = environment
        self._packagePath = os.path.join(rootPath, packageMetaData['name'])
        self._searchPath = searchPath
        self._console = console
        self._packageMetadata = packageMetaData
        # dictionary (name) of dictionary (version) of ToolChain objects.
        self._toolChainsDict = None

        if not os.path.isdir(self._packagePath):
            raise Exception("%s was not found" % (self._packagePath))

        self._hardwareDir = os.path.join(self._packagePath, SearchPath.ARDUINO15_HARDWARE_PATH)
        self._platformIndex = None
        
    def getName(self):
        return self._packageMetadata['name']
    
    def getEnvironment(self):
        return self._environment

    def getToolChains(self):
        if not self._toolChainsDict:
            self._toolChainsDict = dict()
            for toolchainMetadata in self._packageMetadata['tools']:
                toolchainName = toolchainMetadata['name']
                toolchainVersionName = toolchainMetadata['version']
                try:
                    toolchainVersionsDict = self._toolChainsDict[toolchainName]
                except KeyError:
                    toolchainVersionsDict = dict()
                    self._toolChainsDict[toolchainName] = toolchainVersionsDict
                toolchainVersionsDict[toolchainVersionName] = ToolChain(self, toolchainMetadata, self._console)
            # Now go back through and sort the verion collections
            for name, versions in self._toolChainsDict.iteritems():
                self._toolChainsDict[name] = OrderedDict(sorted(versions.items(), reverse=True))
        return self._toolChainsDict
    
    def getToolChain(self, name, version):
        return self.getToolChains()[name][version]
    
    def getToolChainByNameAndVerison(self, nameAndVersion):
        '''
        Tries to parse the provided string using non-standard name-version macro key. For example the Intel
        platform.txt has the following macro:
        
            {runtime.tools.i586-poky-linux-uclibc-1.6.2+1.0.path}
    
        In this case getToolChainByNameAndVersion should be called with "i586-poky-linux-uclibc-1.6.2+1.0"
        as an argument which should parse out to { "name" : "i586-poky-linux-uclibc", "version": 1.6.2+1.0 }.
        We assume that the last hyphen is the delinator.
        '''
        lastHyphen = nameAndVersion.rfind('-')
        if lastHyphen == -1:
            raise ValueError("{} is not a hyphenated name-value string.".format(nameAndVersion))

        name = nameAndVersion[:lastHyphen]
        version = nameAndVersion[lastHyphen+1:]
        
        return self.getToolChain(name, version)
    
    def getToolChainLatestVersion(self, name):
        versions = self.getToolChains()[name]
        for version in versions.itervalues():
            return version
        return None
    
    def getToolChainLatestAvailableVersion(self, name):
        versions = self.getToolChains()[name]
        for version in versions.itervalues():
            if version.getHostToolChain().exists():
                return version
        return None
        
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
                    self._platformIndex[platformMetadata['architecture']] = platform
                else:
                    #TODO: store missing platforms for a future "download-platform" command.
                    if self._console:
                        self._console.printVerbose(_("Missing platform \"{0}\" ({1} verison {2}). You can download this platform from {3}".format(
                            platformMetadata['name'], 
                            platformMetadata['architecture'], 
                            platformMetadata['version'], 
                            platformMetadata['url'])))
        return self._platformIndex
