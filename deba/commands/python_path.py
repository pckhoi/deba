import argparse
import os

from deba.commands.decorators import subcommand
from deba.config import Config


def exec(conf: Config, args: argparse.Namespace):
    print(os.pathsep.join(conf.script_search_paths))


@subcommand(exec=exec)
def add_subcommand(
    subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        name="pythonPath",
        parents=[parent_parser],
        help="print pythonPath",
    )
    return parser
