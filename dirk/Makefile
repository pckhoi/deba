SHELL = /bin/bash

OS := $(shell uname -s)
MD5 := $(if $(findstring Darwin,$(OS)),md5,md5sum)
PYTHON := python
DIRK_DIR := .dirk
DIRK_FILE := dirk.yaml

DEPS_DIR := $(DIRK_DIR)/deps
DATA_DIR := $(DIRK_DIR)/data
MD5_DIR := $(DIRK_DIR)/md5
INPUT_DIR := $(DATA_DIR)/input
INPUT_LINKS_DIR := $(DIRK_DIR)/input_links
STAGES := $(shell $(PYTHON) -m dirk stages list)
DEP_FILES := $(patsubst %,$(DEPS_DIR)/%.d,$(STAGES))

.PHONY: dirk cleandirk

dirk: $(shell $(PYTHON) -m dirk targets list)

cleandirk:
	rm -rf $(DIRK_DIR)

define check_var
@[ "$($(1))" ] || ( echo "$(1) is not set"; exit 1 )
endef

# calculate md5
$(MD5_DIR)/%.md5: % | $(MD5_DIR)
	@-mkdir -p $(dir $@) 2>/dev/null
	$(if $(filter-out $(shell cat $@ 2>/dev/null),$(shell $(MD5) $<)),$(MD5) $< > $@)

$(DEPS_DIR)/%.d: %/*.py $(DIRK_FILE) | $(DEPS_DIR)
	$(PYTHON) -m dirk deps --stage $*

$(DIRK_DIR)/main.d: $(DIRK_FILE) | $(DIRK_DIR)
	$(PYTHON) -m dirk deps

$(INPUT_LINKS_DIR)/%.link: $(DIRK_FILE) | $(INPUT_LINKS_DIR)
	$(PYTHON) -m dirk update-input-links

$(INPUT_DIR)/%: $(INPUT_LINKS_DIR)/%.link | $(INPUT_DIR)
	-mkdir $(dir $@) 2>/dev/null
	$(PYTHON) -m dirk download $(shell cat $<) $@

$(DIRK_DIR): ; @-mkdir $@ 2>/dev/null
$(DEPS_DIR) $(DATA_DIR) $(MD5_DIR) $(INPUT_LINKS_DIR): | $(DIRK_DIR) ; @-mkdir $@ 2>/dev/null
$(INPUT_DIR): | $(DATA_DIR) ; @-mkdir $@ 2>/dev/null

include $(DIRK_DIR)/overrides.d
include $(DEP_FILES)