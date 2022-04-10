import argparse

from deba.commands.decorators import subcommand
from deba.config import Config


def exec(conf: Config, args: argparse.Namespace):
    print(conf.md5_dir)


@subcommand(exec=exec)
def add_subcommand(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name="md5Dir")
    return parser
