# Bolo

Smart pipeline framework that knows how to analyze your Python scripts (without running) and generate Make rules for you. If you specify script prerequisites and targets within the script itself, Bolo can pick them up automatically based on pre-defined patterns and write Make rules accordingly. In addition, Bolo mandates a few good rules for sane project management.

## Table of Contents

## Getting Started

## Terms & Concepts

- **Stage**:
- **Prerequisite**:
- **Target**:
- **Pattern**:

## Pattern Format

## Configuration

Bolo configuration is read from a file called `bolo.yaml`. This file should be in the same folder
as `Makefile`. Here's an example:

```yaml
# A stage is a folder that houses scripts of similar execution order. Stage execution order is the
# same as specified order. Bolo enforce that order by forcing scripts to prefix their targets with
# the stage name and preventing scripts from reading targets of later stages.
stages:
  # stage name is also the folder name
  - name: clean
    # if for some reasons, you want bolo to ignore certain scripts in this stage, this is how
    ignoredScripts:
      - baton_rouge_pd_cprr.py
  - name: match
    # if bolo somehow cannot pick up some prerequisites, you can include them manually for all
    # underlying scripts like this. However, the preferred method is always to add a pattern in
    # patterns.prerequisites.
    commonPrerequisites:
      - reference/us_census_first_names.csv
  - name: fuse
    # targets in this list will not be validated (doesn't have to be prefixed with "{stage.name}/")
    # and will not be included in the Make rules.
    ignoredTargets:
      - duplicates.csv

# targets are the final targets of your entire pipeline. They will be updated when you run `make bolo`.
targets:
  - fuse/person.csv
  - fuse/event.csv
  - fuse/allegation.csv

patterns:
  # prerequisite patterns are patterns that bolo look for in scripts to determine their prerequisites
  prerequisites:
    - pd.read_csv(bolo.data(r'.+\.csv'))
  # target patterns are patterns that bolo look for in scripts to determine their targets
  targets:
    - "`*`.to_csv(bolo.data(r'.+\\.csv'))"
# # overrides are Make rules that you want to include manually. Each entry is equivalent to a Make rule
# # of this form:
# #     [target]: [prerequisites]
# #         [recipe]
# # Any rule introduced here will override rules that Bolo picked up from analyzing scripts. The primary
# # purpose of this section is to override any Make rule produced by Bolo that you don't like. Any Make
# # recipe that doesn't invoke Python or not invoking scripts from stage folders shouldn't really be
# # included here. Please include them in the Makefile instead.
# overrides:
#   - target:
#       - fuse/per_new_orleans_pd.csv
#     prerequisites:
#       - match/new_orleans_personnel.csv
#     recipe: $(PYTHON) fuse/new_orleans_pd.py

# # By default, the parent folder of bolo.yaml is automatically included in PYTHONPATH during script
# # execution. If you want to include more paths in PYTHONPATH then please include them here
# pythonPath:
#   - src/lib

# # dataDir is the directory that houses all data produced by scripts invoked with Bolo. It is "data"
# # by default. In scripts, you call bolo.data to prefix file paths with this directory.
# dataDir: data
```

## Folder structure

## Module Loading
