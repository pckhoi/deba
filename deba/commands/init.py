import argparse
import pathlib
import shutil

from deba.commands.decorators import subcommand
from deba.config import Config, Stage
from deba.deps.expr import ExprPatterns
from deba.serialize import yaml_dump


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
    deba_file = cwd / "deba.yaml"
    if not deba_file.is_file():
        # prompt for stages
        stages = []
        if args.stages is None:
            print(
                "A stage is a group of scripts that serve the same purpose. "
                "Examples of stage are: 'OCR', 'NER', 'cleaning', 'record_linkage', etc."
            )
            while True:
                cont = input("Add a stage? (Y/n) ")
                if cont != "" and cont.strip().lower() != "y":
                    break
                stages.append(Stage(name=input("  stage name: ")))
            print()
        else:
            stages = [Stage(name=name.strip()) for name in args.stages]

        # prompt for targets
        targets = []
        if args.targets is None:
            print("A target is an output of the entire pipeline.")
            while True:
                cont = input("Add a target? (Y/n) ")
                if cont != "" and cont.strip().lower() != "y":
                    break
                targets.append(input("  target: ").strip())
            print()
        else:
            targets = args.targets

        # prompt for patterns
        prerequisite_patterns = []
        if args.prerequisite_patterns is None:
            print(
                "A prerequisite pattern tells Deba how to extract prerequisites from a script. "
                "Visit https://github.com/pckhoi/deba#pattern to learn more."
            )
            while True:
                cont = input("Add a prerequisite pattern? (Y/n) ")
                if cont != "" and cont.strip().lower() != "y":
                    break
                prerequisite_patterns.append(input("  prerequisite pattern: ").strip())
            print()
        else:
            prerequisite_patterns = args.prerequisite_patterns
        target_patterns = []
        if args.target_patterns is None:
            print(
                "A target pattern tells Deba how to extract targets from a script. "
                "Visit https://github.com/pckhoi/deba#pattern to learn more."
            )
            while True:
                cont = input("Add a target pattern? (Y/n) ")
                if cont != "" and cont.strip().lower() != "y":
                    break
                target_patterns.append(input("  target pattern: ").strip())
            print()
        else:
            target_patterns = args.target_patterns

        # write deba config
        conf = Config(
            stages=stages,
            targets=targets,
            patterns=ExprPatterns(
                prerequisites=prerequisite_patterns, targets=target_patterns
            ),
        )
        with open(deba_file, "w") as f:
            f.write(yaml_dump(conf))
        print("Wrote deba config to %s" % deba_file.name)
    else:
        print("Deba config found, skipping config initialization")

    # write make config
    mk_file = cwd / "deba.mk"
    shutil.copyfile(pathlib.Path(__file__).parent / "Makefile", mk_file)
    print("wrote Make config to %s" % mk_file.name)
    ensure_line(cwd / "Makefile", "include deba.mk")

    # write .gitignore
    ensure_line(cwd / ".gitignore", ".deba")


@subcommand(exec=exec, open_config=False)
def add_subcommand(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        name="init", description="initialize deba config in the current folder"
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
        help="target files. Each time your run `make deba`, these files will be updated if any of their dependencies have been updated since.",
    )
    parser.add_argument(
        "--prerequisite-patterns",
        type=str,
        nargs="*",
        help="prerequisite patterns that Deba uses to find prerequisites for each script",
    )
    parser.add_argument(
        "--target-patterns",
        type=str,
        nargs="*",
        help="target patterns that Deba uses to find targets for each script",
    )
    return parser
