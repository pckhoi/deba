import argparse
import pathlib
import shutil

from bolo.commands.decorators import subcommand
from bolo.config import Config, Stage
from bolo.deps.expr import ExprPatterns
from bolo.serialize import yaml_dump


def is_line_found(file: pathlib.Path, expected_line: str) -> bool:
    if file.is_file():
        with open(file, "r") as f:
            for line in f:
                if line.strip() == expected_line:
                    return True
    return False


def ensure_line(file: pathlib.Path, line: str):
    if not is_line_found(file, line):
        with open(file, "a+") as f:
            f.write("\n%s\n" % line)
        print('added "%s" to %s' % (line, file.name))


def exec(conf: Config, args: argparse.Namespace):
    cwd = pathlib.Path.cwd()
    bolo_file = cwd / "bolo.yaml"
    if not bolo_file.is_file():
        # prompt for stages
        stages = []
        if args.stages is None:
            while True:
                cont = input("add a stage? (Y/n)")
                if cont != "" and cont.strip().lower() != "y":
                    break
                stages.append(Stage(name=input("  stage name:")))
            if len(stages) == 0:
                raise ValueError("must add at least 1 stage")
        else:
            stages = [Stage(name=name.strip()) for name in args.stages]

        # prompt for targets
        targets = []
        if args.targets is None:
            while True:
                cont = input("add a target? (Y/n)")
                if cont != "" and cont.strip().lower() != "y":
                    break
                targets.append(input("  target: ").strip())
            if len(targets) == 0:
                raise ValueError("must add at least 1 target")
        else:
            targets = args.targets

        # prompt for patterns
        prerequisite_patterns = []
        if args.prerequisite_patterns is None:
            while True:
                cont = input("add an prerequisite pattern? (Y/n)")
                if cont != "" and cont.strip().lower() != "y":
                    break
                prerequisite_patterns.append(input("  prerequisite pattern: ").strip())
            if len(prerequisite_patterns) == 0:
                raise ValueError("must add at least 1 prerequisite pattern")
        else:
            prerequisite_patterns = args.prerequisite_patterns
        target_patterns = []
        if args.target_patterns is None:
            while True:
                cont = input("add an target pattern? (Y/n)")
                if cont != "" and cont.strip().lower() != "y":
                    break
                target_patterns.append(input("  target pattern: ").strip())
            if len(target_patterns) == 0:
                raise ValueError("must add at least 1 target pattern")
        else:
            target_patterns = args.target_patterns

        # write bolo config
        conf = Config(
            stages=stages,
            targets=targets,
            patterns=ExprPatterns(
                prerequisites=prerequisite_patterns, targets=target_patterns
            ),
        )
        with open(bolo_file, "w") as f:
            f.write(yaml_dump(conf))
        print("wrote bolo config to %s" % bolo_file.name)
    else:
        print("bolo config found, skipping config initialization")

    # write make config
    mk_file = cwd / "bolo.mk"
    shutil.copyfile(pathlib.Path(__file__).parent / "Makefile", mk_file)
    print("wrote Make config to %s" % mk_file.name)
    ensure_line(cwd / "Makefile", "include bolo.mk")

    # write .gitignore
    ensure_line(cwd / ".gitignore", ".bolo")


@subcommand(exec=exec, open_config=False)
def add_subcommand(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        name="init", description="initialize bolo config in the current folder"
    )
    parser.add_argument(
        "--stages",
        type=str,
        nargs="*",
        help="names of execution stages. Each stage is a plain folder that houses scripts that have similar execution order. Execution order among stages follows their order in the config file.",
    )
    parser.add_argument(
        "--targets",
        type=str,
        nargs="*",
        help="target files. Each time your run `make bolo`, these files will be updated if any of their dependencies have been updated since.",
    )
    parser.add_argument(
        "--prerequisite-patterns",
        type=str,
        nargs="*",
        help="prerequisite patterns that Dirk uses to find prerequisites for each script",
    )
    parser.add_argument(
        "--target-patterns",
        type=str,
        nargs="*",
        help="target patterns that Dirk uses to find targets for each script",
    )
    return parser
