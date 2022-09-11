import unittest
from unittest.mock import patch, call
import argparse

from deba.commands.stages import add_subcommand
from deba.config import Config, Stage
from deba.test_utils import subcommand_testcase, CommandTestCaseMixin


@subcommand_testcase(add_subcommand)
class StagesCommandTestCase(CommandTestCaseMixin, unittest.TestCase):
    @patch("builtins.print")
    def test_run(self, mock_print):
        conf = Config(stages=[Stage(name="clean"), Stage(name="fuse")])

        self.exec(conf, "stages")

        mock_print.assert_has_calls([call("clean"), call("fuse")])
