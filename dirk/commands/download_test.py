import unittest
import argparse

from dirk.commands.download import add_subcommand
from dirk.test_utils import StaticServerMixin


class DownloadCommandTestCase(StaticServerMixin, unittest.TestCase):
    def test_run(self):
        parser = argparse.ArgumentParser("dirk")
        subparsers = parser.add_subparsers()
        add_subcommand(subparsers)

        self.write_file(
            "abc.csv",
            [
                "a,b,c",
                "1,2,3",
            ],
        )

        args = parser.parse_args(
            ["download", self.base_url + "/abc.csv", self.file_path("def.csv")]
        )
        args.exec(None, args)

        self.assertFileContent(
            "def.csv",
            [
                "a,b,c",
                "1,2,3",
            ],
        )
