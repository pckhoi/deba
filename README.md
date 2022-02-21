# Deba

Smart pipeline framework that knows how to analyze your Python scripts (without running) and generate Make rules for you. If you specify script prerequisites and targets within the script itself, Deba can pick them up automatically based on pre-defined patterns and write Make rules accordingly. In addition, Deba mandates a few good rules for sane project management.

- [Deba](#deba)
  - [Getting Started](#getting-started)
  - [Terms & Concepts](#terms--concepts)
    - [Prerequisite](#prerequisite)
    - [Target](#target)
    - [Stage](#stage)
    - [Pattern](#pattern)
  - [Configuration](#configuration)
  - [Folder structure](#folder-structure)
  - [Module Loading](#module-loading)

## Getting Started

## Terms & Concepts

Deba is a tool that complements GNU Make therefore borrows many terms directly from Make, and introduces some of its own.

### Prerequisite

Prerequisite in Make refers to assets/source files that when updated retrigger a build. In the context of Deba, we're not building binaries but rather transform data of one kind to another. Prerequisite in this context means input data.

### Target

Target in Make refers build artifacts and/or resulting binaries. In the context of Deba, target refers to output data.

### Stage

A stage is a group of scripts with the same execution order. When using Deba, you must declare stage names in [deba.yaml](#configuration) and put your scripts under folders named after the stages. Stage execution order is the same order as specified in deba.yaml. Deba enforces that order by forcing scripts to prefix their targets with the stage name and preventing scripts from reading targets of later stages.

### Pattern

Deba relies on patterns declared by the user to scan the scripts for prerequisites and targets. A pattern must have the form `<function call>(<prerequisite or target string>)`. Here's how each part is read:

- `function call`:
  - can be plain function call e.g. `pd.read_csv`
  - can be nested e.g. `pd.read_csv(deba.data(<prerequisite or target string>))`
  - can match names in scope by using glob pattern between backticks e.g. `` `df_*`.to_csv ``, which can match `df_09.to_csv` or `df_cleaned.to_csv`. Refers to [fnmatch](https://docs.python.org/3/library/fnmatch.html) to learn what glob patterns can be used between backticks.
- `prerequisite or target string`:
  - must be a regular expression that matches intended prerequisites or targets. For example if I want to detect all prerequisites that ends with `.csv`, I can use `pd.read_csv(r'.+\.csv')`.

## Configuration

Deba configuration is read from a file called `deba.yaml`. This file should be in the same folder
as `Makefile`. Here's an example:

```yaml
# A stage is a folder that houses scripts of similar execution order.
stages:
  # stage name is also the folder name
  - name: clean
    # if for some reasons, you want deba to ignore certain scripts in this stage, this is how
    ignoredScripts:
      - baton_rouge_pd_cprr.py
  - name: match
    # if deba somehow cannot pick up some prerequisites, you can include them manually for all
    # underlying scripts like this. However, the preferred method is always to add a pattern in
    # patterns.prerequisites.
    commonPrerequisites:
      - reference/us_census_first_names.csv
  - name: fuse
    # targets in this list will not be validated (doesn't have to be prefixed with "{stage.name}/")
    # and will not be included in the Make rules.
    ignoredTargets:
      - duplicates.csv

# targets are the final targets of your entire pipeline. They will be updated when you run `make deba`.
targets:
  - fuse/person.csv
  - fuse/event.csv
  - fuse/allegation.csv

patterns:
  # prerequisite patterns are patterns that deba look for in scripts to determine their prerequisites
  prerequisites:
    - pd.read_csv(deba.data(r'.+\.csv'))
  # target patterns are patterns that deba look for in scripts to determine their targets
  targets:
    - "`*`.to_csv(deba.data(r'.+\\.csv'))"

# # overrides are Make rules that you want to include manually. Each entry is equivalent to a Make rule
# # of this form:
# #     [target]: [prerequisites]
# #         [recipe]
# # Any rule introduced here will override rules that Deba picked up from analyzing scripts. The primary
# # purpose of this section is to override any Make rule produced by Deba that you don't like. Any Make
# # recipe that doesn't invoke Python or not invoking scripts from stage folders shouldn't really be
# # included here. Please include them in the Makefile instead.
# overrides:
#   - target:
#       - fuse/per_new_orleans_pd.csv
#     prerequisites:
#       - match/new_orleans_personnel.csv
#     recipe: $(PYTHON) fuse/new_orleans_pd.py

# # By default, the parent folder of deba.yaml is automatically included in PYTHONPATH during script
# # execution. If you want to include more paths in PYTHONPATH then please include them here
# pythonPath:
#   - src/lib

# # dataDir is the directory that houses all data produced by scripts invoked with Deba. It is "data"
# # by default. In scripts, you call deba.data to prefix file paths with this directory.
# dataDir: data
```

## Folder structure

## Module Loading
