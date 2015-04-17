#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import os

import ano
import jinja2
from jinja2.loaders import PackageLoader


class MakefileGenerator(object):
    
    TEMPLATE_MAKEFILE = "Makefile.jinja"
    TEMPLATE_MAKEFILE_HEX = "MakeHex.jinja"
    GENNAME_MAKEFILE = "Makefile"
    
    def __init__(self, builddir, package, platformName, boardName, console):
        super(MakefileGenerator, self).__init__()
        self._package = package
        self._boardName = boardName
        self._platformName = platformName
        self._console = console
        self._jinjaEnv = None
        self._builddir = builddir
        
    def getBuilddir(self):
        return self._builddir
    
    def getJinjaEnvironment(self, baseDir=None):
        if baseDir is None:
            baseDir = os.getcwd()
        if self._jinjaEnv is None:
            self._jinjaEnv = jinja2.Environment(loader=PackageLoader("ano", "Arduino15/templates"))
            self._jinjaEnv.globals['package'] = self._package
            platform = self._package[self._platformName]
            self._jinjaEnv.globals['platform'] = platform
            self._jinjaEnv.globals['board'] = platform[self._boardName]
            self._jinjaEnv.globals['env'] = {
                'version':ano.__version__
            }
        self._jinjaEnv.globals['env']['builddir'] = os.path.relpath(self._builddir, baseDir)
        return self._jinjaEnv
    
    def writeMakefile(self, targetDir=None):
        if targetDir is None:
            targetDir = os.getcwd()
        template = self.getJinjaEnvironment(targetDir).get_template(MakefileGenerator.TEMPLATE_MAKEFILE)
        makefilePath = os.path.join(targetDir, MakefileGenerator.GENNAME_MAKEFILE)
        # TODO: allow overwrite
        print template.render()
#         with open(makefilePath, 'wt') as f:
#             f.write(template.render())
            
    def writeHexCompilerMakefile(self, targetDir=None):
        None
