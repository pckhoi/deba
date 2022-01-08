SHELL = /bin/bash

OS := $(shell uname -s)
MD5 := $(if $(findstring Darwin,$(OS)),md5,md5sum)
PYTHON := python
DIRK_DIR := .dirk
DIRK_FILE := dirk.yaml

MD5_DIR := $(DIRK_DIR)/md5
STAGES_DIR := $(DIRK_DIR)/stages
STAGE_DIRS := $(patsubst %,$(STAGES_DIR)/%,$(shell $(PYTHON) -m dirk stages list))
STAGE_DEP_FILES := $(patsubst %,%/data.d,$(STAGE_DIRS))

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

$(STAGES_DIR)/%/data.d: %/*.py $(DIRK_FILE) | $(STAGES_DIR)/%
	$(PYTHON) -m dirk deps --stage $*

$(DIRK_DIR)/data.d: $(DIRK_FILE) | $(DIRK_DIR)
	$(PYTHON) -m dirk deps

$(DIRK_DIR): ; @-mkdir $@ 2>/dev/null
$(MD5_DIR) $(STAGES_DIR): | $(DIRK_DIR) ; @-mkdir $@ 2>/dev/null
$(STAGE_DIRS): | $(STAGES_DIR) ; @-mkdir $@ 2>/dev/null

include $(DIRK_DIR)/data.d
include $(DATA_DEP_FILES)