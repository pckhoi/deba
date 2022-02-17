import argparse
import pathlib
import shutil

from dirk.commands.decorators import subcommand
from dirk.config import Config, Stage
from dirk.deps.expr import ExprPatterns
from dirk.serialize import yaml_dump


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
    dirk_file = cwd / "dirk.yaml"
    if not dirk_file.is_file():
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
        input_patterns = []
        if args.input_patterns is None:
            while True:
                cont = input("add an input pattern? (Y/n)")
                if cont != "" and cont.strip().lower() != "y":
                    break
                input_patterns.append(input("  input pattern: ").strip())
            if len(input_patterns) == 0:
                raise ValueError("must add at least 1 input pattern")
        else:
            input_patterns = args.input_patterns
        output_patterns = []
        if args.output_patterns is None:
            while True:
                cont = input("add an output pattern? (Y/n)")
                if cont != "" and cont.strip().lower() != "y":
                    break
                output_patterns.append(input("  output pattern: ").strip())
            if len(output_patterns) == 0:
                raise ValueError("must add at least 1 output pattern")
        else:
            output_patterns = args.output_patterns

        # write dirk config
        conf = Config(
            stages=stages,
            targets=targets,
            patterns=ExprPatterns(inputs=input_patterns, outputs=output_patterns),
        )
        with open(dirk_file, "w") as f:
            f.write(yaml_dump(conf))
        print("wrote dirk config to %s" % dirk_file.name)
    else:
        print("dirk config found, skipping config initialization")

    # write make config
    mk_file = cwd / "dirk.mk"
    shutil.copyfile(pathlib.Path(__file__).parent / "Makefile", mk_file)
    print("wrote Make config to %s" % mk_file.name)
    ensure_line(cwd / "Makefile", "include dirk.mk")

    # write .gitignore
    ensure_line(cwd / ".gitignore", ".dirk")


@subcommand(exec=exec, open_config=False)
def add_subcommand(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        name="init", description="initialize dirk config in the current folder"
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
        help="target files. Each time your run `make dirk`, these files will be updated if any of their dependencies have been updated since.",
    )
    parser.add_argument(
        "--input-patterns",
        type=str,
        nargs="*",
        help="input patterns that Dirk uses to find input files for each script",
    )
    parser.add_argument(
        "--output-patterns",
        type=str,
        nargs="*",
        help="output patterns that Dirk uses to find output files for each script",
    )
    return parser
