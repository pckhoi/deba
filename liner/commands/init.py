from shutil import copyfile
import pathlib

from liner.config import Config


def run(args):
    script_dir = pathlib.Path(__file__).parent
    copyfile(
        script_dir / 'Makefile',
        args.make_file
    )
    conf = Config()


def add_command(subparsers):
    parser = subparsers.add_parser('init')
    parser.add_argument('-x', type=int, default=1)
    parser.add_argument('y', type=float)
    parser.set_defaults(func=run)
