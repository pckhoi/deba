import argparse

from .init import add_subcommand as add_init_command
from .data_dir import add_subcommand as add_data_dir_command
from .deps import add_subcommand as add_deps_command
from .stages import add_subcommand as add_stages_command
from .targets import add_subcommand as add_targets_command
from .python_path import add_subcommand as add_python_path_command
from .test import add_subcommand as add_test_command


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        "deba", description="discover proper order of execution"
    )
    subparsers = parser.add_subparsers()
    add_init_command(subparsers)
    add_data_dir_command(subparsers)
    add_deps_command(subparsers)
    add_stages_command(subparsers)
    add_targets_command(subparsers)
    add_python_path_command(subparsers)
    add_test_command(subparsers)
    return parser


def exec():
    parser = get_parser()

    args = parser.parse_args()
    args.exec(None, args)


__all__ = ["get_parser"]
