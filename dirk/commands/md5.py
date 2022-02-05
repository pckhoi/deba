import argparse
import hashlib
import pathlib

from dirk.commands.decorators import subcommand
from dirk.config import Config


def exec(conf: Config, args: argparse.Namespace):
    old = ""
    try:
        with open(args.destination, "r") as dst:
            old = dst.read()
    except FileNotFoundError:
        pass
    m = hashlib.sha256()
    with open(args.source, "rb") as src:
        while True:
            piece = src.read(4096)
            if not piece:
                break
            m.update(piece)
    hd = m.hexdigest()
    if hd != old:
        with open(args.destination, "w") as dst:
            dst.write(hd)


@subcommand(exec=exec, open_config=False)
def add_subcommand(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        name="md5", description="write md5 hash of specified file"
    )
    parser.add_argument("source", type=pathlib.Path, help="file to hash")
    parser.add_argument("destination", type=pathlib.Path, help="write md5 to this file")
    return parser
