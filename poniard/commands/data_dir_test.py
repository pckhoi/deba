import unittest
from unittest.mock import patch
import argparse

from poniard.commands.data_dir import add_subcommand
from poniard.config import Config, Stage


class DataDirCommandTestCase(unittest.TestCase):
    @patch("builtins.print")
    def test_run(self, mock_print):
        parser = argparse.ArgumentParser("poniard")
        subparsers = parser.add_subparsers()
        add_subcommand(subparsers)
        conf = Config(stages=[Stage(name="clean")])

        args = parser.parse_args(["dataDir"])
        args.exec(conf, args)

        mock_print.assert_called_with("data")
