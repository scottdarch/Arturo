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
APP_NAME 					:= ano
LOCALES  					+= en_US \

# +---------------------------------------------------------------------------+
# | BUILD TOOLS (you can override these by setting a value in local.mk)
# +---------------------------------------------------------------------------+
XGETTEXT					?= xgettext
MSGFMT						?= msgfmt
MSGINIT						?= msginit
PYTHON  					?= python2

# +---------------------------------------------------------------------------+
# | BUILD LOCATIONS
# +---------------------------------------------------------------------------+
BUILDDIR                    := build
PYTHON_SOURCE_FOLDER		:= $(APP_NAME)
INTERMEDIATES_FOLDER        := .intermediates
TRANSLATIONS_INTERMEDIATES  := $(INTERMEDIATES_FOLDER)/pots
TRANSLATIONS_DIR 			:= $(PYTHON_SOURCE_FOLDER)/i18n
EGG_FOLDER 		 			:= $(APP_NAME).egg-info
DIST_FOLDER					:= dist
PYTHON_INTERMEDIATES		:= $(BUILDDIR)/lib

# +---------------------------------------------------------------------------+
# | BUILD ARTIFACTS
# +---------------------------------------------------------------------------+
TRANSLATEFILENAME			:= ano_strings
PYTHON_SOURCE 				:= $(wildcard $(PYTHON_SOURCE_FOLDER)/*.py) \
                			   $(wildcard $(PYTHON_SOURCE_FOLDER)/**/*.py) \
                			   $(wildcard $(PYTHON_SOURCE_FOLDER)/**/**/*.py) \

PYTHON_SOURCE_BELLWETHER    := $(PYTHON_INTERMEDIATES)/$(APP_NAME)/__init__.py
MOFILES 					:= $(addprefix $(TRANSLATIONS_DIR)/, $(addsuffix .mo, $(LOCALES)))
EGG_SETUP					:= setup.py

# +---------------------------------------------------------------------------+
# | BUILD TARGETS
# +---------------------------------------------------------------------------+

.PHONY : all
all: $(PYTHON_SOURCE_BELLWETHER)
	@# build all

.PHONY : clean
clean:
	rm -rf $(BUILDDIR)
	rm -rf $(EGG_FOLDER)
	rm -rf $(DIST_FOLDER)
	rm -rf $(INTERMEDIATES_FOLDER)

.PHONY : install
install: $(EGG_SETUP) $(PYTHON_SOURCE_BELLWETHER)
	env $(PYTHON) $< install

.PHONY : translate
translate: $(MOFILES)
	# Translating all python source. .mo files go into source path and will need to be
	# checked in.

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

$(PYTHON_SOURCE_BELLWETHER) : $(EGG_SETUP) $(PYTHON_SOURCE)
	env $(PYTHON) $< build
	@# python setuptools doesn't update the modified when copying the python source so we have to touch it
	@# to keep from rebuilding it every time.
	touch $@
