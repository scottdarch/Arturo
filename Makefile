#  _____     _               
# |  _  |___| |_ _ _ ___ ___ 
# |     |  _|  _| | |  _| . |
# |__|__|_| |_| |___|_| |___|
# http://32bits.io/Arturo/
#

-include local.mk

XGETTEXT?=xgettext
MSGFMT?=msgfmt
MSGINIT?=msginit

BUILDDIR=build
PYTHON_SOURCE_FOLDER=ano
TRANSLATIONS_INTERMEDIATES=$(BUILDDIR)
TRANSLATIONS_DIR=$(PYTHON_SOURCE_FOLDER)/i18n
TRANSLATEFILENAME=ano_strings
PYTHON_SOURCE = $(wildcard $(PYTHON_SOURCE_FOLDER)/*.py) \
                $(wildcard $(PYTHON_SOURCE_FOLDER)/**/*.py) \

LOCALES = en_US \


MOFILES = $(addprefix $(TRANSLATIONS_DIR)/, $(addsuffix .mo, $(LOCALES)))

.PHONY : all
all: $(MOFILES)
	@# just build the translations

.PHONY : clean
clean:
	rm -rf $(BUILDDIR)

$(TRANSLATIONS_INTERMEDIATES)/$(TRANSLATEFILENAME).pot : $(PYTHON_SOURCE)
	@[ -d $(dir $@) ] || mkdir -p $(dir $@)
	$(XGETTEXT) --language=Python --keyword=_ --output=$@ $^

$(TRANSLATIONS_INTERMEDIATES)/%.po : $(TRANSLATIONS_INTERMEDIATES)/$(TRANSLATEFILENAME).pot
	@[ -d $(dir $@) ] || mkdir -p $(dir $@)
	$(MSGINIT) --input $< --no-translator --locale=$* --output-file=$@

$(TRANSLATIONS_DIR)/%.mo : $(TRANSLATIONS_INTERMEDIATES)/%.po
	@[ -d $(dir $@) ] || mkdir -p $(dir $@)
	$(MSGFMT) $^ --output-file=$@

install: $(MOFILES)
	env python2 setup.py install
