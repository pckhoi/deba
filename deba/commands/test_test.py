import unittest
from unittest.mock import patch, call
import argparse

from deba.commands.test import add_subcommand
from deba.test_utils import subcommand_testcase, CommandTestCaseMixin


@subcommand_testcase(add_subcommand)
class TestCommandTestCase(CommandTestCaseMixin, unittest.TestCase):
    @patch("builtins.print")
    def test_run(self, mock_print):
        self.exec(
            None,
            "test",
            r"`*_df`.to_csv(r'.+\.csv')",
            r"my_df.to_csv('my_data.csv')",
        )
        mock_print.assert_has_calls([call('Extracted "my_data.csv"')])

        with self.assertRaises(SystemExit) as cm:
            self.exec(
                None,
                "test",
                r"`*_df`.to_csv(r'.+\.csv')",
                r"my_df.t_csv('my_data.csv')",
            )
        mock_print.assert_has_calls([call("Does not match")])
        self.assertEqual(
            cm.exception.args,
            (1,),
        )
