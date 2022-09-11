import unittest
from unittest.mock import patch
import argparse

from deba.commands.md5_dir import add_subcommand
from deba.config import Config, Stage
from deba.test_utils import subcommand_testcase, CommandTestCaseMixin


@subcommand_testcase(add_subcommand)
class MD5DirCommandTestCase(CommandTestCaseMixin, unittest.TestCase):
    @patch("builtins.print")
    def test_run(self, mock_print):
        conf = Config(stages=[Stage(name="clean")])

        self.exec(conf, "md5Dir")

        mock_print.assert_called_with(".deba/md5")

    @patch("builtins.print")
    def test_run_with_absolute_data_dir(self, mock_print):
        conf = Config(stages=[Stage(name="clean")], md5_dir="/runner/_work/md5")
        self.assertEqual(conf.md5_dir, "/runner/_work/md5")

        self.exec(conf, "md5Dir")

        mock_print.assert_called_with("/runner/_work/md5")
