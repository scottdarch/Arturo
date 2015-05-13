# -*- coding: utf-8 -*-

#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

# Thanks to (Maemo)[https://wiki.maemo.org/Internationalize_a_Python_application] for this snippit and the
# tutorial

import gettext
import locale
import os

from arturo import __lib_name__


def _init_i18n():
    mo_location = os.path.dirname(__file__)

    # Now we need to choose the language. We will provide a list, and gettext
    # will use the first translation available in the list
    #
    DEFAULT_LANGUAGES = os.environ.get('LANG', '').split(':')
    DEFAULT_LANGUAGES += ['en_US']
     
    lc, encoding = locale.getdefaultlocale()  # @UnusedVariable
    if lc:
        languages = [lc]
    
    # Concat all languages (env + default locale),
    #  and here we have the languages and location of the translations
    languages += DEFAULT_LANGUAGES

    # Lets tell those details to gettext
    gettext.install(True, localedir=None, unicode=1)
    gettext.find(__lib_name__, mo_location)
    gettext.textdomain (__lib_name__)
    gettext.bind_textdomain_codeset(__lib_name__, "UTF-8")
    return gettext.translation(__lib_name__, mo_location, languages=languages, fallback=True)

language = _init_i18n()
