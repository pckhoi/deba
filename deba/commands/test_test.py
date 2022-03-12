import unittest
from unittest.mock import patch, call
import argparse

from deba.commands.test import add_subcommand


class TestCommandTestCase(unittest.TestCase):
    @patch("builtins.print")
    def test_run(self, mock_print):
        parser = argparse.ArgumentParser("deba")
        subparsers = parser.add_subparsers()
        add_subcommand(subparsers)

        args = parser.parse_args(
            ["test", r"`*_df`.to_csv(r'.+\.csv')", r"my_df.to_csv('my_data.csv')"]
        )
        args.exec(
            None,
            args,
        )
        mock_print.assert_has_calls([call('Extracted "my_data.csv"')])

        args = parser.parse_args(
            ["test", r"`*_df`.to_csv(r'.+\.csv')", r"my_df.t_csv('my_data.csv')"]
        )
        with self.assertRaises(SystemExit) as cm:
            args.exec(
                None,
                args,
            )
        mock_print.assert_has_calls([call("Does not match")])
        self.assertEqual(
            cm.exception.args,
            (1,),
        )
