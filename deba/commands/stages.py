import argparse

from deba.commands.decorators import subcommand
from deba.config import Config


def exec(conf: Config, args: argparse.Namespace):
    for stage in conf.stages:
        print(stage.name)


@subcommand(exec=exec)
def add_subcommand(
    subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name="stages", parents=[parent_parser], add_help=False)
    return parser
