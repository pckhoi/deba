import argparse

from dirk.commands.decorators import subcommand
from dirk.config import Config


def exec(conf: Config, args: argparse.Namespace):
    pass


@subcommand(exec=exec)
def add_my_subcommand(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name="deps")
    # parser.add_argument("--my-sub-flag", type=str, default="def")
    return parser
