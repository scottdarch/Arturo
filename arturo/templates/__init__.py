#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import os

from arturo import __app_name__, __lib_name__
import jinja2
from jinja2.loaders import PackageLoader

class JinjaTemplate(object):
    '''
    Wrapper around a jinja2 template object which sets up the provided environment for the template when rendered.
    '''
    
    JINJASUFFIX = ".jinja"
    
    def __init__(self, jinjaEnvironment, templateName, templateFileName, parentTemplateName=None):
        self._name = templateName
        self._fileName = templateFileName
        self._parentTemplate = parentTemplateName + self.JINJASUFFIX if parentTemplateName is not None else None
        self._template = None
        self._jinjaEnv = jinjaEnvironment
    
    def getTemplate(self):
        if self._template is None:
            self._template = self._jinjaEnv.get_template(self._fileName + self.JINJASUFFIX, parent=self._parentTemplate)
        return self._template
    
    def renderTo(self, targetFilePath, params):
        with open(targetFilePath, 'wt') as f:
            f.write(self.render(targetFilePath, params))
            f.write('\n')

    def render(self, targetFilePath, params):
        try:
            params['this'] = {
                    'name'     : self._name,
                    'filename' : os.path.basename(targetFilePath),
                    'path'     : targetFilePath,
                }
            return self.getTemplate().render(params)
        finally:
            params.pop('this')


class JinjaTemplates(object):
    
    TEMPLATES = {
                 "make_bin"            : "MakeBin.mk",
                 "make_toolchain"      : "MakeToolchain.mk",
                 "make_staticlib"      : "MakeStaticLib.mk",
                 "metamake_libs"       : "MakeMetaLibs.mk",
                 "make_lib"            : "MakeLib.mk",
                 "makefile"            : "Makefile",
                 "make_clearvars"      : "MakeClearVars.mk",
                }
    
    @classmethod
    def getRelPathToTemplatesFromPackage(cls):
        return os.path.relpath(os.path.dirname(__file__), __lib_name__)
   
    @classmethod
    def createJinjaEnvironmentForTemplates(cls):
        jinjaEnv = jinja2.Environment(loader=PackageLoader(__lib_name__, cls.getRelPathToTemplatesFromPackage()))
        jinjaEnv.globals['templates'] = JinjaTemplates.TEMPLATES
        return jinjaEnv
        
    @classmethod
    def getTemplate(cls, jinjaEnvironment, templateName, parentTemplateName=None):
        return JinjaTemplate(jinjaEnvironment, templateName, cls.TEMPLATES[templateName], parentTemplateName)
