import argparse

from dirk.commands import (
    init,
    data_dir,
    deps,
    download,
    md5,
    stages,
    targets,
    update_input_links,
)

parser = argparse.ArgumentParser("dirk", help="discover proper order of execution")
subparsers = parser.add_subparsers()
init.add_subcommand(subparsers)
data_dir.add_subcommand(subparsers)
deps.add_subcommand(subparsers)
download.add_subcommand(subparsers)
md5.add_subcommand(subparsers)
stages.add_subcommand(subparsers)
targets.add_subcommand(subparsers)
update_input_links.add_subcommand(subparsers)

args = parser.parse_args()
args.exec(None, args)
