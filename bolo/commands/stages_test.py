import unittest
from unittest.mock import patch, call
import argparse

from bolo.commands.stages import add_subcommand
from bolo.config import Config, Stage


class StagesCommandTestCase(unittest.TestCase):
    @patch("builtins.print")
    def test_run(self, mock_print):
        parser = argparse.ArgumentParser("bolo")
        subparsers = parser.add_subparsers()
        add_subcommand(subparsers)
        conf = Config(stages=[Stage(name="clean"), Stage(name="fuse")])

        args = parser.parse_args(["stages"])
        args.exec(conf, args)

        mock_print.assert_has_calls([call("clean"), call("fuse")])
