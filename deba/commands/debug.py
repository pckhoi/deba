import argparse
import logging

from deba.commands.decorators import subcommand
from deba.config import Config

from deba.deps.module import Loader
from deba.deps.find import find_dependencies


logger = logging.getLogger("deba")


def exec(conf: Config, args: argparse.Namespace):
    loader = Loader(conf.script_search_paths)
    logger.setLevel(logging.DEBUG)
    prerequisites, references, targets = find_dependencies(
        loader,
        args.script,
        conf.patterns.prerequisites or [],
        conf.patterns.references or [],
        conf.patterns.targets or [],
        debug=True,
    )
    logger.debug(
        "%s:\n\t%s",
        args.script,
        "\n\t".join(
            [
                "%s:\n\t\t%s" % (title, "\n\t\t".join(filepaths))
                for title, filepaths in [
                    ("prerequisites", prerequisites),
                    ("references", references),
                    ("targets", targets),
                ]
                if len(filepaths) > 0
            ]
        ),
    )


@subcommand(exec=exec)
def add_subcommand(
    subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        name="debug",
        parents=[parent_parser],
        description="print prerequisites and targets from a single script",
    )
    parser.add_argument(
        "script",
        metavar="SCRIPT",
        type=str,
        help="the script to scan",
    )
    return parser
