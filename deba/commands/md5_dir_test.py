import unittest
from unittest.mock import patch
import argparse

from deba.commands.md5_dir import add_subcommand
from deba.config import Config, Stage


class MD5DirCommandTestCase(unittest.TestCase):
    @patch("builtins.print")
    def test_run(self, mock_print):
        parser = argparse.ArgumentParser("deba")
        subparsers = parser.add_subparsers()
        add_subcommand(subparsers)
        conf = Config(stages=[Stage(name="clean")])

        args = parser.parse_args(["md5Dir"])
        args.exec(conf, args)

        mock_print.assert_called_with(".deba/md5")

    @patch("builtins.print")
    def test_run_with_absolute_data_dir(self, mock_print):
        parser = argparse.ArgumentParser("deba")
        subparsers = parser.add_subparsers()
        add_subcommand(subparsers)
        conf = Config(stages=[Stage(name="clean")], md5_dir="/runner/_work/md5")
        self.assertEqual(conf.md5_dir, "/runner/_work/md5")

        args = parser.parse_args(["md5Dir"])
        args.exec(conf, args)

        mock_print.assert_called_with("/runner/_work/md5")
