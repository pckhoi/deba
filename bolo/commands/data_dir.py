import argparse

from bolo.commands.decorators import subcommand
from bolo.config import Config


def exec(conf: Config, args: argparse.Namespace):
    print(conf.data_dir)


@subcommand(exec=exec)
def add_subcommand(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name="dataDir")
    return parser
