import argparse
import typing

from dirk.config import Config

EXEC_FUNC = typing.Callable[[Config, argparse.Namespace], None]
ADD_COMMAND_FUNC = typing.Callable[
    [argparse._SubParsersAction], argparse.ArgumentParser
]


def subcommand(exec: EXEC_FUNC):
    def inner(func: ADD_COMMAND_FUNC):
        def inner_still(
            subparsers: argparse._SubParsersAction,
        ):
            parser = func(subparsers)
            parser.set_defaults(exec=exec)

        return inner_still

    return inner
