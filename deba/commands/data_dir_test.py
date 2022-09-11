import unittest
from unittest.mock import patch

from deba.commands.data_dir import add_subcommand
from deba.config import Config, Stage
from deba.test_utils import subcommand_testcase, CommandTestCaseMixin


@subcommand_testcase(add_subcommand)
class DataDirCommandTestCase(CommandTestCaseMixin, unittest.TestCase):
    @patch("builtins.print")
    def test_run(self, mock_print):
        self.exec(Config(stages=[Stage(name="clean")]), "dataDir")

        mock_print.assert_called_with("data")

    @patch("builtins.print")
    def test_run_with_absolute_data_dir(self, mock_print):
        conf = Config(stages=[Stage(name="clean")], data_dir="/runner/_work/data")
        self.assertEqual(conf.data_dir, "/runner/_work/data")
        self.exec(conf, "dataDir")

        mock_print.assert_called_with("/runner/_work/data")
