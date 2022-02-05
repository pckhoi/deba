import argparse

import requests
from dirk.commands.decorators import subcommand
from dirk.config import Config


def exec(conf: Config, args: argparse.Namespace):
    with requests.get(args.link, stream=True) as r:
        r.raise_for_status()
        with open(args.filename, "wb") as f:
            for chunk in r.iter_content():
                f.write(chunk)


@subcommand(exec=exec, open_config=False)
def add_subcommand(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(
        name="download", description="download a link to specified location"
    )
    parser.add_argument("link", type=str, help="link to download")
    parser.add_argument("filename", type=str, help="target file location")
    return parser
