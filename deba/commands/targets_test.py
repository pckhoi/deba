import unittest
from unittest.mock import patch, call
import argparse

from deba.commands.targets import add_subcommand
from deba.config import Config, Stage
from deba.test_utils import subcommand_testcase, CommandTestCaseMixin


@subcommand_testcase(add_subcommand)
class TargetsCommandTestCase(CommandTestCaseMixin, unittest.TestCase):
    @patch("builtins.print")
    def test_run(self, mock_print):
        self.exec(
            Config(
                stages=[Stage(name="clean"), Stage(name="fuse")],
            ),
            "targets",
        )
        mock_print.assert_not_called()

        self.exec(
            Config(
                stages=[Stage(name="clean"), Stage(name="fuse")],
                targets=["fuse/personnel.csv", "fuse/complaint.csv"],
            ),
            "targets",
        )
        mock_print.assert_has_calls(
            [call("data/fuse/personnel.csv"), call("data/fuse/complaint.csv")]
        )
