import argparse

from poniard.commands.decorators import subcommand
from poniard.config import Config


def exec(conf: Config, args: argparse.Namespace):
    print(conf.data_dir)


@subcommand(exec=exec)
def add_subcommand(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name="dataDir")
    return parser
