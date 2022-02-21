import argparse
import typing

from deba.config import Config, get_config

EXEC_FUNC = typing.Callable[[Config, argparse.Namespace], None]
ADD_COMMAND_FUNC = typing.Callable[
    [argparse._SubParsersAction], argparse.ArgumentParser
]


def subcommand(exec: EXEC_FUNC, open_config=True):
    def inner(func: ADD_COMMAND_FUNC):
        def inner_still(
            subparsers: argparse._SubParsersAction,
        ):
            parser = func(subparsers)

            def _exec(conf: Config, args: argparse.Namespace):
                if open_config and conf is None:
                    conf = get_config()
                exec(conf, args)

            parser.set_defaults(exec=_exec)

        return inner_still

    return inner
