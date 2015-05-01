#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#
import os

from ano import __app_name__
import jinja2
from jinja2.loaders import PackageLoader


class JinjaTemplates(object):
    
    JINJASUFFIX = ".jinja"
    
    MAKEFILE_TARGETS   = "MakeTargets.mk"
    MAKEFILE           = "Makefile"
    
    @classmethod
    def getRelPathToTemplatesFromPackage(cls):
        return os.path.relpath(os.path.dirname(__file__), __app_name__)
    
    @classmethod
    def createJinjaEnvironmentForTemplates(cls):
        env = jinja2.Environment(loader=PackageLoader(__app_name__, cls.getRelPathToTemplatesFromPackage()))
        env.globals['templates'] = {
            'make_targets':cls.MAKEFILE_TARGETS,
            'makefile':cls.MAKEFILE
        }
        return env
        
    @classmethod
    def getTemplate(cls, jinjaEnvironment, templateName):
        return jinjaEnvironment.get_template(templateName + cls.JINJASUFFIX)
