#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import os

from arturo import __app_name__
from arturo.commands.base import ConfiguredCommand, mkdirs
from arturo.commands.build import Cmd_source_libs
from arturo.libraries import Library
from arturo.templates import JinjaTemplates


# +---------------------------------------------------------------------------+
# | MetaMake_libs
# +---------------------------------------------------------------------------+
class Metamakegen_libs(ConfiguredCommand):
    
    # +-----------------------------------------------------------------------+
    # | Command
    # +-----------------------------------------------------------------------+
    def appendCommandTemplates(self, outTemplates=None):
        templates = super(Metamakegen_libs, self).appendCommandTemplates(outTemplates)
        templates['arguments']['path'] = '--path'
        return templates
    
    def add_parser(self, subparsers):
        return subparsers.add_parser(self.getCommandName(), help=_('Generate {} meta-makefiles for the project.'.format(__app_name__)))
    
    # +-----------------------------------------------------------------------+
    # | ArgumentVisitor
    # +-----------------------------------------------------------------------+
    def onVisitArgParser(self, parser):
        parser.add_argument("-p", "--path", default=None)
        
    def onVisitArgs(self, args):
        if args.path is None:
            self._path = self.getProject().getBuilddir() + JinjaTemplates.TEMPLATES['metamake_libs']
        else:
            self._path = args.path
        
    # +-----------------------------------------------------------------------+
    # | Runnable
    # +-----------------------------------------------------------------------+
    def run(self):
        configuration           = self.getConfiguration()
        jinjaEnv                = configuration.getJinjaEnvironment()
        makefileTemplate        = JinjaTemplates.getTemplate(jinjaEnv, 'metamake_libs')
        builddir                = os.path.dirname(self._path)
        targetsMakefilePath     = self._path
        
        mkdirs(builddir)
        
        initRenderParams = self.appendCommandTemplates()
        
        sourceLibsCommand = self.getCommand(Cmd_source_libs)
        
        libraries = ""
        sources   = ""
        
        for libraryNameAndVersion in sourceLibsCommand.getAllPossibleLibsForProject().iterkeys():
            libraries += libraryNameAndVersion
            libraries += " "
        
        for source in sourceLibsCommand.getAllSources():
            sources += source
            sources += " "
        
        initRenderParams['source'] = {'libs': libraries, 'files': sources}
        
        makefileTemplate.renderTo(targetsMakefilePath, initRenderParams)
