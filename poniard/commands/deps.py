import argparse
import io
import json
import os
import typing

from charset_normalizer import logging

from poniard.commands.decorators import subcommand
from poniard.config import Config, Stage

# from poniard.deps.finder import DepsFinder
from poniard.deps.module import Loader
from poniard.deps.find import find_dependencies


class InvalidDependencyError(Exception):
    pass


def validate_inputs(
    conf: Config, stage: Stage, ins: typing.List[str], rel_script_path: str
):
    ins_set = set()
    for filename in ins:
        if filename in ins_set:
            print(
                "WARNING: input %s of script %s found more than once"
                % (json.dumps(filename), rel_script_path)
            )
        ins_set.add(filename)
        if conf.is_data_from_latter_stages(stage.name, filename):
            raise InvalidDependencyError(
                "input %s of script %s comes from a later stage"
                % (json.dumps(filename), rel_script_path)
            )


def validate_outputs(
    conf: Config, stage: Stage, outs: typing.List[str], rel_script_path: str
):
    outs_set = set()
    for filename in outs:
        if filename in outs_set:
            print(
                "WARNING: output %s of script %s found more than once"
                % (json.dumps(filename), rel_script_path)
            )
        outs_set.add(filename)
        if not filename.startswith(stage.name + "/"):
            raise InvalidDependencyError(
                "output %s of script %s must start with %s"
                % (
                    json.dumps(filename),
                    rel_script_path,
                    json.dumps(stage.name + "/"),
                )
            )


def write_deps(
    conf: Config,
    stage: Stage,
    loader: Loader,
    deps_file: io.TextIOWrapper,
    script_name: str,
    script_path: str,
):
    ins, outs = find_dependencies(
        loader,
        script_path,
        conf.patterns.inputs or [],
        conf.patterns.outputs or [],
    )

    if stage.ignored_outputs is not None:
        outs = [s for s in outs if s not in stage.ignored_outputs]

    rel_script_path = os.path.join(stage.name, script_name)
    validate_inputs(conf, stage, ins, rel_script_path)
    validate_outputs(conf, stage, outs, rel_script_path)

    if conf.overrides is not None:
        for idx, exec_rule in enumerate(conf.overrides):
            if exec_rule.target_set == set(outs):
                logging.info(
                    "override #%d matches outputs, skipping script %s"
                    % (idx, script_name)
                )
                return

    # write rule for this script
    targets = " ".join(["$(PONIARD_DATA_DIR)/%s" % name for name in outs])
    deps_file.write(
        "%s &: %s %s | $(PONIARD_DATA_DIR)/%s\n\t$(call poniard_execute,%s)\n\n"
        % (
            targets,
            "$(PONIARD_MD5_DIR)/%s.md5" % (rel_script_path),
            " ".join(
                ["$(PONIARD_DATA_DIR)/%s" % name for name in ins]
                + (
                    [str(p) for p in stage.common_prerequisites]
                    if stage.common_prerequisites is not None
                    else []
                )
            ),
            stage.name,
            rel_script_path,
        )
    )


def exec(conf: Config, args: argparse.Namespace):
    if args.stage != "":
        loader = Loader(conf.script_search_paths)
        stage = conf.get_stage(args.stage)
        if stage is None:
            raise ValueError(
                "stage %s not found, available stages are: %s",
                json.dumps(args.stage),
                json.dumps([st.name for st in conf.stages]),
            )
        os.makedirs(conf.deps_dir, exist_ok=True)
        with open(stage.deps_filepath, "w") as f:
            # write rule for data dir
            f.write(
                "$(PONIARD_DATA_DIR)/%s: ; @-mkdir -p $@ 2>/dev/null\n\n" % (stage.name)
            )

            for script_name, script_path in stage.scripts():
                write_deps(conf, stage, loader, f, script_name, script_path)
    else:
        if conf.overrides is not None:
            os.makedirs(conf.poniard_dir, exist_ok=True)
            with open(conf.main_deps_filepath, "w") as f:
                for rule in conf.overrides:
                    f.write(
                        "%s &: %s\n\t%s\n\n"
                        % (
                            rule.target_str,
                            " ".join(
                                "$(PONIARD_DATA_DIR)/%s" % d for d in rule.prerequisites
                            ),
                            rule.recipe,
                        )
                    )


@subcommand(exec=exec)
def add_subcommand(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name="deps", description="write make rules")
    parser.add_argument(
        "--stage",
        type=str,
        default="",
        help="if specified, analyze and write make rules for scripts in this stage. Otherwise, write overriden make rules.",
    )
    return parser
