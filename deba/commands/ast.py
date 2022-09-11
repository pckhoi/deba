import argparse
import ast
import logging

from deba.commands.decorators import subcommand
from deba.config import Config

import astpretty


logger = logging.getLogger("deba")


def exec(conf: Config, args: argparse.Namespace):
    with open(args.script, "r") as f:
        node = ast.parse(f.read())
    astpretty.pprint(node)


@subcommand(exec=exec)
def add_subcommand(
    subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        name="ast",
        parents=[parent_parser],
        description="pretty print SCRIPT ast",
    )
    parser.add_argument(
        "script",
        metavar="SCRIPT",
        type=str,
        help="the script to print",
    )
    return parser
