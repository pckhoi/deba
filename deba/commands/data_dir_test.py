import unittest
from unittest.mock import patch
import argparse

from deba.commands.data_dir import add_subcommand
from deba.config import Config, Stage


class DataDirCommandTestCase(unittest.TestCase):
    @patch("builtins.print")
    def test_run(self, mock_print):
        parser = argparse.ArgumentParser("deba")
        subparsers = parser.add_subparsers()
        add_subcommand(subparsers)
        conf = Config(stages=[Stage(name="clean")])

        args = parser.parse_args(["dataDir"])
        args.exec(conf, args)

        mock_print.assert_called_with("data")

    @patch("builtins.print")
    def test_run_with_absolute_data_dir(self, mock_print):
        parser = argparse.ArgumentParser("deba")
        subparsers = parser.add_subparsers()
        add_subcommand(subparsers)
        conf = Config(stages=[Stage(name="clean")], data_dir="/runner/_work/data")
        self.assertEqual(conf.data_dir, "/runner/_work/data")

        args = parser.parse_args(["dataDir"])
        args.exec(conf, args)

        mock_print.assert_called_with("/runner/_work/data")
