import argparse
import io
import json
import os
import typing

from deba.commands.decorators import subcommand
from deba.config import Config, Stage

from deba.deps.module import Loader
from deba.deps.find import find_dependencies


class InvalidDependencyError(Exception):
    pass


def validate_prerequisites(
    conf: Config, stage: Stage, ins: typing.List[str], rel_script_path: str
):
    ins_set = set()
    for filename in ins:
        if filename in ins_set:
            print(
                "WARNING: prerequisite %s of script %s found more than once"
                % (json.dumps(filename), rel_script_path)
            )
        ins_set.add(filename)
        if conf.enforce_stage_order and conf.is_data_from_latter_stages(
            stage.name, filename
        ):
            raise InvalidDependencyError(
                "prerequisite %s of script %s comes from a later stage"
                % (json.dumps(filename), rel_script_path)
            )


def validate_targets(
    conf: Config, stage: Stage, outs: typing.List[str], rel_script_path: str
):
    outs_set = set()
    for filename in outs:
        if filename in outs_set:
            print(
                "WARNING: target %s of script %s found more than once"
                % (json.dumps(filename), rel_script_path)
            )
        outs_set.add(filename)
        if not filename.startswith(stage.name + "/"):
            raise InvalidDependencyError(
                "target %s of script %s must start with %s"
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
    prerequisites, targets = find_dependencies(
        loader,
        script_path,
        conf.patterns.prerequisites or [],
        conf.patterns.targets or [],
    )

    if stage.ignored_targets is not None:
        targets = [s for s in targets if s not in stage.ignored_targets]

    rel_script_path = os.path.join(stage.name, script_name)
    validate_prerequisites(conf, stage, prerequisites, rel_script_path)
    validate_targets(conf, stage, targets, rel_script_path)

    if len(targets) == 0:
        print("    no target, skipping script %s" % script_name)
        return

    if len(prerequisites) == 0:
        print("    no prerequisite, skipping script %s" % script_name)
        return

    if conf.overrides is not None:
        for idx, exec_rule in enumerate(conf.overrides):
            if exec_rule.target_set == set(targets):
                print(
                    "    override #%d matches targets, skipping script %s"
                    % (idx, script_name)
                )
                return

    # write rule for this script
    targets = " ".join(["$(DEBA_DATA_DIR)/%s" % name for name in targets])
    deps_file.write(
        "%s &: %s %s | $(DEBA_DATA_DIR)/%s\n\t$(call deba_execute,%s)\n\n"
        % (
            targets,
            "$(DEBA_MD5_DIR)/%s.md5" % (rel_script_path),
            " ".join(
                ["$(DEBA_DATA_DIR)/%s" % name for name in prerequisites]
                + (
                    [
                        "$(DEBA_MD5_DIR)/%s.md5" % str(p)
                        for p in stage.common_prerequisites
                    ]
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
                "$(DEBA_DATA_DIR)/%s: ; @-mkdir -p $@ 2>/dev/null\n\n" % (stage.name)
            )

            for script_name, script_path in stage.scripts():
                write_deps(conf, stage, loader, f, script_name, script_path)
    else:
        os.makedirs(conf.deba_dir, exist_ok=True)
        with open(conf.main_deps_filepath, "w") as f:
            if conf.overrides is not None:
                for rule in conf.overrides:
                    f.write(
                        "%s &: %s\n\t%s\n\n"
                        % (
                            rule.target_str,
                            " ".join(
                                "$(DEBA_DATA_DIR)/%s" % d for d in rule.prerequisites
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
