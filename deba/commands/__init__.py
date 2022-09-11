import argparse
import logging

from .init import add_subcommand as add_init_command
from .data_dir import add_subcommand as add_data_dir_command
from .deps import add_subcommand as add_deps_command
from .stages import add_subcommand as add_stages_command
from .targets import add_subcommand as add_targets_command
from .python_path import add_subcommand as add_python_path_command
from .test import add_subcommand as add_test_command
from .md5_dir import add_subcommand as add_md5_command
from .debug import add_subcommand as add_debug_command
from .ast import add_subcommand as add_ast_command


logger = logging.getLogger("deba")


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        "deba", description="discover proper order of execution"
    )

    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase output verbosity"
    )

    subparsers = parser.add_subparsers()
    add_init_command(subparsers, common_parser)
    add_data_dir_command(subparsers, common_parser)
    add_deps_command(subparsers, common_parser)
    add_stages_command(subparsers, common_parser)
    add_targets_command(subparsers, common_parser)
    add_python_path_command(subparsers, common_parser)
    add_test_command(subparsers, common_parser)
    add_md5_command(subparsers, common_parser)
    add_debug_command(subparsers, common_parser)
    add_ast_command(subparsers, common_parser)
    return parser


def exec():
    parser = get_parser()
    args = parser.parse_args()

    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    ch.setLevel(logging.DEBUG)
    if args.verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARN)

    args.exec(None, args)


__all__ = ["get_parser"]
