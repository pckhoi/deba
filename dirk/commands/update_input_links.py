import argparse
import os
import pathlib
import shutil

from dirk.commands.decorators import subcommand
from dirk.config import Config


def exec(conf: Config, args: argparse.Namespace):
    if conf.inputs is None:
        return
    for dir_name, files in conf.inputs.items():
        link_dir = pathlib.Path(conf.input_links_dir) / dir_name
        os.makedirs(link_dir, 0o755, exist_ok=True)

        # add new links/update existing links
        names = set()
        for file in files:
            fp = link_dir / ("%s.link" % file._name)
            names.add(fp.name)
            link_match = False
            try:
                with open(fp, "r") as f:
                    if f.read().strip() == file.url:
                        link_match = True
            except FileNotFoundError:
                pass
            if not link_match:
                with open(fp, "w") as f:
                    f.write(file.url)

        # remove files that are no longer found in links_file
        for file in link_dir.iterdir():
            if not file.is_dir() and file.name not in names:
                os.remove(file)

    dirs = set(conf.inputs.keys())
    for subdir in pathlib.Path(conf.input_links_dir).iterdir():
        if subdir.is_dir() and subdir.name not in dirs:
            shutil.rmtree(subdir, ignore_errors=True)


@subcommand(exec=exec)
def add_subcommand(
    subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name="update-input-links")
    return parser
