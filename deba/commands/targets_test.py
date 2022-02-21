import unittest
from unittest.mock import patch, call
import argparse

from deba.commands.targets import add_subcommand
from deba.config import Config, Stage


class TargetsCommandTestCase(unittest.TestCase):
    @patch("builtins.print")
    def test_run(self, mock_print):
        parser = argparse.ArgumentParser("deba")
        subparsers = parser.add_subparsers()
        add_subcommand(subparsers)
        args = parser.parse_args(["targets"])

        args.exec(
            Config(
                stages=[Stage(name="clean"), Stage(name="fuse")],
            ),
            args,
        )
        mock_print.assert_not_called()

        args.exec(
            Config(
                stages=[Stage(name="clean"), Stage(name="fuse")],
                targets=["fuse/personnel.csv", "fuse/complaint.csv"],
            ),
            args,
        )
        mock_print.assert_has_calls(
            [call("data/fuse/personnel.csv"), call("data/fuse/complaint.csv")]
        )
