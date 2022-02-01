import argparse
import io
import json
import os
import typing

from charset_normalizer import logging

from dirk.commands.decorators import subcommand
from dirk.config import Config, Stage
from dirk.deps.finder import DepsFinder


class InvalidDependencyError(Exception):
    pass


def validate_inputs(
    conf: Config, stage: Stage, ins: typing.List[str], rel_script_path: str
):
    for filename in ins:
        if conf.is_data_from_latter_stages(stage.name, filename):
            raise InvalidDependencyError(
                "input %s of script %s comes from a latter stage"
                % (json.dumps(filename), rel_script_path)
            )


def validate_outputs(
    conf: Config, stage: Stage, outs: typing.List[str], rel_script_path: str
):
    for filename in outs:
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
    finder: DepsFinder,
    deps_file: io.TextIOWrapper,
    dir_var: str,
    script_name: str,
    script_path: str,
):
    ins, outs = finder.find_dependencies(
        script_path,
        conf.expressions.inputs or [],
        conf.expressions.outputs or [],
    )

    rel_script_path = os.path.join(stage.name, script_name)
    validate_inputs(conf, stage, ins, rel_script_path)
    validate_outputs(conf, stage, outs, rel_script_path)

    for idx, exec_rule in enumerate(conf._overrides):
        if set(exec_rule.target) == set(outs):
            logging.info(
                "override #%d matches outputs, skipping script %s" % (idx, script_name)
            )
            return

    # write rule for this script
    targets = " ".join(["$(DATA_DIR)/%s" % name for name in outs])
    deps_file.write(
        "%s: %s %s | $(%s)\n\t$(PYTHON) %s\n\n"
        % (
            targets,
            "$(MD5_DIR)/%s.md5" % (rel_script_path),
            " ".join(
                ["data/%s" % name for name in ins]
                + [str(p) for p in stage._common_deps]
            ),
            dir_var,
            rel_script_path,
        )
    )


def exec(conf: Config, args: argparse.Namespace):
    if args.stage != "":
        finder = DepsFinder(conf.script_search_paths())
        stage = conf.get_stage(args.stage)
        if stage is None:
            raise ValueError(
                "stage %s not found, available stages are: %s",
                json.dumps(args.stage),
                json.dumps([st.name for st in conf.stages]),
            )
        dir_var = "%s_DATA_DIR" % stage.name.upper()
        os.makedirs(conf.deps_dir, exist_ok=True)
        with open(stage.deps_filepath, "w") as f:
            # write rule for data dir
            f.write("%s := $(DATA_DIR)/%s\n\n" % (dir_var, stage.name))
            f.write("$(%s): | $(DATA_DIR) ; @-mkdir $@ 2>/dev/null\n\n" % (dir_var))

            for script_name, script_path in stage.scripts():
                write_deps(conf, stage, finder, f, dir_var, script_name, script_path)


@subcommand(exec=exec)
def add_subcommand(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name="deps")
    parser.add_argument("--stage", type=str, default="")
    return parser
