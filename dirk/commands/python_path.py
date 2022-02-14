import argparse
import os

from dirk.commands.decorators import subcommand
from dirk.config import Config


def exec(conf: Config, args: argparse.Namespace):
    print(";".join(conf.script_search_paths))


@subcommand(exec=exec)
def add_subcommand(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name="pythonPath", help="print pythonPath")
    return parser
