SHELL = /bin/bash

OS := $(shell uname -s)
PYTHON := python
PONIARD_DIR := .poniard
PONIARD_FILE := poniard.yaml

PONIARD_DEPS_DIR := $(PONIARD_DIR)/deps
PONIARD_DATA_DIR := $(shell $(PYTHON) -m poniard dataDir)
PONIARD_MD5_DIR := $(PONIARD_DIR)/md5
PONIARD_STAGES := $(shell $(PYTHON) -m poniard stages)
PONIARD_DEP_FILES := $(patsubst %,$(PONIARD_DEPS_DIR)/%.d,$(PONIARD_STAGES))
PONIARD_PYTHON_PATH := $(shell $(PYTHON) -m poniard pythonPath)

.PHONY: poniard cleanponiard

poniard: $(shell $(PYTHON) -m poniard targets)

cleanponiard:
	rm -rf $(PONIARD_DIR)

define poniard_execute
@start_time=$$SECONDS && \
echo "running $(1)" | sed $$'s,.*,\e[1;37m&\e[m,' && \
(set -o pipefail; PYTHONPATH=$(PONIARD_PYTHON_PATH) $(PYTHON) $(1) 2>&1>&3 | sed $$'s,.*,    \e[31m&\e[m,' >&2 )3>&1 | sed $$'s,.*,    \e[1;30m&\e[m,' && \
echo "    script completed in $$((SECONDS - start_time)) seconds" | sed $$'s,.*,\e[1;34m&\e[m,'
endef

# calculate md5
$(PONIARD_MD5_DIR)/%.md5: % | $(PONIARD_MD5_DIR)
	@-mkdir -p $(dir $@) 2>/dev/null
	@$(PYTHON) -m poniard md5 $< $@

$(PONIARD_DEPS_DIR)/%.d: %/*.py $(PONIARD_FILE) | $(PONIARD_DEPS_DIR)
	$(PYTHON) -m poniard deps --stage $*

$(PONIARD_DIR)/main.d: $(PONIARD_FILE) | $(PONIARD_DIR)
	$(PYTHON) -m poniard deps

$(PONIARD_DIR): ; @-mkdir $@ 2>/dev/null
$(PONIARD_DATA_DIR): ; @-mkdir -p $@ 2>/dev/null
$(PONIARD_DEPS_DIR) $(PONIARD_MD5_DIR): | $(PONIARD_DIR) ; @-mkdir $@ 2>/dev/null

include $(PONIARD_DIR)/main.d
include $(PONIARD_DEP_FILES)