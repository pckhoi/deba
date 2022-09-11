import argparse
import os

from deba.commands.decorators import subcommand
from deba.config import Config


def exec(conf: Config, args: argparse.Namespace):
    if conf.targets is None:
        return
    for target in conf.targets:
        print(os.path.join(conf.data_dir, target))


@subcommand(exec=exec)
def add_subcommand(
    subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        name="targets",
        parents=[parent_parser],
        help="print targets",
    )
    return parser
