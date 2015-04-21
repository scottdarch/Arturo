#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import errno
import os

from ano.Arturo2.templates import JinjaTemplates


class MakefileGenerator(object):
    
    def __init__(self, configuration, console):
        super(MakefileGenerator, self).__init__()
        self._configuration = configuration
        self._console = console
        
    def getBuilddir(self):
        return self._builddir
    
    def writeMakeTargets(self):
        jinjaEnv = self._configuration.getJinjaEnvironment()
        template = JinjaTemplates.getTemplate(jinjaEnv, JinjaTemplates.MAKEFILE_TARGETS)
        builddir = self._configuration.getBuilddir()
        makefilePath = os.path.join(self._configuration.getBuilddir(), JinjaTemplates.MAKEFILE_TARGETS)
        self._mkdirs(builddir)
        with open(makefilePath, 'wt') as f:
            f.write(template.render())

    def writeMakeHex(self, targetDir=None):
        None

    # +-----------------------------------------------------------------------+
    # | PRIVATE
    # +-----------------------------------------------------------------------+
    def _mkdirs(self, path):
        '''
        Thanks (stack overflow)[https://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python]
        '''
        try:
            os.makedirs(path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise