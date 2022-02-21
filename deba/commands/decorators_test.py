import argparse
import unittest
import unittest.mock

from deba.commands.decorators import subcommand
from deba.config import Config, Stage


def spy():
    def inner(func):
        return unittest.mock.Mock(wraps=func)

    return inner


class WithConfigTestCase(unittest.TestCase):
    def test_decorator(self):
        my_conf = Config(stages=[Stage(name="clean")], targets=["clean/my_data.csv"])

        @spy()
        def exec(conf: Config, args: argparse.Namespace):
            self.assertEqual(conf, my_conf)
            self.assertEqual(args.my_arg, 3)
            self.assertEqual(args.my_sub_flag, "abc")

        @subcommand(exec=exec)
        def add_my_subcommand(
            subparsers: argparse._SubParsersAction,
        ) -> argparse.ArgumentParser:
            parser = subparsers.add_parser(name="my-sub-command")
            parser.add_argument("--my-sub-flag", type=str, default="def")
            return parser

        parser = argparse.ArgumentParser("my-program")
        parser.set_defaults(my_arg=3)
        subparsers = parser.add_subparsers()
        add_my_subcommand(subparsers)

        args = parser.parse_args(["my-sub-command", "--my-sub-flag", "abc"])
        args.exec(my_conf, args)
        exec.assert_called_once_with(my_conf, args)
