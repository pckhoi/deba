import unittest
import argparse

from bolo.commands.md5 import add_subcommand
from bolo.config import Config, Stage
from bolo.test_utils import TempDirMixin


class MD5CommandTestCase(TempDirMixin, unittest.TestCase):
    def test_run(self):
        parser = argparse.ArgumentParser("bolo")
        subparsers = parser.add_subparsers()
        add_subcommand(subparsers)

        self.write_file(
            "clean/a.py",
            [
                'if __name__ == "__main__":',
                '  df = read_csv("raw/a_input.csv")',
                '  df.to_csv("clean/a_output.csv")',
            ],
        )

        args = parser.parse_args(
            ["md5", self.file_path("clean/a.py"), self.file_path("clean/a.py.md5")]
        )
        args.exec(None, args)

        mod1 = self.assertFileContent(
            "clean/a.py.md5",
            ["7c9bbdd4f16e4479144a112545ca4de20ce466d9e9c80be34418a10d19df0050"],
        )

        args.exec(None, args)

        mod2 = self.assertFileContent(
            "clean/a.py.md5",
            ["7c9bbdd4f16e4479144a112545ca4de20ce466d9e9c80be34418a10d19df0050"],
        )

        # doesn't modify file if hash hasn't changed
        self.assertEqual(mod1, mod2)

        self.write_file(
            "clean/a.py",
            [
                'if __name__ == "__main__":',
                '  df = read_csv("raw/my_a_input.csv")',
                '  df.to_csv("clean/my_a_output.csv")',
            ],
        )

        args.exec(None, args)

        self.assertFileContent(
            "clean/a.py.md5",
            ["c47c9c118d13df6ee863abce1d85786031c72434d0e4d776c869a871a5d128d5"],
        )
