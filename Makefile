#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

# Local overrides for building Arturo _not_ for building _with_ Arturo (i.e. this 
# file is not used by ano). To override Arturo/ano values for a project use a 
# preferences.txt or modify the preferences.txt controlled by the Arduino IDE.
-include local.mk

# +---------------------------------------------------------------------------+
# | BUILD VARIABLES
# +---------------------------------------------------------------------------+
APP_NAME                     := ano
LIB_NAME                     := arturo
APP_VERSION                  := 2.0.0
LOCALES                      += en_US \

# +---------------------------------------------------------------------------+
# | BUILD TOOLS (you can override these by setting a value in local.mk)
# +---------------------------------------------------------------------------+
XGETTEXT                    ?= xgettext
MSGFMT                      ?= msgfmt
MSGINIT                     ?= msginit
PYTHON                      ?= python2
PYTHON_VERSION              ?= 2.7
PIP                         ?= pip

# +---------------------------------------------------------------------------+
# | BUILD LOCATIONS
# +---------------------------------------------------------------------------+
BUILDDIR                    := build
PYTHON_SOURCE_FOLDER        := $(LIB_NAME)
INTERMEDIATES_FOLDER        := .intermediates
TRANSLATIONS_INTERMEDIATES  := $(INTERMEDIATES_FOLDER)/pots
TRANSLATIONS_DIR            := $(PYTHON_SOURCE_FOLDER)/i18n
EGG_FOLDER                  := $(LIB_NAME).egg-info
DIST_FOLDER                 := dist

# +---------------------------------------------------------------------------+
# | BUILD ARTIFACTS
# +---------------------------------------------------------------------------+
TRANSLATEFILENAME           := $(LIB_NAME)_strings
PYTHON_SOURCE               := $(wildcard $(PYTHON_SOURCE_FOLDER)/*.py) \
                               $(wildcard $(PYTHON_SOURCE_FOLDER)/**/*.py) \
                               $(wildcard $(PYTHON_SOURCE_FOLDER)/**/**/*.py) \

JINJA_SOURCE                := $(wildcard $(PYTHON_SOURCE_FOLDER)/*.jinja) \
                               $(wildcard $(PYTHON_SOURCE_FOLDER)/**/*.jinja) \
                               $(wildcard $(PYTHON_SOURCE_FOLDER)/**/**/*.jinja) \

APP_SCRIPT                  := $(BUILDDIR)/scripts-$(PYTHON_VERSION)/$(APP_NAME)
MOFILES                     := $(addprefix $(TRANSLATIONS_DIR)/, $(addsuffix .mo, $(LOCALES)))
SETUP_SCRIPT                := setup.py
EGG_FILE                    := $(DIST_FOLDER)/$(LIB_NAME)-$(APP_VERSION)-py$(PYTHON_VERSION).egg

# +---------------------------------------------------------------------------+
# | BUILD TARGETS
# +---------------------------------------------------------------------------+

.PHONY : all
all: $(APP_SCRIPT)
	@# build all

.PHONY : clean
clean: $(SETUP_SCRIPT)
	env $(PYTHON) $< clean
	rm -rf $(BUILDDIR)
	rm -rf $(EGG_FOLDER)
	rm -rf $(DIST_FOLDER)
	rm -rf $(INTERMEDIATES_FOLDER)

.PHONY : install
install: $(SETUP_SCRIPT) $(EGG_FILE)
	@#nothing

.PHONY : translate
translate: $(MOFILES)
	# Translating all python source. .mo files go into source path and will need to be
	# checked in.

.PHONY : uninstall
uninstall:
	env $(PIP) uninstall $(LIB_NAME)

# +---------------------------------------------------------------------------+
# | BUILD RECIPES
# +---------------------------------------------------------------------------+

$(TRANSLATIONS_INTERMEDIATES)/$(TRANSLATEFILENAME).pot : $(PYTHON_SOURCE)
	@[ -d $(dir $@) ] || mkdir -p $(dir $@)
	$(XGETTEXT) --language=Python --keyword=_ --output=$@ $^

$(TRANSLATIONS_INTERMEDIATES)/%.po : $(TRANSLATIONS_INTERMEDIATES)/$(TRANSLATEFILENAME).pot
	@[ -d $(dir $@) ] || mkdir -p $(dir $@)
	$(MSGINIT) --input $< --no-translator --locale=$* --output-file=$@

$(TRANSLATIONS_DIR)/%.mo : $(TRANSLATIONS_INTERMEDIATES)/%.po
	@[ -d $(dir $@) ] || mkdir -p $(dir $@)
	$(MSGFMT) $^ --output-file=$@

$(APP_SCRIPT) : $(SETUP_SCRIPT) $(PYTHON_SOURCE) $(JINJA_SOURCE)
	env $(PYTHON) $< build
	@# python setuptools doesn't update the modified when copying the python source so we have to touch it
	@# to keep from rebuilding it every time.
	touch $@

$(EGG_FILE) : $(SETUP_SCRIPT) $(APP_SCRIPT)
	@#env $(PYTHON) $< bdist_egg
	env $(PYTHON) $< install
